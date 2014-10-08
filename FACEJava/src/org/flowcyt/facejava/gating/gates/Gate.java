package org.flowcyt.facejava.gating.gates;

import java.util.Set;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;

/**
 * <p>
 * Gates represent a subsetting operation on the event data from an FCS file. Events that
 * are inside the Gate are considered to be in the resultant subset. How "inside" is
 * determined is up to each Gate.
 * 
 * <p>
 * The Gate interface must be implemented by all Gates. Implementors should inherit from
 * one of the abstract classes that implement Gate.
 * 
 * <p>
 * A Gate is equal to another Gate if their ids are the same, since ids must be unique
 * (wrt some GateSet).
 * 
 * @author echng
 */
public interface Gate {
	/**
	 * @return Returns the gate's id. Note that tds must be unique within a GateSet
	 * (since equal ids mean equal gates).
	 */
	public String getId();
	
	/**
	 * <p>
	 * Determines which of the given events are inside the gate. The Population's default
	 * DataRetriever will be used to resolve ParameterReferences and retrieve event data.
	 * Check sub-classes for the semantics of "inside" for each gate type.
	 * 
	 * <p>
	 * This is a convenience method for gate.isInside(population, population.getRetriever()).
	 * 
	 * @param population The Population of Events to gate on. The Population's default
	 * DataRetriever will be used to resolve ParameterReferences and retrieve event data.
	 * @return Returns the subset of Events in population that are inside the Gate as a
	 * GateSubPopulation. Gates should *try* to preserve the relative order that the events are in
	 * the Population gated upon, but it is not guaranteed.
	 * @throws DataRetrievalException Thrown if there was an error retrieving a
	 * datum from the given event for testing against this Gate. Check the
	 * exception's concrete type to see the specific cause.
	 */
	public GateSubPopulation isInside(Population population) throws DataRetrievalException;
	
	/**
	 * <p>
	 * Determines which of the given events are inside the gate. The given DataRetriever
	 * will be used to resolve ParameterReferences and retrieve event data. Check sub-classes
	 * for the semantics of "inside" for each gate type.
	 * 
	 * <p>
	 * This is the method that should be used by clients as concrete Gate types may be able
	 * to implement some sort of optimisation when given Sets of Events that is not possible
	 * to implement when given one event at a time.
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
	public GateSubPopulation isInside(Population population, DataRetriever retriever) throws DataRetrievalException;
	
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
	public boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException;
	
	/**
	 * Validates the Gate. Gate's should provide implementations for this method
	 * which check to see that the Gate meets the requirements for a valid Gate of
	 * its type as defined in the standard. If fails to meeat a requirement, an
	 * InvalidGateDescriptionException must be thrown explaining why. Otherwise,
	 * the method simply returns.
	 * 
	 * validate() should be called as soon as validity can be correctly determined.
	 * For most gates, this is during construction. But for some, e.g., BooleanGates,
	 * it must happen later. isInside() should not be called until validity is
	 * determined.
	 * 
	 * @throws InvalidGateDescriptionException Thrown if the Gate does not meet
	 * a requirement as defined in the specification for it to be valid.
	 */
	public void validate() throws InvalidGateDescriptionException;
	
	/**
	 * Returns the set of other Gates that this Gate directly depends on (i.e., this gate
	 * uses the value of isInside() of the other gates to determine its own isInside()
	 * value). Indirect dependencies (the dependecies of the Gates that this Gate depends
	 * on (and so on)) can be obtained by calling this method on the returned Gates.  
	 *  
	 * @return Returns the Set of Gates this gate depends on.
	 */
	public Set<Gate> getDirectDependencies();
}
