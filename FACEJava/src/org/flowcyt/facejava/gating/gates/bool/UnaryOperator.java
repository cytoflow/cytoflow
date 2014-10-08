package org.flowcyt.facejava.gating.gates.bool;

import java.util.Collections;
import java.util.List;

import org.flowcyt.facejava.gating.gates.Gate;

/**
 * <p>
 * An abstract super-class for unary boolean operations.
 *  
 * @author echng
 */
public abstract class UnaryOperator implements BooleanGateOperator {

	/**
	 * The Gate operand. 
	 */
	protected Gate operand;
	
	/**
	 * Constructor.
	 * 
	 * @param operand The Gate operand.
	 */
	public UnaryOperator(Gate operand) {
		this.operand = operand;
	}
		
	public List<Gate> getOperands() {
		return Collections.singletonList(operand);
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("Operand:");
		builder.append("\n---\n");
		builder.append("* ");
		builder.append(operand.toString());
		builder.append("\n");
		builder.append("\n---");
		return builder.toString();
	}
}
