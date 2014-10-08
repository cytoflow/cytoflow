package org.flowcyt.facejava.fcsdata.exception;

/**
 * <p>
 * Thrown when the CFCSDataSetType is not List Mode. We don't deal with any other
 * type of data.
 * 
 * @author echng
 */
public class InvalidCFCSDataSetTypeException extends Exception {
	private static final long serialVersionUID = 8927235137252034415L;
	
	public InvalidCFCSDataSetTypeException() {
		super("Data Type not List Mode");
	}	
}
