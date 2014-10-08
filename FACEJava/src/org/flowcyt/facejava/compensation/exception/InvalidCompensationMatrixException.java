package org.flowcyt.facejava.compensation.exception;

/**
 * <p>
 * Thrown if a valid compensation matrix could not be calculated to be used to
 * calculate a FcsDataSet (e.g., it was non-invertible). 
 * 
 * @author echng
 */
public class InvalidCompensationMatrixException extends Exception {
	private static final long serialVersionUID = -628930354405164307L;

	public InvalidCompensationMatrixException(String message) {
		super(message);
	}
	
	public InvalidCompensationMatrixException(Exception cause) {
		super(cause);
	}
	
	public InvalidCompensationMatrixException(String message, Exception cause) {
		super(message + cause.toString(), cause);
	}
}
