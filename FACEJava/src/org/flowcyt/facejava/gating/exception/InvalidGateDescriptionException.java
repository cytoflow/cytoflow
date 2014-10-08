package org.flowcyt.facejava.gating.exception;

/**
 * <p>
 * Thrown when a gate is invalid with respect to the schema or specification.
 * It is mainly used when there are semantics about a gate that are not met. That is,
 * validity rules that cannot be captured in the schema. 
 * 
 * @author echng
 */
public class InvalidGateDescriptionException extends InvalidGatingMLFileException {
	private static final long serialVersionUID = -8646476589546597114L;

	public InvalidGateDescriptionException(String id, String reason) {
		super("Gate " + id + " - " + reason);
	}
}
