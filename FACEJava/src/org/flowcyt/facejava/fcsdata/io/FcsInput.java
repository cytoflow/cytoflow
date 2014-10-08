package org.flowcyt.facejava.fcsdata.io;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;

import org.flowcyt.facejava.fcsdata.exception.InvalidDataSetsException;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;

/**
 * <p>
 * This interface is meant to be used as a generic facade to allow us to hook in any library 
 * that can read FCS data files and produce FCSData objects. For each FCS input library, a class
 * implementing this interface is created. The class will use the library's methods to extract
 * the data that is needed by the FSCData objects, create the FCSData objects and return them
 * to the caller in an FcsDataFile. 
 * 
 * @author echng
 */
public interface FcsInput {
	
	/**
	 * Open the given string as a URI. See read(URI) for more info about supported URIs.
	 * 
	 * @param uriString A string representation of the URI to open.
	 * @return Returns an FcsDataFile representing the FCS file at the location specified by the
	 * URI string.
	 * @throws IOException Thrown if the FCS file could not be read. Possible reasons:
	 * - The URI is not absolute.
	 * - There is no protocol handler for the given protocol.
	 * - The URI cannot be loaded.
	 * @throws InvalidDataSetsException Thrown if there was an error loading one of
	 * the data sets in the FCS file. The list returned by getDataSets() will not contain
	 * these DataSets. e.g., if Data Set 0 and 2 are OK but 1 is not List Mode, only 
	 * DataSets 0 and 2 will appear in the list. Use getReasons() to find out which data
	 * sets (by index) had errors and what the error was (e.g., it had a duplicate
	 * parameter name, it wasn't in List Mode, etc.)
	 * @throws URISyntaxException Thrown if a URI could not be created from the given String
	 * because it does not follow the URI format.
	 */
	public FcsDataFile read(String uriString) throws IOException, InvalidDataSetsException, URISyntaxException;
	
	/**
	 * <p>
	 * Opens the given URI. 
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
	 * @param uri The URI to open
	 * @return Returns an FcsDataFile representing the FCS file at the location specified by the
	 * URI string.
	 * @throws IOException Thrown if the FCS file could not be read. Possible reasons:
	 * - The URI is not absolute (no protocol ... we need to know how to load it).
	 * - There is no protocol handler for the protocol of the given URI.
	 * - The URI cannot be loaded for some reason (e.g.., file not found, etc.).
	 * @throws InvalidDataSetsException Thrown if there was an error loading one of
	 * the data sets in the FCS file. The list returned by getDataSets() will not contain
	 * these DataSets. e.g., if Data Set 0 and 2 are OK but 1 is not List Mode, only 
	 * DataSets 0 and 2 will appear in the list. Use getReasons() to find out which data
	 * sets (by index) had errors and what the error was (e.g., it had a duplicate
	 * parameter name, it wasn't in List Mode, etc.)
	 */
	public FcsDataFile read(URI uri) throws IOException, InvalidDataSetsException;
	
	/**
	 * Opens the given File. Use this method to open file's on the local filesystem.
	 * 
	 * @param file The File to open.
	 * @return Returns an FcsDataFile representing the FCS file represented by the given File.
	 * @throws IOException Thrown if the FCS file could not be read.
	 * @throws InvalidDataSetsException Thrown if there was an error loading one of
	 * the data sets in the FCS file. The list returned by getDataSets() will not contain
	 * these DataSets. e.g., if Data Set 0 and 2 are OK but 1 is not List Mode, only 
	 * DataSets 0 and 2 will appear in the list. Use getReasons() to find out which data
	 * sets (by index) had errors and what the error was (e.g., it had a duplicate
	 * parameter name, it wasn't in List Mode, etc.)
	 */
	public FcsDataFile read(File file) throws IOException, InvalidDataSetsException;
}
