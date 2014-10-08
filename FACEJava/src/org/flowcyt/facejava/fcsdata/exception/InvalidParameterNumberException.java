package org.flowcyt.facejava.fcsdata.exception;

import org.flowcyt.facejava.fcsdata.impl.FcsParameterList;

/**
 * <p>
 * Thrown when a FcsParameter with an invalid Parameter Number is added to a
 * FcsParameterList. A ParameterNumber is invalid if it does not one more than
 * its position in the list.
 * 
 * @author echng
 */
public class InvalidParameterNumberException extends Exception {
	
	private static final long serialVersionUID = -4547082123941080278L;

	private FcsParameterList paramList;
	
	private int parameterNumber;
	
	public InvalidParameterNumberException(FcsParameterList paramList, int parameterNumber) {
		super("Duplicate Parameter Number: " + parameterNumber);
		this.paramList = paramList;
		this.parameterNumber = parameterNumber;
	}

	public FcsParameterList getDataSet() {
		return paramList;
	}

	public int getParameterNumber() {
		return parameterNumber;
	}
}
