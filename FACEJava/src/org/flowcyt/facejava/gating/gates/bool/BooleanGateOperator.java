package org.flowcyt.facejava.gating.gates.bool;

import java.util.List;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.gates.Gate;

/**
 * <p>
 * Represents the boolean operation that is performed by a BooleanGate on its Gates.
 * BooleanGateOperators are only visible to BooleanGates. 
 * 
 * @author echng
 */
public interface BooleanGateOperator {
	/**
	 * Determines if the boolean operation when performed on its operands is true.
	 * 
	 * @param ev The Event to use in the boolean operation
	 * @param retriever The DataRetriever to use to retrieve data from the
	 * Event. 
	 * @return Returns true if the boolean operation carried out is true given the
	 * event and its operand Gates
	 * @throws DataRetrievalException Thrown if there was an error retrieving a
	 * datum from the given event for testing against one of the operator's Gate
	 * operands. Check the exception's concrete type to see the specific cause.
	 */
	public boolean isTrue(Event ev, DataRetriever retriever) throws DataRetrievalException;
	
	/**
	 * @return Returns a list containing all the operand Gates involved in the operation.
	 * Note that the list is complete only after resolveRefernces() has been called. Before
	 * resolveReferences(), it will only contain the Gates that were defined within the
	 * BooleanGate. 
	 */
	public List<Gate> getOperands();
}