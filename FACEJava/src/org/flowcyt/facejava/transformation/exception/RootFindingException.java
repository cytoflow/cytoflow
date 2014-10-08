package org.flowcyt.facejava.transformation.exception;

import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;

/**
 * <p>
 * Thrown if there was an error finding the root of a transformation function.
 * 
 * @author echng
 */
public class RootFindingException extends DataRetrievalException {
	private static final long serialVersionUID = -2584163756229146416L;
	
	public RootFindingException(String message) {
		super(message);
	}
	
	public RootFindingException(String message, Throwable cause) {
		super(message, cause);
	}
}
