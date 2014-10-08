package org.flowcyt.facejava.compensation;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

import org.apache.commons.math.linear.InvalidMatrixException;
import org.apache.commons.math.linear.MatrixUtils;
import org.apache.commons.math.linear.RealMatrix;
import org.flowcyt.facejava.compensation.exception.InvalidCompensationMatrixException;
import org.flowcyt.facejava.fcsdata.AbstractOrderedPopulation;
import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;
import org.flowcyt.facejava.fcsdata.impl.FcsParameter;

/**
 * <p>A CompensatedDataSet contains the Events of a FcsDataSet
 * after compensation has been applied using the spillover values from a given
 * SpilloverMatrix.
 * 
 * <p>
 * The compensation is calculated as follows. We apply a total ordering on any FcsParameters
 * which have a spillover specified *and* are in the given FcsDataSet. This total ordering is
 * used to determine a matrix structure where the spillover values for the i-th parameter
 * is in the i-th row and the i-th column. Entry Aij corresponds to the ratio of spillover
 * from the j-th to the i-th parameter and is called the spillover coefficient (see the comments
 * for SpilloverMatrix for more details).
 * 
 * <p>
 * Then, for a given Event we create the vector V such that the i-th entry in V is the
 * event data for the i-th parameter.  
 * 
 * The general compensation equation is A * F = M, where A is the created matrix, F
 * is the true fluorescense values and M is the measured fluoresence values.
 * 
 * Thus, to compensate the (uncompensated) data, V = M and we use A-inverse to find F. 
 *    <pre>A-inverse * A * F = F = A-inverse * M =  A-inverse * V</pre>
 * 
 * And to uncompensate the (compensated) data, V = F and thus,
 *    <pre>M = A * F = A * V</pre>
 * <p>
 * <b>Notes:</b>
 * 
 * <ul>
 * <li>Compensation can only be applied with the Parameters in an FCS file and not any
 *     derived parameters like transformations.
 * <li>From the above, we get that Compensation can only be applied to FcsDataSets since
 *     they have only FCS Parameters.
 * <li>The resulting population contains new Event objects which correspond to the Events
 *     in the FcsDataSet. i.e., the first event in the list of Events in the
 *     CompensatedDataSet contains the compensated event values for the first event in the
 *     FcsDataSet.
 * <li>The uncompensated Events can be retrieved from the original FcsDataSet returned by
 *     getParentPopulation().
 * </ul> 
 * 
 * <p>
 * See <a href="http://www.drmr.com/compensation/indexDetail.html">http://www.drmr.com/compensation/indexDetail.html</a>
 * for more information about compensation.
 * 
 * @author echng
 */
public class CompensatedDataSet extends AbstractOrderedPopulation {
	// XXX: Should we allow compensation on arbitrary populations? How would that affect say
	// a compensation on a population that has a parent? Since events could appear in both,
	// the parent could end up with some of its events compensated while some are not.
	// One solution could be to return a new compensated population instead of mutating the
	// original. Also how to handle Parameters which aren't FcsParameters (like Transformations).
	// Is the compensation calculation valid for them?
	
	/**
	 * A list containing the FcsParameters that were involved in the compensation calculation.
	 * i.e., they are in the compensated FcsDataSet and have a Parametereference that is in the
	 * SpilloverMatrix. 
	 */
	private List<FcsParameter> compensatedParameters;
		
	/**
	 * Constructor. Creates a CompensatedDataSet.
	 * 
	 * @param ds The FcsDataSet to be compensated. Its Events will not be changed.
	 * @param spillovers The spillover values to use when compensating.
	 * @throws InvalidCompensationMatrixException Thrown if the Compensation Matrix (built from the
	 * Parameters in the SpilloverMatrix that are in the given data set) is singular
	 * (non-invertible).
	 */
	public CompensatedDataSet(FcsDataSet ds, SpilloverMatrix spillovers) throws InvalidCompensationMatrixException {
		super(ds);
		
		this.compensatedParameters = new ArrayList<FcsParameter>();
		
		// Compensation will be finished by the end of the next group of statements.
		List<ParameterReference> parameterReferenceList = buildParameterList(spillovers.getSpecifiedParameterReferences());	
		try {
			compensate(buildCompensationMatrix(spillovers, parameterReferenceList));
		} catch (DataRetrievalException e) {
			throw new AssertionError("Should be no problems. We know the Parameters exist and FcsParameters should never have a problem retrieving data.");
		}
	}
	
	/**
	 * Determines which of the ParameterReferences in the given SpilloverCoefficients can be 
	 * resolved to Parameters in the FcsDataSet and applies a total ordering to them by adding
	 * them to the compensatedParameters list. The returned list of ParameterReferences are the
	 * ParameterReferences that were resolved successfully and its order corresponds to the
	 * order in compensatedParameters.
	 * 
	 * @param allParameterReferences A Set containing all the ParameterReferences that have
	 * spillovers specified.
	 * @returns parameterReferenceList Returns a list of ParameterReferences that are the
	 * ParameterReferences that were resolved successfully and its order corresponds to the
	 * order in compensatedParameters.
	 */
	private List<ParameterReference> buildParameterList(Set<ParameterReference> allParameterReferences) {
		List<ParameterReference> rv = new ArrayList<ParameterReference>();
		DataRetriever retriever = this.getParentPopulation().getRetriever();
		for (ParameterReference parameterReference : allParameterReferences) {
			try {
				// The cast should be ok since FcsDataSets can only have FcsParameters as
				// parameters. 
				compensatedParameters.add((FcsParameter)retriever.resolveReference(parameterReference));
				rv.add(parameterReference);
			} catch (ClassCastException e) {
				throw new AssertionError("Only Parameters from a FCS file can be compensated.");
			}	
			catch (NoSuchParameterException e) {
				// Don't do anything. We're trying to determine what's present in the data
				// set and what's not.
			}
		}
		return rv;
	}
	
