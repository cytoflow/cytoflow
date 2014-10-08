package org.flowcyt.facejava.gating.exception;

import java.lang.Exception;;

/**
 * <p>
 * Thrown when the XML Gating file is invalid with respect to the schema.
 * 
 * @author sli
 */
public class InvalidGatingMLFileException extends Exception {
	private static final long serialVersionUID = 8071527661460307273L;

	public InvalidGatingMLFileException() {
		super();
	}

	public InvalidGatingMLFileException(String msg) {
		super(msg);
	}
}
