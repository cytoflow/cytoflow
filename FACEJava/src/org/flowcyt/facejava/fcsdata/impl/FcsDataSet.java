package org.flowcyt.facejava.fcsdata.impl;

import java.util.Collections;
import java.util.List;

import org.flowcyt.facejava.fcsdata.AbstractOrderedPopulation;
import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Parameter;
import org.flowcyt.facejava.fcsdata.exception.CircularParameterDependencyException;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.fcsdata.exception.InvalidParameterNumberException;

/**
 * <p>
 * Represents a single Data Set within a FCS data file.
 * 
 * <p>
 * The FcsDataSet orders its Events by the order they appear in the FCS file. This
 * ordering is kept as a convenience so that when writing out a FcsDataSet to a new file
 * the Events will appear in the same order. Thus, although it is preferable to keep
 * this relative ordering it is not enforced.
 * 
 * <p>
 * The Population is unmodifiable.
 * 
 * @author echng
 */
public class FcsDataSet extends AbstractOrderedPopulation {
	/**
	 * The FCS version of the data set.
	 */
	private String fcsVersion;
	
	/**
	 * The data set number in the FCS file. Starts from 1.
	 */
	private int datasetNumber;
	
	/**
	 * The FcsParameters in the data set. The order in the list corresponds to the
	 * order of the values within Events in the data set.
	 */
	private FcsParameterList parameters;
	
    /**
     * The default DataRetriever for the FCS data set. It uses only the FcsParameters
     * that were part of the original data set. 
     */
    private DataRetriever retriever;
	
    /**
     * Creates a DataSet with the given Parameters and Events.
     * 
     * @param fcsVersion The Version string of the FCS Data Set.
     * @param datasetNumber The data set's number in the FCS file. Starts from 1.
     * @param parameters A list containing the parameters in the FCS file for the data set. The
     * parameters must be in order sorted by their Parameter number. Also, there can be no gaps in 
     * parameter number (i.e, parameter 4 then parameter 6 next).
     * @param events The Events in the FcsDataSet. The order of the Events in the List will
     * be preserved.
     * @throws InvalidParameterNumberException Thrown if the parameter number of at least one
	 * of the given parameters is not the expected Parameter number. (i.e., not equal to one more
	 * than the list index its at.) 
	 * @throws DuplicateParameterReferenceException Thrown if there are multiple Parameter that
	 * can be referenced with the same ParameterReference
	 */
	public FcsDataSet(String fcsVersion, int datasetNumber, List<FcsParameter> parameters, List<Event> events) throws InvalidParameterNumberException, DuplicateParameterReferenceException {
		super(null, events);
		
		this.fcsVersion = fcsVersion;
		this.datasetNumber = datasetNumber;
		this.parameters = new FcsParameterList(parameters);
		
		try {
			retriever = new DataRetriever(Collections.singletonList(this.parameters));
		} catch (CircularParameterDependencyException e) {
			throw new AssertionError("FcsParameters should not be depending on any other parameters.");
		}
	}

	/**
	 * @return Returns the FCS version of the data set. 
	 */
    public String getFCSVersion() {
    	return fcsVersion;    	
    }
	
	/**
	 * @return Returns the data set number of this data set in its FCS file. Starts
	 * from 1.
	 */
	public int getDataSetNumber() {
		return datasetNumber;
	}
    
    /**
     * The DataRetriever contains the FcsParameters that are in this data set. The same 
     * DataRetriever instance is always returned.
     */
	public DataRetriever getRetriever() {
		return retriever;
	}
	
	/**
	 * Order matters for FcsDataSet. The FcsParameters are ordered by their Parameter Number.
	 */
	public FcsParameterList getParameters() {
		return parameters;
	}
	
	/**
	 * Convenience method for getParameters().size() ... go Demeter!
	 * 
	 * @return Returns the number of parameters in the data set.
	 */
	public int getParameterCount() {
		return parameters.size();
	}
	    
    public String toString() {
    	StringBuilder builder = new StringBuilder();
    	builder.append("Data Set Number: ");
    	builder.append(this.datasetNumber);
    	builder.append("\nVersion: ");
    	builder.append(this.getFCSVersion());
    	builder.append("; # Events: ");
    	builder.append(this.size());
    	builder.append("; # Parameters: ");
    	builder.append(this.parameters.size());
    	builder.append("\n");
    	for (Parameter param : this.getParameters()) {
    		builder.append(param.toString());
    		builder.append("\n");
    	}
    	return builder.toString();
    }
}
