package org.flowcyt.facejava.gating.gates.bool;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.gates.Gate;

/**
 * <p>
 * Implements the boolean Not operation. That is, the operator is true iff the Event is 
 * not inside the operand Gate.
 * 
 * @author echng
 */
public class NotOperator extends UnaryOperator {
	
	/**
	 * Creates a Not Operator.
	 * 
	 * @param operand The Gate operand.
	 */
	public NotOperator(Gate operand) {
		super(operand);
	}

	/**
	 * The operator is true iff the Event is not inside the operand Gate.
	 */
	public boolean isTrue(Event ev, DataRetriever retriever) throws DataRetrievalException {
		return !operand.isInside(ev, retriever);
	}

	public String toString() {
		return "Operator: Not\n" + super.toString(); 
	}
}
