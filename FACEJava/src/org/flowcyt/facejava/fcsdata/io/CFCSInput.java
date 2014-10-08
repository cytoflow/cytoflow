package org.flowcyt.facejava.fcsdata.io;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.flowcyt.cfcs.CFCSData;
import org.flowcyt.cfcs.CFCSDataSet;
import org.flowcyt.cfcs.CFCSError;
import org.flowcyt.cfcs.CFCSErrorCodes;
import org.flowcyt.cfcs.CFCSListModeData;
import org.flowcyt.cfcs.CFCSParameter;
import org.flowcyt.cfcs.CFCSParameters;
import org.flowcyt.cfcs.CFCSSystem;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.fcsdata.exception.InvalidCFCSDataSetTypeException;
import org.flowcyt.facejava.fcsdata.exception.InvalidDataSetsException;
import org.flowcyt.facejava.fcsdata.exception.InvalidParameterNumberException;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;
import org.flowcyt.facejava.fcsdata.impl.FcsParameter;

/**
 * <p>
 * The default FcsInput. This adapter uses the CFCS library to read FCS files. (Thus,
 * it depends on CFCS being in the classpath.)
 * 
 * @author echng
 */
public class CFCSInput implements FcsInput {

	public FcsDataFile read(String uri) throws IOException, InvalidDataSetsException, URISyntaxException {
		return read(new URI(uri));
	}

	public FcsDataFile read(File file) throws IOException, InvalidDataSetsException {
		return read(file.toURI());
	}

	public FcsDataFile read(URI uri) throws IOException, InvalidDataSetsException {
		CFCSSystem readSystem = new CFCSSystem();
		try {
			readSystem.open(uri.toURL());
		} catch(CFCSError e){
			if (e.errorNumber == CFCSErrorCodes.CFCSIOError)
				throw new IOException(e.toString());
			throw e;
		} catch (IllegalArgumentException ex) {
			throw new IOException("Cannot open non-absolute URIs (" + uri.toString() + ")");
		}
		return extractData(readSystem);
	}
	
	/**
	 * Uses CFCS to extract the FCS data needed by the FCSData objects.
	 * 
	 * @param readSystem The main CFCS class that represents a single data file.
	 * @return Returns the FcsDataFile representation of the FCS data in the given CFCSSystem.
	 * @throws InvalidDataSetsException Thrown if there was an error loading one of
	 * the data sets in the FCS file. The list returned by getDataSets() will not contain
	 * these DataSets. e.g., if Data Set 0 and 2 are OK but 1 is not List Mode, only 
	 * DataSets 0 and 2 will appear in the list. Use getReasons() to find out which data
	 * sets (by index) had errors and what the error was (e.g., it had a duplicate
	 * parameter name, it wasn't in List Mode, etc.)
	 */
	private FcsDataFile extractData(CFCSSystem readSystem) throws InvalidDataSetsException {
		List<FcsDataSet> dataSets = new ArrayList<FcsDataSet>();
		
		Map<Integer, Exception> invalidDataSets = new HashMap<Integer, Exception>();
				
		for (int i = 0; i < readSystem.getCount(); ++i) {
			CFCSDataSet cfcsDs = readSystem.getDataSet(i);
			try {
				dataSets.add(extractDataSet(cfcsDs, i + 1));
			} catch (InvalidCFCSDataSetTypeException ex) {
				invalidDataSets.put(i+1, ex);
			} catch (DuplicateParameterReferenceException ex) {
				invalidDataSets.put(i+1, ex);
			} catch (InvalidParameterNumberException ex) {
				invalidDataSets.put(i+1, ex);
			}
		}
		
		if (invalidDataSets.size() > 0)
			throw new InvalidDataSetsException(invalidDataSets);
		
		return new FcsDataFile(dataSets);
	}
	
	/**
	 * Extracts the FCS Data in the CFCSDataSet and creates the corresponding FCSData objects.
	 * 
	 * @param cfcsDs The CFCSDataSet to extract data from.
	 * @param datasetNumber The dataset number of the given CFCSDataSet.
	 * @return Returns the DataSet representation of the FCS Data in the given CFCSDataSet. 
	 * @throws InvalidCFCSDataSetTypeException Thrown if the CFCSDataSet does not contain 
	 * List Mode Data.
	 * @throws InvalidParameterNumberException Thrown if one of the FCS parameters has an invalid
	 * parameter number.
	 * @throws DuplicateParameterReferenceException Thrown if there is a duplicate FCS parameter
	 * name ($PnN) in the given CFCSDataSet.
	 */
	private FcsDataSet extractDataSet(CFCSDataSet cfcsDs, int datasetNumber) throws InvalidCFCSDataSetTypeException, InvalidParameterNumberException, DuplicateParameterReferenceException {
		CFCSData readData = cfcsDs.getData();
		if (readData.getType() != CFCSData.LISTMODE) {
			throw new InvalidCFCSDataSetTypeException();
		}
				
		CFCSParameters cfcsDsParams = cfcsDs.getParameters();
		int parameterCount = cfcsDsParams.getCount();
		List<FcsParameter> parameters = new ArrayList<FcsParameter>(parameterCount);
		
		for(int i = 0; i < parameterCount; ++i) {
			CFCSParameter cfcsParam = cfcsDsParams.getParameter(i);
			FcsParameter param;
			try {
				param = new FcsParameter(cfcsParam.getShortName(), i+1);
			} catch (CFCSError e) {
				param = new FcsParameter(i+1);
			}
			parameters.add(param);
		}
		
		CFCSListModeData readLMData = (CFCSListModeData) readData;
		int eventCount = readLMData.getCount();
		List<Event> events = new ArrayList<Event>(eventCount);
		
		for (int i = 0; i < eventCount; ++i) {
			double[] doubleData = new double[parameterCount];
			readLMData.getEvent(i, doubleData);
			events.add(new Event(doubleData));
		}
		
		return new FcsDataSet(cfcsDs.getVersion(), datasetNumber, parameters, events);
	}
}
