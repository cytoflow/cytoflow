package org.flowcyt.facejava.transformation.xmlio;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.HashSet;
import java.util.Set;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBElement;
import javax.xml.bind.JAXBException;
import javax.xml.bind.UnmarshalException;
import javax.xml.bind.ValidationEvent;

import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.transformation.Transformation;
import org.flowcyt.facejava.transformation.TransformationCollection;
import org.flowcyt.facejava.transformation.exception.InvalidTransformationException;
import org.flowcyt.facejava.transformation.exception.InvalidTransformationMLFileException;
import org.flowcyt.facejava.transformation.jaxb.ParameterTransformation;
import org.flowcyt.facejava.transformation.jaxb.TransformationML;
import org.flowcyt.facejava.utils.schemas.JAXBReader;
import org.xml.sax.SAXException;

/**
 * <p>
 * Used to read TransformationML files. Each reader is specific to a single transformation file. 
 * 
 * @author echng
 */
public class TransformationMLFileReader {
	/**
	 * The location of the TransformationML schema to be used for validation.
	 */
	private static final String TRANSFORMATION_SCHEMA_LOCATION = "schemas/Transformation-ML.v1.0/schema/Transformation-ML.v1.0.xsd";
	
	/**
	 * The package name to pass to JAXBContext.newInstance. That is, the package name
	 * specified when JAXB auto-generated the source files.
	 */
	private static final String JAXB_CONTEXT_PACKAGE_NAME = "org.flowcyt.facejava.transformation.jaxb";
		
	/**
	 * The JAXBReader to use to unmarshal files. It is shared among all instances, so we save
	 * the cost of recreating the JAXBContext for each file.
	 */
	private static JAXBReader reader;
	
	/**
	 * A URL to the TransformationML File that this reader will read.
	 */
	private URL xmlFile;
	
	/**
	 * An array containing the ValidationEvents of the last call to read().
	 */
	private ValidationEvent[] events;
	
	/**
	 * Initializes the static JAXBReader. If it has already been initialized nothing is done. 
	 * 
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	private static void initReader() throws SAXException, JAXBException {
		if (reader == null) {
			reader = new JAXBReader(TRANSFORMATION_SCHEMA_LOCATION, JAXB_CONTEXT_PACKAGE_NAME);
		}
	}
	
	/**
	 * @return Returns the JAXBContext for Transformation files.
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public static JAXBContext getJAXBContext() throws SAXException, JAXBException {
		initReader();
		return reader.getJAXBContext();
	}
	
	/**
	 * Constructor. Creates a TransformationMLFileReader that will read from the file pointed to
	 * by the uri. See TransformationMLFileReader(URI) for more info about supported URIs.
	 * 
	 * @param uri A URI string of the file to be loaded.  
	 * @throws URISyntaxException Thrown if the given string is not a valid URI.
	 * @throws MalformedURLException Thrown if the URI cannot be converted to a URL.
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public TransformationMLFileReader(String uri) throws URISyntaxException, MalformedURLException, SAXException, JAXBException {
		this(new URI(uri));
	}
	
	/**
	 * Constructor. Creates a TransformationMLFileReader that will read from the given File.
	 * This constructor can be used for reading local files.
	 * @param file The File to be loaded.
	 * @throws MalformedURLException Should never be thrown as URLs are created by File.toURL().
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public TransformationMLFileReader(File file) throws MalformedURLException, SAXException, JAXBException {
		this(file.toURI());
	}
	
	/**
	 * <p>
	 * Constructor. Creates a TransformationMLFileReader that will read from the given URI.
	 * 
	 * <p>
	 * <b>Notes:</b>
	 * <ul>
	 * <li>non-absolute URIs (ones with no scheme/protocol) cannot be loaded. This is because
	 *     the given URI is converted to a URL (which must have protocols) before loading
	 *     since the file must exist and must be able to be loaded.
	 * <li>a java.net.URL is used thus only protocols supported by Java URLs can be loaded
	 * </ul>
	 *        
	 * @param uri The URI to load.
	 * @throws MalformedURLException Thrown if the URI could not be converted to a URL.
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public TransformationMLFileReader(URI uri) throws MalformedURLException, SAXException, JAXBException {
		try {
			xmlFile = uri.toURL();
		} catch (IllegalArgumentException e) {
			// URI throws this when the uri is not ansolute.
			throw new MalformedURLException(e.getMessage());
		}
		initReader();
	}
	
	/**
	 * <p>
 	* Constructor. Creates a TransformationMLFileReader that will read from the given URL.
	 * 
	 * <p>
	 * Note that a java.net.URL is used thus only protocols supported by Java URLs can be loaded.
	 * 
	 * @param url The URL to load.
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public TransformationMLFileReader(URL url) throws SAXException, JAXBException {
		xmlFile = url;
		initReader();
	}
	
	/**
	 * Reads in the file specified at construction and returns a TransformationCollection
	 * containing all the transformations in the that file.
	 * 
	 * @return returns a TransformationCollection containing all the transformations in the
	 * file specified at construction.
	 * @throws JAXBException Thrown if JAXB could not unmarshal the file.
	 * @throws InvalidTransformationMLFileException Thrown if the file does not validate against
	 * the schema.
	 * @throws InvalidTransformationException Thrown if any transformation is invalid by the
	 * specification (i.e., problems that aren't because it didn't validate against the schema).
	 * @throws DuplicateParameterReferenceException Thrown if any transformations in the file have
	 * duplicate names.
	 * @throws IOException Thrown if the file could not be read.
	 */
	public TransformationCollection read() throws JAXBException, InvalidTransformationMLFileException, InvalidTransformationException, DuplicateParameterReferenceException, IOException {
		try {
			JAXBElement<?> rootElement = reader.read(xmlFile);
			events = reader.getValidationEvents();
			
			if (events != null && events.length > 0) {
				throw new InvalidTransformationMLFileException("Does not validate against schema: " + events[0]);
			}
			
			TransformationML transforms = (TransformationML) rootElement.getValue();
			TransformationCollection rv = new TransformationCollection();
			Set<ParameterReference> references = new HashSet<ParameterReference>();
			
			for (ParameterTransformation jaxbTrans : transforms.getTransformation()) {
				Transformation trans = TransformationFactory.createTransformation(jaxbTrans);
				if (!references.add(trans.getReference()))
					throw new DuplicateParameterReferenceException(trans.getReference());
				
				rv.add(trans);
			}
			
			return rv;
		} catch (UnmarshalException ex) {
			throw new InvalidTransformationMLFileException("Does not validate against schema: " + ex.getLinkedException().getMessage());
		}
	}
	
	/**
	 * @return Returns any ValidationEvents that occured during the last call to read() and null
	 * if read() has not been called yet.
	 */
	public ValidationEvent[] getValidationEvents() {
		return events;
	}
}
