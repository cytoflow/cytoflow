package org.flowcyt.facejava.fcsdata.exception;

/**
 * <p>
 * Thrown when there is some error when data are being retrieved from events.
 * Should be extended for any specific error type. 
 * 
 * @author echng
 */
public class DataRetrievalException extends Exception {
	
	private static final long serialVersionUID = 1653741976822648628L;
	
	public DataRetrievalException() {
		super();
	}
	
	public DataRetrievalException(String message) {
		super(message);
	}
	
	public DataRetrievalException(Throwable cause) {
		super(cause);
	}
	
	public DataRetrievalException(String message, Throwable cause) {
		super(message + cause.toString(), cause);
	}
}