	/**
	 * Uses the total ordering given by the compensatedParameters List to build the
	 * compensation matrix's inverse to be used to compensate the DataSet. 
	 * 
	 * @param spillovers Contains the spillover values to be used in the compensation matrix.
	 * @param parameterReferenceList A list of the ParameterReferences that are the
	 * ParameterReferences that were resolved successfully and its order corresponds to the
	 * order in compensatedParameters.
	 * @throws InvalidCompensationMatrixException Thrown if the compensation matrix is singular and
	 * non-invertible.
	 */
	private RealMatrix buildCompensationMatrix(SpilloverMatrix spillovers, List<ParameterReference> parameterReferenceList) throws InvalidCompensationMatrixException {
		if (getCompensatedParameterCount() <= 0)
			return null;
		
		int dimensions = parameterReferenceList.size();
		double[][] matrixData = new double[dimensions][dimensions];
		
		int i = 0;
		for (ParameterReference parameterReference : parameterReferenceList) {
			int j = 0;
			for (ParameterReference otherParameterReference : parameterReferenceList) {
				matrixData[i][j++] = spillovers.getSpilloverValue(parameterReference, otherParameterReference);
			}
			++i;
		}
		
		RealMatrix compensationMatrix = MatrixUtils.createRealMatrix(matrixData);
		try {
			return compensationMatrix.inverse();
		} catch (InvalidMatrixException e) {
			throw new InvalidCompensationMatrixException(e);
		}
	}
	
	/**
	 * Applies the compensation to the DataSet. The compensation is only performed if the
	 * DataSet is not already compensated. The compensatedEvents list is only .
	 *  
	 * @return Returns true if the compensation took place and false if the DataSet has
	 * already been compensated and compensation was not performed.
	 * @throws DataRetrievalException Thrown if the event data could not be retrieved.
	 */
	private void compensate(RealMatrix compensationMatrixInverse) throws DataRetrievalException {
		// XXX: Rather than compensate one event at a time we can compensate all events by 
		// building a matrix where each column contains the data for one event, then perform
		// a left-multiply with the inverse of the compensation matrix.	The result will have
		// the compensated events in the columns. Only problem is (maybe) the memory requirements
		// when there are hundreds of thousands of events.
		
		if (getCompensatedParameterCount() > 0) {
			for (Event ev : this.getParentPopulation()) {
				double[] measuredVals = getCurrentEventData(ev);
				double[] trueVals = compensationMatrixInverse.operate(measuredVals);
				this.events.add(makeNewEvent(ev, trueVals));				
			}
		} else {
			this.events.addAll(this.getParentPopulation());
		}
	}
	
	/**
	 * Creates a vector containing the current event data with the correct total ordering.
	 * 
	 * @param ev The event to get the data from.
	 * @return Returns an array which represents the vector of event data.
	 * @throws DataRetrievalException Thrown if the event data could not be retrieved.
	 */
	private double[] getCurrentEventData(Event ev) throws DataRetrievalException {
		double[] measuredVals = new double[compensatedParameters.size()];
		int i = 0;
		DataRetriever retriever = this.getParentPopulation().getRetriever();
		for (FcsParameter param : compensatedParameters) {
			measuredVals[i++] = retriever.getScale(param, ev);
		}
		return measuredVals;
	}
	
	/**
	 * Creates a new Event that contains the data in newValues for the parameters that
	 * were involved in the un/compensation and the data in oldEvent for the rest of the
	 * parameters.
	 * 
	 * @param oldEvent The old event whose data the new Event will use for non-compensated
	 * parameters.
	 * @param newValues The new values for the compensated parameters to put in the event. The
	 * order in the array must follow the total ordering imposed by parameterList.
	 */
	private Event makeNewEvent(Event oldEvent, double[] newValues) {
		double[] newEventData = oldEvent.getData();
		
		int i = 0;
		for (FcsParameter param : compensatedParameters) {
			newEventData[param.getParameterNumber() - 1] = newValues[i++];
		}
		
		return new Event(newEventData);
	}	
		
	/**
	 * @return Returns the number of parameters in the data set that have been compensated.
	 * i.e, the number of rows (and columns) in the compensation matrix OR the number of
	 * ParameterReferences in the given SpilloverMatrix that are resolved successfully to 
	 * FcsParameters in the given FcsDataSet.
	 */
	public int getCompensatedParameterCount() {
		return compensatedParameters.size();
	}
	
	/**
	 * @return Returns a list of the FcsParameters in the data set that are involved in the
	 * compensation calculations. The parameters are in the same order as the total ordering
	 * that was used during construction of the compensation matrix. 
	 */
	public List<FcsParameter> getCompensatedParameters() {
		return Collections.unmodifiableList(compensatedParameters);
	}
	
	/**
	 * @return Returns the FcsDataSet that the Compensator operates upon. It contains the
	 * uncompensated events.
	 */
	public FcsDataSet getParentPopulation() {
		return (FcsDataSet) super.getParentPopulation();
	}

	/**
	 * @return Returns the same retriever as the FcsDataSet that was compensated.
	 */
	public DataRetriever getRetriever() {
		return this.getParentPopulation().getRetriever();
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("Compensation Parameters: ");
		
		for (FcsParameter param : compensatedParameters) {
			builder.append(param.getReference().getValue());
			builder.append("\t");
		}
		builder.append("\n");
		
		builder.append("# Events: ");
    	builder.append(this.size());
    	builder.append("\n");
    	return builder.toString();
	}
}
