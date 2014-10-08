package org.flowcyt.facejava.gating.gates.bool;

import java.util.Collections;
import java.util.List;

import org.flowcyt.facejava.gating.gates.Gate;

/**
 * <p>
 * Abstract super-class for a boolean operation which operates on n-ary (more than one)
 * operands.
 * 
 * @author echng
 */
public abstract class NAryOperator implements BooleanGateOperator {
	
	/**
	 * Contains the operands of the operator.
	 */
	private List<Gate> operands;
	
	/**
	 * Constructor.
	 * 
	 * @param operands The Gates operands
	 */
	public NAryOperator(List<Gate> operands) {
		this.operands = operands;
	}
	
	public List<Gate> getOperands() {
		return Collections.unmodifiableList(operands);
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("Operands:");
		builder.append("\n---\n");
		for (Gate operand : operands) {
			builder.append("* ");
			builder.append(operand.toString());
			builder.append("\n");
		}
		builder.append("\n---");
		return builder.toString();
	}
	
}
