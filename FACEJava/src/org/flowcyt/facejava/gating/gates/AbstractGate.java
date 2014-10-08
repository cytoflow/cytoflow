package org.flowcyt.facejava.gating.gates;

import java.util.ArrayList;
import java.util.List;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;

/**
 * <p>
 * Abstract superclass for all Gates. Implements some basic functionality (mostly handling 
 * IDs).
 *  
 * @author echng
 */
public abstract class AbstractGate implements Gate {
	/**
	 * The id of the gate. Must be unique among all gates. 
	 */
	private String id;
	
	/**
	 * @param gateId The gate's id.
	 */
	public AbstractGate(String gateId) {
		this.id = gateId;
	}
	
	public GateSubPopulation isInside(Population population) throws DataRetrievalException {
		return this.isInside(population, population.getRetriever());	
	}
	
	/**
	 * <p>
	 * Implementors should override this method if optimisation is possible when sets of
	 * events are given instead of only one event (e.g., Polytope Gates).
	 * 
	 * <p>
	 * By default, this method will iterate through the Events in the given Population can call
	 * Gate.isInside(Event, DataRetriver) on each one. Events are computed in the order given
	 * by the Population so relative order is maintained.
	 */
	public GateSubPopulation isInside(Population population, DataRetriever retriever) throws DataRetrievalException {
		List<Event> insideEvents = new ArrayList<Event>();
		for (Event ev : population) {
			if (this.isInside(ev, retriever))
				insideEvents.add(ev);
		}
		return new GateSubPopulation(population, retriever, this, insideEvents);		
	}
	
	public String getId() {
		return id;
	}
	
	public boolean equals(Object o) {
		return o instanceof Gate && id.equals(((Gate)o).getId());
	}
	
	public int hashCode() {
		return id.hashCode();
	}
	
	public String toString() {
		return "Gate \"" + id + "\""; 
	}
}
