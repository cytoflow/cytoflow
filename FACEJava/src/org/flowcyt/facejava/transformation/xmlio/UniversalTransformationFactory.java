package org.flowcyt.facejava.transformation.xmlio;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.io.Serializable;
import java.util.HashSet;
import java.util.Set;
import java.util.Stack;

import javax.xml.bind.JAXBElement;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Marshaller;
import javax.xml.namespace.QName;

import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.transformation.UniversalTransformation;
import org.flowcyt.facejava.transformation.exception.InvalidTransformationException;
import org.flowcyt.facejava.transformation.jaxb.BvarType;
import org.flowcyt.facejava.transformation.jaxb.CiType;
import org.flowcyt.facejava.transformation.jaxb.MathType;
import org.xml.sax.SAXException;

import com.albin.archimedes.BoundVariable;
import com.albin.archimedes.MathObject;
import com.albin.archimedes.SymbolTable;
import com.albin.archimedes.dao.MathObjectDAOException;
import com.albin.archimedes.dao.UnsupportedElementException;
import com.albin.archimedes.mathmldao.CastorXMLMathMLDAO;

/**
 * <p>
 * Used to create Universal Transformations with MathJ objects. By putting all the MathJ
 * specific stuff here, we can load Transformation-ML files that do not contain universal
 * transformations when Archimedes MathJ is not found on the classpath.
 * 
 * @author echng
 *
 */
class UniversalTransformationFactory {
	
	private static final String TEMP_FILE_NAME_PREFIX = "facegate.uni-trans.";
	
	private static final String TEMP_FILE_NAME_SUFFIX = ".tmp.xml";
	
	private static final String MATH_ML_NAMESPACE = "http://www.w3.org/1998/Math/MathML";
	
	private static final String MATH_ML_ROOT_ELEMENT_NAME = "math";
	
	/**
	 * To use the MathJ library, we need to feed it the path to an xml file containing
	 * only the MathML. Thus, for each universal transformation we marhsal (using JAXB) 
	 * the mathml math element and all its contents to a temporary file, whose path we
	 * then pass to thelibrary.
	 * 
	 * @param name The name of the transformation
	 * @param math The JAXB MathType representing the root MathML node. 
	 * @return Returns the new Transformation
	 * @throws InvalidTransformationException Thrown if the Transformation couldn't be created.
	 */
	public static UniversalTransformation createUniversal(String name,
			MathType math) throws InvalidTransformationException {
		try {
			// Create a temporary file in a system-dependent way.
			File tempFile = File.createTempFile(TEMP_FILE_NAME_PREFIX, TEMP_FILE_NAME_SUFFIX);
			tempFile.deleteOnExit();

			Marshaller m = TransformationMLFileReader.getJAXBContext().createMarshaller();
			OutputStream out = new FileOutputStream(tempFile);
			ParameterNameListener nameListener = new ParameterNameListener();
			m.setListener(nameListener);

			// We need to wrap MathType in an element (since it's just a complex
			// type) for
			// JAXB to be able to marshal it.
			JAXBElement<MathType> mathElem = new JAXBElement<MathType>(
					new QName(MATH_ML_NAMESPACE, MATH_ML_ROOT_ELEMENT_NAME),
					MathType.class, math);

			m.marshal(mathElem, new PrintWriter(out));

			MathObject transObj = createMathObject(tempFile, nameListener
					.getParameterNames(), name);

			Set<ParameterReference> refSet = new HashSet<ParameterReference>();
			for (String stringRef : nameListener.getParameterNames()) {
				refSet.add(new ParameterReference(stringRef));
			}

			return new UniversalTransformation(name, refSet, transObj);
		} catch (IOException e) {
			throw new InvalidTransformationException(name,
					"Could not write temp file for universal transformation.");
		} catch (JAXBException e) {
			throw new InvalidTransformationException(name,
					"Could not write temp file for universal transformation.");
		} catch (SAXException e) {
			throw new InvalidTransformationException(name,
					"Could not write temp file for universal transformation.");
		}
	}

	/**
	 * Creates a MathJ MathObject to use for the transformation.
	 * 
	 * @param transformationFile
	 *            The temporary file containing the marshalled math element.
	 * @param parameters
	 *            A set containing the parameter references that are being
	 *            transformed.
	 * @param name
	 *            The name of the transformation.
	 * @return Returns the MathObject that will caryy out the transformation.
	 * @throws InvalidTransformationException
	 *             Thrown if the MathObject couldn't be created by MathJ.
	 */
	private static MathObject createMathObject(File transformationFile,
			Set<String> parameters, String name)
			throws InvalidTransformationException {
		CastorXMLMathMLDAO dao = new CastorXMLMathMLDAO();

		SymbolTable symbolTable = new SymbolTable();

		for (String param : parameters) {
			BoundVariable bvar = new BoundVariable(param);
			bvar.setBoundValue(1.0D);
			symbolTable.putIdentifier(bvar);
		}

		try {
			return dao.getMathObject(transformationFile.getCanonicalPath(),
					symbolTable);
		} catch (MathObjectDAOException e) {
			throw new InvalidTransformationException(name, e.getMessage());
		} catch (UnsupportedElementException e) {
			throw new InvalidTransformationException(name, e.getMessage());
		} catch (IOException e) {
			throw new InvalidTransformationException(name, e.getMessage());
		}
	}

	/**
	 * This Listener will look for ParameterNames in ci elements as the math
	 * element gets marshalled.
	 * 
	 * The MathJ library must also know beforehand, which ci elements are not
	 * bound variables. We must also know so we can do dependency checks on the
	 * parameters. So the listener, will grab all the ci elements that are
	 * descendants of the given math element and remove any that are not the
	 * *immediate* child of a bvar element. For example, in <bvar> <ci>x</ci>
	 * <degree><ci>n</ci></degree> </bvar> x is a bound variable while n is
	 * not.
	 * 
	 * @author echng
	 */
	private static class ParameterNameListener extends Marshaller.Listener {
		/**
		 * A stack containing the bvar elements that are the ancestors of the
		 * current element being processed. This is so we can handle nested
		 * bvars.
		 */
		private Stack<BvarType> bvarStack = new Stack<BvarType>();

		/**
		 * A set containing the parameter names in ci elements that were found.
		 */
		private Set<String> parameterNames = new HashSet<String>();

		public void afterMarshal(Object source) {
			// Finished processing the bvar reset to null.
			if (!bvarStack.empty() && source == bvarStack.peek()) {
				bvarStack.pop();
			}
		}

		public void beforeMarshal(Object source) {
			if (source instanceof BvarType) {
				bvarStack.push((BvarType) source);
			} else if (source instanceof CiType) {
				CiType ci = (CiType) source;
				if (bvarStack.empty()
						|| !bvarStack.peek().getBvarContent().contains(ci)) {
					for (Serializable ser : ci.getContent()) {
						if (ser instanceof String) {
							parameterNames.add(((String) ser).trim());
							break;
						}
					}
				}
			}
		}

		public Set<String> getParameterNames() {
			return parameterNames;
		}
	}
}
