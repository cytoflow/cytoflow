package org.flowcyt.facejava.gating.gates.bool;

import java.util.List;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.gates.Gate;

/**
 * <p>
 * Implements the Or boolean operation. That is, the operator is true iff at least one of
 * its operand Gates have the given Event inside it.
 * 
 * @author echng
 */
public class OrOperator extends NAryOperator {

	/**
	 * Creates an Or Operator.
	 * @param operands The Gate operands
	 */
	public OrOperator(List<Gate> operands) {
		super(operands);
	}

	/**
	 * The operator is true iff at least one of its operand Gates have the given
	 * Event inside it.
	 */
	public boolean isTrue(Event ev, DataRetriever retriever) throws DataRetrievalException {
		for (Gate g : this.getOperands()) {
			if (g.isInside(ev, retriever))
				return true;
		}
		return false;
	}

	public String toString() {
		return "Operator: Or\n" + super.toString(); 
	}
}
