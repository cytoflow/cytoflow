package org.flowcyt.facejava.gating.gates.geometric;

import java.util.ArrayList;
import java.util.List;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.gates.GateSubPopulation;

/**
 * <p>
 * PolytopeGate will use different implementations to perform the actual event
 * testing because performance gains can be realized by doing so (over just using the
 * n-dimension tester for everything). See the different implementations of
 * PolytopeGateTester for details of how they compute inside-ness.
 *
 * @author echng
 */
abstract class PolytopeGateTester {
	/**
	 * The PolytopeGate the tester is for.
	 */
	protected PolytopeGate gate;
	
	/**
	 * Constructor. Creates a tester for the given Gate.
	 * 
	 * @param gate The PolytopeGate the tester is for.
	 */
	public PolytopeGateTester(PolytopeGate gate) {
		this.gate = gate;
	}
	
	/**
	 * Default to testing each event separately. Same implementation as in AbstractGate.
	 * We need this implementation  so that PolytopeGate can override all calls to
	 * the Gate version of this method to its PolytopeGateTester. Otherwise, it would
	 * have to check the number of dimensions rather than relying on polymorphism.
	 * 
	 * @param population The Population of Events to gate on.
	 * @param retriever The DataRetriever to use to grab data from the Event and resolve
	 * ParameterReferences.
	 * @return Returns the subset of Events in population that are inside the Gate as a
	 * GateSubPopulation. Gates should *try* to preserve the relative order that the events are in
	 * the Population gated upon, but it is not guaranteed.
	 * @throws DataRetrievalException Thrown if there was an error retrieving a
	 * datum from the given event for testing against this Gate. Check the
	 * exception's concrete type to see the specific cause.
	  */
	public GateSubPopulation isInside(Population population, DataRetriever retriever) throws DataRetrievalException {
		List<Event> insideEvents = new ArrayList<Event>();
		for (Event ev : population) {
			if (this.isInside(ev, retriever))
				insideEvents.add(ev);
		}
		return new GateSubPopulation(population, retriever, gate, insideEvents);
	}
	
	/**
	 * Determines if the given event is inside the Gate. (when the data are 
	 * retrieved using the given DataRetriever). Check sub-classes for the
	 * semantics of "inside" for each gate type.
	 * 
	 * @param ev The event to check
	 * @param retriever The DataRetriever to use to grab data from the Event.
	 * @return Returns true if the event is inside the gate, false otherwise.
	 * @throws DataRetrievalException Thrown if there was an error retrieving a
	 * datum from the given event for testing against this Gate. Check the
	 * exception's concrete type to see the specific cause.
	 */
	public abstract boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException;

}
