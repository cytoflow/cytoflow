package org.flowcyt.facejava.fcsdata.statistics;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Parameter;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;

/**
 * <p>
 * This class contains methods for obtaining Descriptive Statistics about a Population. Since most
 * statistics are only useful when calculated for a specific parameter (i.e., using the data values
 * for one parameter from all events to calculate some statistic), the constructor takes a
 * DataRetriever to use to get values from Events in the population. Statistics are calculated 
 * for all the parameters in the ParameterCollections given to the DataRetriever. This class
 * also calculates the few statistics which are not parameter-specific.
 * 
 * @author echng
 */
public class PopulationStatistics {
	
	/**
	 * The Population that this PopulationStatistics was calculated for.
	 */
	private Population population;
	
	/**
	 * The DataRetriever used to get event data from Events. It also defines which Parameters
	 * statistics are calculated for (by having them in one of the ParameterCollections that
	 * is given to it.)
	 */
	private DataRetriever retriever;
	
	/**
	 * Maps each Parameter in the given DataRetriever to its ParameterStatistics object.
	 */
	private Map<Parameter, PopulationParameterStatistics> parameterStats;
	
	/**
	 * Constructor. Statistics are calculated for the events currently in the population. If 
	 * new Events are added to the Population after construction, then the Statistics object
	 * must be updated with those events using update(). The default Dataretriever for the Population
	 * is used to retrieve data. 
	 * 
	 * @param pop The Population to calculate statistics for.
	 * @throws DataRetrievalException Thrown if data could not be retrieved.
	 */
	public PopulationStatistics(Population pop) throws DataRetrievalException {
		this(pop, pop.getRetriever());
	}
	
	/**
	 * Constructor. Statistics are calculated for the events currently in the population. If 
	 * new Events are added to the Population after construction, then the Statistics object
	 * must be updated with those events using update().
	 * 
	 * @param pop The Population to calculate statistics for.
	 * @param retriever The DataRetriever to use to get event data from the population. Also,
	 * statistics will only be calculated for parameters in the retriever.  
	 * @throws DataRetrievalException Thrown if data could not be retrieved.
	 */
	public PopulationStatistics(Population pop, DataRetriever retriever) throws DataRetrievalException {
		this.population = pop;
		this.retriever = retriever;
		parameterStats = new HashMap<Parameter, PopulationParameterStatistics>();
		for (Parameter param : retriever.getAllParameters()) {
			parameterStats.put(param, new PopulationParameterStatistics(this, param));
		}
		this.update(pop);
	}
	
	/**
	 * Updates the calculated statistics to include the given collection of new events. 
	 * 
	 * @param newEvents The Collection of Events to be used to update the calculated stats. These
	 * Events must not have already been in a Collection that update() was called with.
	 * @throws DataRetrievalException Thrown if there was a problem retrieving data 
	 * from the Events during stats calculations.
	 */
	public void update(Collection<Event> newEvents) throws DataRetrievalException {
		for (PopulationParameterStatistics paramStat : parameterStats.values()) {
			paramStat.update(newEvents);
		}
	}
	
	/**
	 * @return Returns the DataRetriever used to retrieve data from Events for calculation.
	 */
	public DataRetriever getRetriever() {
		return retriever;
	}	
	
	/**
	 * @return Returns the percent of events in the (immediate) parent population that are
	 * in the population the statistics were calculated for.
	 */
	public double getPercentOfParent() {
		if (population.getParentPopulation() == null)
			return 100;
		return ((double)getN()) / population.getParentPopulation().size() * 100;
	}
	
	/**
	 * @return Returns the percent of events for each of the (grand-)parent populations that are
	 * in the population the statistics were calculated for. The list starts with the percent
	 * of the immediate parent (i.e., the same value as getPercentofParent()), followed by
	 * the grandparent and so on.
	 */
	public List<Double> getPercentofParents() {
		List<Double> rv = new ArrayList<Double>();
		Population current = population.getParentPopulation();
		while (current != null) {
			rv.add(((double)getN()) / current.size() * 100);
		}		
		return rv;		
	}
	
	/**
	 * @return Returns the number of events inside the gate. This method returns the same 
	 * value as population.getEventCount() (where population is the Population specified
	 * during construction).
	 */
	public int getN() {
		return population.size();
	}
	
	/**
	 * @return Returns a collection containing the ParameterStatistics for all Parameters
	 * in the DataRetriver.
	 */
	public Collection<PopulationParameterStatistics> getAllParameterStatistics() {
		return Collections.unmodifiableCollection(parameterStats.values());
	}
	
	/**
	 * @param param The Parameter to retrieve the ParameterStatistics object for.
	 * @return Returns the ParameterStatistics object for the given Parameter.
	 */
	public PopulationParameterStatistics getParameterStatistics(Parameter param) {
		return parameterStats.get(param);
	}
	
	/**
	 * @param parameterReference The ParameterReference to the Parameter to retrieve the
	 * ParameterStatistics object for. The reference is resolved using the retriever given
	 * at construction.
	 * @return Returns the ParameterStatistics object for the given Parameter.
	 * @throws NoSuchParameterException Thrown if the reference could not be resolved.
	 */
	public PopulationParameterStatistics getParameterStatistics(ParameterReference parameterReference) throws NoSuchParameterException {
		return this.getParameterStatistics(this.getRetriever().resolveReference(parameterReference));
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("# Events Inside: ");
		builder.append(getN());
		builder.append(" (");
		builder.append(getPercentOfParent());
		builder.append("%)\n");
		for (PopulationParameterStatistics paramStat : getAllParameterStatistics()) {
			builder.append(paramStat.toString());
		}
		return builder.toString();
	}
}
