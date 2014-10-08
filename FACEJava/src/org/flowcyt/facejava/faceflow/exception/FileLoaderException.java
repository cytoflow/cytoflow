package org.flowcyt.facejava.faceflow.exception;

/**
 * <p>
 * Thrown by FileLoaders when they encounter Exceptions when loading files. This
 * exception wraps the Exception that caused the error. The purpose of having the
 * class is to avoid having FileLoader be a brittle supertype, particularly when a new
 * type of Exception is thrown when loading one of the files and the interfaces of all
 * FileLoaders would have to be update, without this wrapper Exception class 
 * 
 * @author echng
 */
public class FileLoaderException extends Exception {
	private static final long serialVersionUID = 5718611455296991377L;

	/**
	 * Constructor. This Exception always wraps the real cause of the error.
	 * 
	 * @param cause The Exception that caused the error.
	 */
	public FileLoaderException(Exception cause) {
		super(cause.getMessage(), cause);
	}
	
	public void printStackTrace() {
		super.printStackTrace();
		Throwable cause = this.getCause();
		while (cause != null) {
			cause.printStackTrace();
			cause = cause.getCause();
		}
	}
}
