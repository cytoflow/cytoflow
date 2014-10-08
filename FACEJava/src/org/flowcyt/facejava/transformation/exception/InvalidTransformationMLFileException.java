package org.flowcyt.facejava.transformation.exception;

/**
 * <p>
 * Thrown when a TransformationML file does not validate against the schema.
 * 
 * @author echng
 */
public class InvalidTransformationMLFileException extends Exception {
	
	private static final long serialVersionUID = -2986388374604014082L;
	
	public InvalidTransformationMLFileException() {
		super();
	}
	
	public InvalidTransformationMLFileException(String message) {
		super(message);
	}
}
