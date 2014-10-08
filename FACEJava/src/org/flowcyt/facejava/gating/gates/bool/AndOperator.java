package org.flowcyt.facejava.gating.gates.bool;

import java.util.List;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.gates.Gate;

/**
 * <p>
 * Implements the boolean And operation. That is, the operator is true iff all its operand
 * Gates have the Event inside it.
 * 
 * @author echng
 */
public class AndOperator extends NAryOperator {
	
	/**
	 * Creates an And Operator.
	 * @param operands The Gate operands
	 */
	public AndOperator(List<Gate> operands) {
		super(operands);
	}

	/**
	 * The operator is true iff all its operand Gates have the Event inside it.
	 */
	public boolean isTrue(Event ev, DataRetriever retriever) throws DataRetrievalException {
		for (Gate g : this.getOperands()) {
			if (!g.isInside(ev, retriever))
				return false;
		}
		return true;
	}
	
	public String toString() {
		return "Operator: And\n" + super.toString(); 
	}
}
