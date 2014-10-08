package org.flowcyt.facejava.fcsdata;

import java.util.AbstractList;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.statistics.PopulationStatistics;

/**
 * <p>
 * An abstract base class for Populations where the order of Events in the Population
 * matters. This class provides implementations for get(int) and size(), the minimum
 * needed for subclasses of AbstractList (and it does not override any other methods in 
 * AbstractList). Thus, it is, by default, an unmodifiable list (i.e., any set(),
 * add(), or remove() operations throw exceptions). Modifiable Populations should
 * override those methods. Note that if the Events are modified, the PopulationStatistics
 * will need to be updated as well.
 * 
 * <p>
 * Subclasses need to only provide an implementation for getRetriever().
 * 
 * @author echng
 */
public abstract class AbstractOrderedPopulation extends AbstractList<Event> implements Population {
	/**
	 * The Parent Population.
	 */
	private Population parent;
	
	/**
	 * The list of events (order corresponds to list order).
	 */
	protected List<Event> events;
	
	/**
	 * Statistics about the Population.
	 */
	protected PopulationStatistics stats;
	
	/**
	 * Constructor. Creates an empty Population with no parent.
	 */
	public AbstractOrderedPopulation() {
		this.parent = null;
		this.events = new ArrayList<Event>();
	}
	
	/**
	 * Constructor. Creates an empty Population with the given Parent.
	 * 
	 * @param parentPopulation The Parent of this Population.
	 */
	public AbstractOrderedPopulation(Population parentPopulation) {
		this();
		this.parent = parentPopulation;
	}
	
	/**
	 * Constructor. Creates a Population containing the Events in the given Collection
	 * with the given parent Population.
	 * 
	 * @param parentPopulation The parent of this Population.
	 * @param coll A Collection containing the Events that this Population will contain
	 */
	public AbstractOrderedPopulation(Population parentPopulation, Collection<? extends Event> coll) {
		this(parentPopulation);
		for (Event ev : coll) {
			events.add(ev);
		}
	}
	
	@Override public Event get(int index) {
		return events.get(index);
	}

	@Override public int size() {
		return events.size();
	}

	public Population getParentPopulation() {
		return parent;
	}

	/**
	 * Stats are calculated upon first call to this method.
	 */
	public PopulationStatistics getStatistics() throws DataRetrievalException {
		if (stats == null) {
			stats = new PopulationStatistics(this);
		}
		return stats;
	}
}
