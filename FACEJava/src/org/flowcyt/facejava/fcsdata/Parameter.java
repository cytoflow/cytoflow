package org.flowcyt.facejava.fcsdata;

import java.util.Set;

import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;

/**
 * <p>
 * A Parameter represents a way to get data from an Event. That is, for any
 * defined way of retrieving data from an Event, it should implement Parameter.
 * 
 * <p>
 * E.g., for regular parameters in the FCS file, the data is retrieved directly from
 * the Event. For transformations, a tranformation is applied to the data before being
 * returned.
 * 
 * @author echng
 */
public interface Parameter {
	/**
	 * <p>
	 * Scale data is what would be presented to the user. i.e., if the channel data is
	 * 256, a gain of 2 is specified in the parameter (through $PnG), and the data is linear
	 * (a $PnE of 0,0) then the scale value is 256 / 2 = 128. If the data was logarithmic,
	 * with a $PnR of 1024 and a $PnE of 4,0 then the scale value is 10^(256 * 4 / 1024) = 10.
	 * 
	 * <p>
	 * This is the only data (as opposed to channel) that we use (in any place). 
	 * 
	 * @param ev The event to retrieve the scale data from.
	 * @param retriever The retriever to use to get scale data from any parameters
	 * that this parameter depends on (e.g., transformations).
	 * @return Returns the scale data associated with this parameter for the given 
	 * event.
	 * @throws DataRetrievalException Thrown if there was a problem retrieving the data.
	 * (e.g., a dependency cannot be resolved to a Parameter object.)
	 */
	public double getScale(Event ev, DataRetriever retriever) throws DataRetrievalException;
	
	/**
	 * @return Returns the ParameterReference that can be used to reference the 
	 * Parameter. If there is no way to reference the Parameter, 
	 * ParameterReference.UNREFERENCABLE must be returned.
	 */
	public ParameterReference getReference();
	
	/**
	 * @return Returns a set of identifiers for all the parameters that this parameter
	 * depends on when it is retrieving the data from an event. 
	 */
	public Set<ParameterReference> getDependencies();
}
