package org.flowcyt.facejava.transformation.function;

import org.apache.commons.math.FunctionEvaluationException;
import org.apache.commons.math.analysis.UnivariateRealFunction;

/**
 * <p>
 * The function whose root needs to be found for Hyperlog Transformations.
 * The function is defined as 
 *    
 * <p>
 * EH(y; b, d, r) - parameterValue where
 *  
 * <pre> 
 * EH(y; b, d, r) = { 10 ^ (y * d / r) + b * (d / r) * y - 1        if y >= 0   
 *                  { -(10 ^ (-y * d / r)) + b * (d / r) * y + 1    otherwise
 * </pre>
 * 
 * <p>
 * The constants b, d, and r are specified at the time of construction, while
 * parameterValue is specified later since it changes for each event. Thus, this object
 * actually specifies a *family* of functions -- one for each different value of
 * parameterValue. Therefore, before performing the root finding, parameterValue must
 * be set to specify which of the functions in the family should be solved.
 * 
 * @author echng
 */
public class HyperlogFunction implements UnivariateRealFunction {
	private double b;
	
	private double dDivR;
	
	private double parameterValue;
	
	/**
	 * Constructor. 
	 * @param b See class documentation.
	 * @param d See class documentation.
	 * @param r See class documentation.
	 */
	public HyperlogFunction(double b, double d, double r) {
		this.b = b;
		this.dDivR = d / r;
	}
	
	/**
	 * Sets the parameterValue. That is, it specifies which of the functions in the 
	 * family should be solved when performing the root finding.
	 *  
	 * @param param The parameterValue.
	 */
	 public void setParameterValue(double param) {
		this.parameterValue = param;
	}
	
	public double value(double y) throws FunctionEvaluationException {
		if (y >= 0)
			return Math.pow(10, y * dDivR) + b * dDivR * y - 1 - parameterValue;
		return -Math.pow(10, -y * dDivR) + b * dDivR * y + 1 - parameterValue;
	}
}
