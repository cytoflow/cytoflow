package org.flowcyt.facejava.utils.schemas;

import java.io.IOException;
import java.net.URL;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBElement;
import javax.xml.bind.JAXBException;
import javax.xml.bind.UnmarshalException;
import javax.xml.bind.Unmarshaller;
import javax.xml.bind.ValidationEvent;
import javax.xml.bind.util.ValidationEventCollector;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;

import org.xml.sax.SAXException;

/**
 * <p>
 * A helper class to read XML files that have JAXB-generated classes. Each instance of this class
 * is specific to a Schema (which will be used for validation) and a JAXB package (one that
 * contains the JAXB auto-generated classes).
 * 
 * @author echng
 */
public class JAXBReader {
	/* XXX: There's still a lot of boilerplate code needed to hook up the JAXBReader with the
	 * reader associated with a specific XML file type that we support (see
	 * CompensationMLFileReader and TransformationMLFileReader and how they're pretty much the
	 * same.) There's got to be more refactoring possible that will lessen the code duplication.
	 * 
	 * The refactoring must be able to:
	 *    - Allow caching the JAXBContext for each different type of XML. It can be re-used and
	 *      we'll save the cost of recreation for each read.
	 *    - Cope with the different return types of read() -- TransformationCollection, 
	 *      SpilloverMatrixCollection, etc.
	 *    - Cope with the different exceptions thrown. Each different XML type has their own
	 *      exceptions that are thrown for their various errors.
	 * 
	 * If possible, inheritance should probably be avoided (i.e., that is each of the different
	 * readers inherit from a supertype) since readers are *not* interchangeable. A reader of
	 * one type only knows how to read it's own type and wil fail miserably on any other types.
	 */
	
	
	/**
	 * The Schema object used to validate files. 
	 */
	private Schema schema;
	
	/**
	 * The JAXBContext for the JAXB generated classes.
	 */
	private JAXBContext jc;
	
	/**
	 * Used to collect any events that happen during validation when unmarshalling
	 */
	private ValidationEventCollector eventCollector;
	
	/**
	 * Constructor. Creates a JAXBReader that will validate with the given Schema and create
	 * a content tree using the given JAXB package.
	 * 
	 * @param schemaPath The path to the Schema to use to validate unmarshalled files. The path
	 * will be loaded using the ClassLoader returned by getClass().getClassLoader(). So the schema
	 * path must be in the classpath.
	 * @param jaxbPackageName The package name of the package containing the JAXB generated
	 * classes. (i.e., It will be used as the argument to JAXBContext.newInstance(String)).
	 * @throws JAXBException Thrown if the JAXBContext could not be created
	 * @throws SAXException Thrown if the schema located at the given path could not be read. 
	 */
	public JAXBReader(String schemaPath, String jaxbPackageName) throws SAXException, JAXBException {
		URL url = getClass().getClassLoader().getResource(schemaPath);
		SchemaFactory sf = SchemaFactory.newInstance(javax.xml.XMLConstants.W3C_XML_SCHEMA_NS_URI);
		schema = sf.newSchema(url);
		
		jc = JAXBContext.newInstance(jaxbPackageName);		
		
		eventCollector = new ValidationEventCollector();
	}
	
	/**
	 * @return Returns the JAXBContext for the given JAXB package name. 
	 */
	public JAXBContext getJAXBContext() {
		return jc;
	}
	
	/**
	 * Reads a file and returns the content tree created by JAXB. The returned JAXBElement is
	 * the root element and its getValue() can be cast into the type of the root element specific
	 * to whichever JAXB package was specified at construction. * 
	 * 
	 * @param url The URL of the file to load.
	 * @return The root element of the unmarshalled file.
	 * @throws JAXBException Thrown if JAXB could not unmarshal the file.
	 * @throws IOException Thrown if there was a problem reading the file.
	 */
	public JAXBElement<?> read(URL url) throws JAXBException, IOException {
		Unmarshaller unmarshaller = jc.createUnmarshaller();
		unmarshaller.setSchema(schema);
		
		eventCollector.reset();
		unmarshaller.setEventHandler(eventCollector);
		try {
			JAXBElement<?> rv = (JAXBElement<?>) unmarshaller.unmarshal(url);
			return rv;
		} catch (UnmarshalException e) {
			// Differentiate between IO errors and problems with the file.
			if (e.getLinkedException() instanceof IOException)
				throw (IOException) e.getLinkedException();
			throw e;
		}
	}
	
	/**
	 * @return Returns the ValidationEvents that were raised during the last call to read(). 
	 */
	public ValidationEvent[] getValidationEvents() {
		return eventCollector.getEvents();
	}
}
