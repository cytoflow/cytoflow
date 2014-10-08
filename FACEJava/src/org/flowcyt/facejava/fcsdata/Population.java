package org.flowcyt.facejava.fcsdata;

import java.util.Collection;

import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.statistics.PopulationStatistics;

/**
 * <p>
 * Represents a Population of Events measured by the cytometer. Population is inherently
 * a Collection of Events so it will extend from Collection&lt;Event&gt; so that the
 * Collections Framework can be leveraged. Populations can have parent Populations where
 * the population is related to the parent in some way (e.g., a subset).
 * 
 * <p>
 * Note that order of Events <i>may</i> matter. So (where possible) Events should be used in
 * the order returned by the collection's iterator. For Populations with order, they
 * should implement List&lt;Event&gt;.
 * 
 * <p>
 * Although, in most cases, Populations are not modifiable (as it makes normally makes
 * no sense to be able to add arbitrary Events to a Population), it is not
 * enforced by the interface. Modifying methods in Unmodifiable populations will 
 * throw UnsupportedOperationExceptions (as specified in the Collections framework).
 * 
 * <p>
 * A Population contains a default DataRetriever which should be used whenever event
 * data needs to be retrieved from that Population.
 * 
 * @author echng
 */
public interface Population extends Collection<Event> {
	
	/**
	 * @return Returns the parent Population of this Population. This population is related
	 * to the events that are contained by the parent Population. If the population has
	 * no parent, null is returned.
	 */
	public Population getParentPopulation(); 
	
	/**
	 * @return Returns the PopulationStatistics object which contains descriptive statistics
	 * about the Population. Note: Statistics are only calculated for Parameters which are
	 * in the Population's default DataRetriever. So it is up to implementors exactly
	 * which Parameters stats should be calculated for.
	 * @throws DataRetrievalException Thrown if data could not be retrieved from the population
	 * when calculating statistics.
	 */
	public PopulationStatistics getStatistics() throws DataRetrievalException;
	
	/**
	 * @return Returns the default DataRetriever to use to get data from the events in the
	 * Population. The DataRetriever object returned may or may not always be the same
	 * DataRetriver instance. The implementor should document which parameters are included
	 * in the DataRetriever.
	 */
	public DataRetriever getRetriever();
}
