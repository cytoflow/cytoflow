package org.flowcyt.facejava.fcsdata.io;

import java.io.File;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;

import org.flowcyt.cfcs.CFCSData;
import org.flowcyt.cfcs.CFCSDataSet;
import org.flowcyt.cfcs.CFCSDatatype;
import org.flowcyt.cfcs.CFCSListModeData;
import org.flowcyt.cfcs.CFCSParameter;
import org.flowcyt.cfcs.CFCSParameters;
import org.flowcyt.cfcs.CFCSSystem;
import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Parameter;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;

/**
 * <p>
 * Uses the CFCS library to write out a Population or all Populations in a PopulationCollection
 * (in the order returened by the collection) to a single FCS file. The FCS file will be in
 * Listmode FCS 3.0 format and the following hold:
 * 
 * <ul>
 * <li>Event values are stored as scale in floats, which means ...
 *    <ul>
 *    <li>$DATATYPE = F</li>
 *    <li>All parameters will have $PnE = 0,0</li>
 *    <li>All parameters will have $PnG = 0</li>
 *    <li>All parameters will have $PnB = 64</li>
 *    <li>All parameters will have $PnR set to the maximum value amongst all events for that
 *        parameter or 2, whichever is larger.</li>
 *    </ul>
 * </li>
 * <li>Parameters will have their name (from Parameter.getName()) stored as $PnN. If null,
 *     then $PnN is not stored.</li>
 * </ul>
 * 
 * <p>
 * To try and maximize compatibility with other cytometry software, the default datatype
 * is floats since it seems most programs have trouble reading doubles. CFCSOutput can
 * be set to output double FCS fiiles to be more in line with the upcoming FCS 4.0.
 *    
 * <p>
 * <b>Note:</b> The Parameters stored (and their corresponding data values for the events) are obtained
 * through the DataRetriever returned by Population.getRetriever(). Thus, more parameters may
 * be stored then what was originally in an FCS file. Parameter Order is the same as the order in
 * Population.getRetriever().getAllParameters(). Event order is the same as iterating through 
 * Population.getEvents(). Thus, reading in a file, immediately writing it out, then reading it
 * back in will result in the same Parameter Numbers for the same Parameters and the same Event
 * order (though event values will have been converted to scale).
 * 
 * @author echng
 */
public class CFCSOutput implements FcsOutput {

	/**
	 * Since all values stored are scale values (i.e., linear axis with no gain), $PnE is useless,
	 * so we'll zero out both of its values.
	 */
	private static final double DEFAULT_LOG_DECADES = 0;
	
	private static final double DEFAULT_LOG_OFFSET = 0;
	
	private boolean writeDoubles;
	
	/**
	 * Constructor. Defaults to writing floats in FCS files.
	 */
	public CFCSOutput() {
		this.writeDoubles = false;
	}
	
	/**
	 * Constructor.
	 * 
	 * @param writeDoubles If true, writes doubles in FCS files. Writes floats otherwise. 
	 */
	public CFCSOutput(boolean writeDoubles) {
		this.writeDoubles = writeDoubles;
	}
	
	/**
	 * Set whether or not floats or doubles should be written.
	 * 
	 * @param writeDoubles If true, writes doubles in FCS files. Writes floats otherwise. 
	 */
	public void setWriteDoubles(boolean writeDoubles) {
		this.writeDoubles = writeDoubles;
	}
	
	/**
	 * @return Returns a boolean indicating whether doubles (true) or floats (false)
	 * will be written.
	 */
	public boolean isWriteDoubles() {
		return writeDoubles;
	}
	
	public void write(String uriString, Collection<? extends Population> popColl) throws DataRetrievalException, MalformedURLException, URISyntaxException {
		write(new URI(uriString), popColl);		
	}

	public void write(File file, Collection<? extends Population> popColl) throws DataRetrievalException, MalformedURLException {
		write(file.toURL(), popColl);		
	}

	public void write(URI uri, Collection<? extends Population> popColl) throws DataRetrievalException, MalformedURLException {
		try {
			write(uri.toURL(), popColl);
		} catch (IllegalArgumentException e) {
			// URI throws this when the uri is not absolute.
			throw new MalformedURLException(e.getMessage());
		}			
	}
	
	public void write(URL url, Collection<? extends Population> popColl) throws DataRetrievalException {
		CFCSSystem system = new CFCSSystem();
		system.create(url.toString());
		
		for (Population pop : popColl) {
			writePopulation(system, pop);
		}
		
		system.close();
	}
	
