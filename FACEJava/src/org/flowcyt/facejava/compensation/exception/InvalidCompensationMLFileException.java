package org.flowcyt.facejava.compensation.exception;

/**
 * <p>
 * Thrown if a CompensationML file does not validate against the schema.
 * 
 * @author echng
 */
public class InvalidCompensationMLFileException extends Exception {
	
	private static final long serialVersionUID = 3190083426691039430L;

	public InvalidCompensationMLFileException() {
		super();
	}
	
	public InvalidCompensationMLFileException(String message) {
		super(message);
	}
}
