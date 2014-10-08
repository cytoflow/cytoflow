package org.flowcyt.facejava.transformation.exception;

/**
 * <p>
 * Thrown if there was an error loading a transformation in a Gating XML file.
 * 
 * @author echng
 */
public class InvalidTransformationException extends InvalidTransformationMLFileException {

	private static final long serialVersionUID = -256265569879824094L;
	
	public InvalidTransformationException(String message) {
		super(message);
	}
	
	public InvalidTransformationException(String transformationName, String reason) {
		super("Bad Transformation: " + transformationName + " -- " + reason);
	}

}
