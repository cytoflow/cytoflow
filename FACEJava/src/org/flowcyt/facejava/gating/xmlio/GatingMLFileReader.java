package org.flowcyt.facejava.gating.xmlio;

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

import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.jaxb.AbstractGate;
import org.flowcyt.facejava.gating.jaxb.GatingML;
import org.flowcyt.facejava.utils.schemas.JAXBReader;
import org.xml.sax.SAXException;

/**
 * <p>
 * Responsible for reading gating XML files. It will validate the XML file against the
 * gating schema and report any errors. Each reader is specific to a gating file.
 * 
 * @author echng
 */
public class GatingMLFileReader {
	/**
	 * The location of the gating schema in the classpath to be used for validation.
	 */
	private static final String GATING_SCHEMA_LOATION = "schemas/Gating-ML.v1.1/schema/Gating-ML.v1.1.xsd";
	
	/**
	 * The package name to pass to JAXBContext.newInstance. That is, the package name
	 * specified when JAXB auto-generated the source files.
	 */
	private static final String JAXB_CONTEXT_PACKAGE_NAME = "org.flowcyt.facejava.gating.jaxb";
	
	/**
	 * The JAXBReader to use to unmarshal files. It is shared among all instances, so we save
	 * the cost of recreating the JAXBContext for each file.
	 */
	private static JAXBReader reader;
	
	/**
	 * The URL to the Gating ML File that this reader will read.
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
		if (reader == null)
			reader = new JAXBReader(GATING_SCHEMA_LOATION, JAXB_CONTEXT_PACKAGE_NAME);
	}
	
	/**
	 * @return Returns the JAXBContext for Gating files.
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public static JAXBContext getJAXBContext() throws JAXBException, SAXException {
		initReader();
		return reader.getJAXBContext();
	}
	
	/**
	 * Constructor. Creates a GatingMLFileReader that will read from the file pointed to
	 * by the uri. See GatingMLFileReader(URI) for more info about supported URIs.
	 * 
	 * @param uri A URI string of the file to be loaded.  
	 * @throws URISyntaxException Thrown if the given string is not a valid URI.
	 * @throws MalformedURLException Thrown if the URI cannot be converted to a URL.
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public GatingMLFileReader(String uri) throws URISyntaxException, MalformedURLException, SAXException, JAXBException {
		this(new URI(uri));
	}
	
	/**
	 * Constructor. Creates a GatingMLFileReader that will read from the given File.
	 * This constructor can be used for reading local files.
	 * 
	 * @param file The File to be loaded.
	 * @throws MalformedURLException Should never be thrown as URLs are created by File.toURL().
	 * @throws JAXBException Thrown if the JAXB classes needed to read a file could not be
	 * created.
	 * @throws SAXException Thrown if the schema validating Transformation files could not
	 * be read. 
	 */
	public GatingMLFileReader(File file) throws MalformedURLException, SAXException, JAXBException {
		this(file.toURL());
	}
	
	/**
	 * <p>
	 * Constructor. Creates a GatingMLFileReader that will read from the given URI.
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
	public GatingMLFileReader(URI uri) throws MalformedURLException, SAXException, JAXBException {
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
	 * Constructor. Creates a GatingMLFileReader that will read from the given URL.
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
	public GatingMLFileReader(URL url) throws SAXException, JAXBException {
		xmlFile = url;
		initReader();
	}
	
	/**
	 * Reads in the XML File and returns a GateSet containing all the Gates specified 
	 * in the file.
	 * 
	 * @return Returns a GateSet containing all the Gates specified in the file.
	 * @throws JAXBException Thrown if an unexpected error occurs that JAXB can't handle.
	 * @throws InvalidGatingMLFileException Thrown if the XML File is invalid with respect to
	 * the schema. Use getValidationEvents() to find out what went wrong.
	 * @throws InvalidGateDescriptionException Thrown if one of the gates in the XML 
	 * file does not meet the semantics described in the specification. (i.e., some rule
	 * that is not be captured in the schema.) Check the exception's message for what
	 * went wrong.
	 * @throws IOException Thrown if there was a problem reading the file.
	 */
	public GateSet read() throws JAXBException, InvalidGatingMLFileException, InvalidGateDescriptionException, IOException {
		try {
			JAXBElement<?> rootElement = reader.read(xmlFile);
			events = reader.getValidationEvents();
			
			if (events != null && events.length > 0)
				throw new InvalidGatingMLFileException("Does not validate against schema: " + events[0]);
			
			GatingML gating = (GatingML) rootElement.getValue();
			
			GateSet rv = new GateSet();
			GateFactory factory = GateFactory.newInstance(rv);
			
			for (AbstractGate jaxbGate : gating.getGates()) {
				factory.createAndAddGate(jaxbGate);
			}
			
			for (Gate g : rv) {
				g.validate();
			}
			
			return rv;
		} catch (UnmarshalException ex) {
			// Problem with the XML File -- doesn't validate against schema
			if (ex.getLinkedException() instanceof IOException)
				throw new IOException(ex.getLinkedException().getMessage());
			throw new InvalidGatingMLFileException("Does not validate against schema: " + ex.getLinkedException().getMessage());
		}
	}
	
	/**
	 * Obtain the ValidationEvents that were raised during unmarshalling.
	 * Use this to view errors in the gating XML file.
	 *   
	 * @return Returns an array of ValidationEvents containing the events raised during the 
	 * last call to read(). Each event corresponds to one error. Returns null if read() has
	 * not been called. 
	 */
	public ValidationEvent[] getValidationEvents() {
		return events;
	}
}
 