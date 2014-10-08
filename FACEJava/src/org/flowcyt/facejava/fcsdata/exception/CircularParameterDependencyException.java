package org.flowcyt.facejava.fcsdata.exception;

import java.util.List;

import org.flowcyt.facejava.fcsdata.Parameter;

/**
 * <p>
 * Thrown if the Parameters used during Analysis are found to have circular dependencies. That is, 
 * at least one directly or indirectly depends on itself (uses its own data value to return a data value
 * to the caller).
 * 
 * @author echng
 */
public class CircularParameterDependencyException extends Exception {
	
	private static final long serialVersionUID = 5987554754739101228L;
	
	private List<Parameter> cycle;	
	
	public CircularParameterDependencyException(List<Parameter> cycle) {
		this.cycle = cycle;
	}
	
	public String getMessage() {
		StringBuilder builder = new StringBuilder();
		builder.append("Parameter Dependency Cycle: ");
		boolean first = true;
		for (Parameter param : cycle) {
			builder.append("[");
			builder.append(param.toString());
			builder.append("]");
			if (!first)
				builder.append(" -> ");
			else
				first = false;
		}
		return builder.toString();
	}
}
