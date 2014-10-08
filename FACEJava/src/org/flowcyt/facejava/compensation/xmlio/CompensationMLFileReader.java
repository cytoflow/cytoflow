package org.flowcyt.facejava.compensation.xmlio;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBElement;
import javax.xml.bind.JAXBException;
import javax.xml.bind.UnmarshalException;
import javax.xml.bind.ValidationEvent;

import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.compensation.exception.InvalidCompensationMLFileException;
import org.flowcyt.facejava.compensation.jaxb.CompensationML;
import org.flowcyt.facejava.compensation.jaxb.SpilloverMatrix;
import org.flowcyt.facejava.utils.schemas.JAXBReader;
import org.xml.sax.SAXException;

/**
 * <p>
 * Reads in a CompensationML file. Each reader is specific to a single file.
 * 
 * @author echng
 */
public class CompensationMLFileReader {
	/**
	 * The location of the compensation schema in the classpath.
	 */
	private static final String COMPENSATION_SCHEMA_LOCATION = "schemas/Compensation-ML.v1.0/schema/Compensation-ML.v1.0.xsd";
	
	/**
	 * The package name of the JAXB classes.
	 */
	private static final String JAXB_CONTEXT_PACKAGE_NAME = "org.flowcyt.facejava.compensation.jaxb";
	
	/**
	 * The JAXBReader to use to unmarshal files. It is shared among all instances, so we save
	 * the cost of recreating the JAXBContext for each file.
	 */
	private static JAXBReader reader;
	
	/**
	 * The URL to the file to read.
	 */
	private URL xmlFile;
	
	/**
	 * An array containing the ValidationEvents raised during the last call to read().
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
		if (reader == null)
			reader = new JAXBReader(COMPENSATION_SCHEMA_LOCATION, JAXB_CONTEXT_PACKAGE_NAME);
	}
	
	/**
	 * @return Returns the JAXBContext for Compensation files.
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
	 * Constructor. Creates a CompensationMLFileReader that will read from the file pointed to
	 * by the uri. See CompensationMLFileReader(URI) for more info about supported URIs.
	 * 
	 * @param uri A URI string of the file to be loaded.  
	 * @throws URISyntaxException Thrown if the given string is not a valid URI.
	 * @throws MalformedURLException Thrown if the URI cannot be converted to a URL.
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public CompensationMLFileReader(String uri) throws MalformedURLException, SAXException, JAXBException, URISyntaxException {
		this(new URI(uri));
	}
	
	/**
	 * Constructor. Creates a CompensationMLFileReader that will read from the given File.
	 * This constructor can be used for reading local files.
	 * 
	 * @param file The File to be loaded.
	 * @throws MalformedURLException Should never be thrown as URLs are created by File.toURL().
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public CompensationMLFileReader(File file) throws MalformedURLException, SAXException, JAXBException {
		this(file.toURI());
	}
	
	/**
	 * <p>
	 * Constructor. Creates a CompensationMLFileReader that will read from the given URI.
	 * 
	 * <p>
	 * Notes:
	 * <ul>
	 * <li>non-absolute URIs (ones with no scheme/protocol) cannot be loaded. This is because
	 *          the given URI is converted to a URL (which must have protocols) before loading
	 *          since the file must exist and must be able to be loaded.
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
	public CompensationMLFileReader(URI uri) throws MalformedURLException, SAXException, JAXBException {
		try {
			xmlFile = uri.toURL();
		} catch (IllegalArgumentException e) {
			// URI throws this when the uri is not ansolute.
			throw new MalformedURLException(e.getMessage());
		}
		initReader();
	}
	
	/**
	 * Constructor. Creates a CompensationMLFileReader that will read from the given URL.
	 * 
	 * Note that a java.net.URL is used thus only protocols supported by Java URLs can be loaded.
	 * 
	 * @param url The URL to load.
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public CompensationMLFileReader(URL url) throws SAXException, JAXBException {
		xmlFile = url;
		initReader();
	}
	
	/**
	 * Reads in the file specified at construction and returns a SpilloverMatrixSet
	 * containing all the SpilloverMatrices in the file.
	 * 
	 * @return Returns a SpilloverMatrixSet which contains all the SpilloverMatrices
	 * defined in the file.
	 * @throws JAXBException Thrown if JAXB could not unmarshal the file.
	 * @throws IOException Thrown if the file could not be read.
	 * @throws InvalidCompensationMLFileException Thrown if the file could not be validated
	 * against the schema.
	 */
	public SpilloverMatrixSet read() throws JAXBException, IOException, InvalidCompensationMLFileException {
		try {
			JAXBElement<?> rootElement = reader.read(xmlFile);
			events = reader.getValidationEvents();
			
			if (events != null && events.length > 0) {
				throw new InvalidCompensationMLFileException("Does not validate against schema: " + events[0]);
			}
			
			CompensationML comp = (CompensationML) rootElement.getValue();
			
			SpilloverMatrixSet rv = new SpilloverMatrixSet();
			for (SpilloverMatrix jaxbMatrix : comp.getSpilloverMatrix()) {
				rv.add(SpilloverMatrixFactory.createMatrix(jaxbMatrix));
			}
			
			return rv;
		} catch (UnmarshalException e) {
			throw new InvalidCompensationMLFileException("Does not validate against schema: " + e.getLinkedException().getMessage());
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