	public void write(String uriString, Population pop) throws DataRetrievalException, MalformedURLException, URISyntaxException {
		write(new URI(uriString), pop);	
	}

	public void write(File file, Population pop) throws DataRetrievalException, MalformedURLException {
		write(file.toURL(), pop);
	}

	public void write(URI uri, Population pop) throws DataRetrievalException, MalformedURLException {
		try {
			write(uri.toURL(), pop);
		} catch (IllegalArgumentException e) {
			// URI throws this when the uri is not absolute.
			throw new MalformedURLException(e.getMessage());
		}	
	}
	
	public void write(URL url, Population pop) throws DataRetrievalException {
		CFCSSystem system = new CFCSSystem();
		system.create(url.toString());
		
		writePopulation(system, pop);
		
		system.close();
	}
	
	/**
	 * Adds a Population to the given CFCSSystem as a new data set in the file. The
	 * Population's default DataRetriever (from Population.getRetriever()) is used as the source
	 * of the parameters to be included in the FCS file. All Parameters in the retriever (and
	 * their corresponding scale values for each event) will be written into the file.
	 * 
	 * @param system The CFCSSystem to add the Population to.
	 * @param pop The Population to be added to the CFCSSystem
	 * @throws DataRetrievalException Thrown if there was a problem retrieving data from the
	 * Population.
	 */
	private void writePopulation(CFCSSystem system, Population pop) throws DataRetrievalException {
		CFCSDataSet cfcsDs;
		
		if (writeDoubles)
			cfcsDs = system.createDataSet(CFCSData.LISTMODE, CFCSDatatype.DOUBLE);
		else
			cfcsDs = system.createDataSet(CFCSData.LISTMODE, CFCSDatatype.FLOAT);
		
		CFCSParameters cfcsParams = cfcsDs.getParameters();
		
		DataRetriever retriever = pop.getRetriever();
		
		// Parameters must be ordered when writing FCS files
		List<Parameter> parameters = new ArrayList<Parameter>(retriever.getAllParameters());
		
		// We created it to be list mode so the cast should be fine.
		CFCSListModeData cfcsData = (CFCSListModeData) cfcsDs.getData();
		
		double[] range = new double[parameters.size()];
		Arrays.fill(range, Double.NEGATIVE_INFINITY);
		
		if (writeDoubles)
			writeDoubleData(cfcsData, pop, parameters, retriever, range);
		else
			writeFloatData(cfcsData, pop, parameters, retriever, range);
		
		int i = 0;
		for (Parameter param : parameters) {
			CFCSParameter cfcsParam = new CFCSParameter();
			
			if (writeDoubles)
				cfcsParam.setFieldSize(Double.SIZE);
			else
				cfcsParam.setFieldSize(Float.SIZE);
			
			if (!param.getReference().equals(ParameterReference.UNREFERENCABLE))
				cfcsParam.setShortName(param.getReference().getValue());
			
			cfcsParam.setLogDecades(DEFAULT_LOG_DECADES);
			cfcsParam.setOffset(DEFAULT_LOG_OFFSET);
			
			int pnr = (int) Math.min(Integer.MAX_VALUE, Math.max(2, Math.ceil(range[i++])));
			cfcsParam.setRange(pnr);
			
			cfcsParams.addParameter(cfcsParam);
		}
	}
	
	private void writeDoubleData(CFCSListModeData cfcsData, Population pop, List<Parameter> parameters, DataRetriever retriever, double[] range) throws DataRetrievalException {
		double[] eventData = new double[parameters.size()];
		for (Event ev : pop) {
			int i = 0;
			for (Parameter param : parameters) {
				eventData[i] = retriever.getScale(param, ev);
				range[i] = Math.max(range[i], eventData[i]);
				++i;
			}
			cfcsData.addEvent(eventData);
		}
	}
	
	private void writeFloatData(CFCSListModeData cfcsData, Population pop, List<Parameter> parameters, DataRetriever retriever, double[] range) throws DataRetrievalException {
		float[] eventData = new float[parameters.size()];
		for (Event ev : pop) {
			int i = 0;
			for (Parameter param : parameters) {
				eventData[i] = (float) retriever.getScale(param, ev);
				range[i] = Math.max(range[i], eventData[i]);
				++i;
			}
			cfcsData.addEvent(eventData);
		}
	}
}
