package org.flowcyt.facejava.gating.analysis;

/**
 * <p>
 * Represents an error that happened during analysis. Wraps the exception that caused it.
 * 
 * @author echng
 */
public class AnalysisError {
	
	/**
	 * The exception that caused the error.
	 */
	private Exception cause;
	
	/**
	 * Constructor.
	 * 
	 * @param cause The exception which caused the error.
	 */
	public AnalysisError(Exception cause) {
		this.cause = cause;
	}
	
	/**
	 * @return Returns the wrapped exception.
	 */
	public Exception getCause() {
		return cause;
	}
	
	/**
	 * @return Returns a String explaining why this error was caused.
	 */
	public String toString() {
		return cause.getMessage();
	}
}
