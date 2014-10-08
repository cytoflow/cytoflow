package org.flowcyt.facejava.fcsdata.io;

import java.io.File;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.Collection;

import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;

/**
 * <p>
 * Handles writing out either all the Populations in a PopulationCollection (in the same
 * order as returned by PopulationCollection.getPopulations()) or a single Population to an FCS
 * file. Populations are written as DataSets. By default, the Parameters stored for each Population
 * are the Parameters contained in the DataRetriever returned by Population.getRetriever().
 * 
 * <p>
 * This interface is a generic facade between the FCSData classes and a library which can
 * handle writing FCS files. Each implementation of the interface will use their library to
 * write out the FCS file. Each implementation may have special restrictions on the created FCS
 * file. See their comments.
 * 
 * @author echng
 */
public interface FcsOutput {
	
	/**
	 * Writes a Collection of Populations to an FCS file containing which will contain
	 * a data set for each of the Populations in the Collection. The data sets will be
	 * ordered in the same order as they are returned by the Collection's iterator. 
	 *  
	 * @param uriString A URI string for where the file will be written to.
	 * @param popColl A Collection containing the Populations to write to the FCS
	 * file.
	 * @throws DataRetrievalException Thrown if there was a problem reading event data.
	 * @throws MalformedURLException Thrown if the URI is not absolute (contains no scheme) or
	 * is not a valid URL.
	 * @throws URISyntaxException Thrown if the String is not a valid URI.
	 */
	public void write(String uriString, Collection<? extends Population> popColl) throws DataRetrievalException, MalformedURLException, URISyntaxException;
	
	/**
	 * Writes a Collection of Populations to an FCS file containing which will contain
	 * a data set for each of the Populations in the Collection. The data sets will be
	 * ordered in the same order as they are returned by the Collection's iterator. 
	 * 
	 * @param file The local file to write to.
	 * @param popColl A Collection containing the Populations to write to the FCS
	 * file.
	 * @throws DataRetrievalException Thrown if there was a problem reading event data.
	 * @throws MalformedURLException Thrown if the URI is not absolute (contains no scheme) or
	 * is not a valid URL.
	 */
	public void write(File file, Collection<? extends Population> popColl) throws DataRetrievalException, MalformedURLException;
	
	/**
	 * Writes a Collection of Populations to an FCS file containing which will contain
	 * a data set for each of the Populations in the Collection. The data sets will be
	 * ordered in the same order as they are returned by the Collection's iterator. 
	 * 
	 * @param uri The URI of where the file will be written to. Note that we must be able to
	 * write to something so the URI is converted to a URL first. So the URI must be absolute.
	 * @param popColl A Collection containing the Populations to write to the FCS
	 * file.
	 * @throws DataRetrievalException Thrown if there was a problem reading event data.
	 * @throws MalformedURLException Thrown if the URI is not absolute (contains no scheme) or
	 * is not a valid URL.
	 */
	public void write(URI uri, Collection<? extends Population> popColl) throws DataRetrievalException, MalformedURLException;
	
	/**
	 * Writes a Collection of Populations to an FCS file containing which will contain
	 * a data set for each of the Populations in the Collection. The data sets will be
	 * ordered in the same order as they are returned by the Collection's iterator. 
	 * 
	 * @param url The URL of where the file will be written to.
	 * @param popColl A Collection containing the Populations to write to the FCS
	 * file.
	 * @throws DataRetrievalException Thrown if there was a problem reading event data.
	 */
	public void write(URL url, Collection<? extends Population> popColl) throws DataRetrievalException;
	
	/**
	 * Writes a Population to an FCS file containing one data set with the data in the population.
	 * 
	 * @param uriString A URI string for where the file will be written to.
	 * @param pop The Population to write to a FCS file.
	 * @throws DataRetrievalException Thrown if there was a problem reading event data.
	 * @throws MalformedURLException Thrown if the URI is not absolute (contains no scheme) or
	 * is not a valid URL.
	 * @throws URISyntaxException Thrown if the String is not a valid URI.
	 */
	public void write(String uriString, Population pop) throws DataRetrievalException, MalformedURLException, URISyntaxException;
	
	/**
	 * Writes a Population to an FCS file containing one data set with the data in the population.
	 *
	 * @param file The local file to write to.
	 * @param pop The Population to write to a FCS file.
	 * @throws DataRetrievalException Thrown if there was a problem reading event data.
	 * @throws MalformedURLException Thrown if the URI is not absolute (contains no scheme) or
	 * is not a valid URL.
	 */
	public void write(File file, Population pop) throws DataRetrievalException, MalformedURLException;
	
	/**
	 * Writes a Population to an FCS file containing one data set with the data in the population.
	 *
	 * @param uri The URI of where the file will be written to. Note that we must be able to
	 * write to something so the URI is converted to a URL first. So the URI must be absolute.
	 * @param pop The Population to write to a FCS file.
	 * @throws DataRetrievalException Thrown if there was a problem reading event data.
	 * @throws MalformedURLException Thrown if the URI is not absolute (contains no scheme) or
	 * is not a valid URL.
	 */
	public void write(URI uri, Population pop) throws DataRetrievalException, MalformedURLException;
	
	/**
	 * Writes a Population to an FCS file containing one data set with the data in the population.
	 *
	 * @param url The URL of where the file will be written to.
	 * @param pop The Population to write to a FCS file.
	 * @throws MalformedURLException Thrown if the URI is not absolute (contains no scheme) or
	 * is not a valid URL.
	 */
	public void write(URL url, Population pop) throws DataRetrievalException;
}
