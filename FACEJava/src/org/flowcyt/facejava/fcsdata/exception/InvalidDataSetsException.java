package org.flowcyt.facejava.fcsdata.exception;

import java.util.Map;

/**
 * <p>
 * Thrown if at least one data set in an FCS data file is bad. Use getReasons() to find
 * out the reasons why. This exception wraps exceptions thrown when reading a data
 * set so that the other data sets in a data file will still be read. 
 * 
 * @author echng
 */
public class InvalidDataSetsException extends Exception {
	
	private static final long serialVersionUID = 3858774424121734424L;

	private Map<Integer, Exception> reasons;
	
	/**
	 * Constructor.
	 * @param reasons A Map of Data Set number (starts from 1) to the Exception that
	 * caused the error when loading.. 
	 */
	public InvalidDataSetsException(Map<Integer, Exception> reasons) { 
		this.reasons = reasons;
	}
	
	/**
	 * @return Returns the reasons map.
	 */
	public Map<Integer, Exception> getReasons() {
		return reasons;
	}
	
	public String getMessage() {
		StringBuilder builder = new StringBuilder();
		for (Map.Entry<Integer, Exception> entry : reasons.entrySet()) {
			builder.append("Invalid DataSet #" + entry.getKey() + " -- " + entry.getValue());
		}
		return builder.toString();
	}
	
}
