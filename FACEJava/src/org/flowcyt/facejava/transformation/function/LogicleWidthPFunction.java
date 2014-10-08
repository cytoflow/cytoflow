package org.flowcyt.facejava.transformation.function;

import org.apache.commons.math.FunctionEvaluationException;
import org.apache.commons.math.analysis.UnivariateRealFunction;

/**
 * <p>
 * The function to calculate the p constant in the Logicle function. Given w, p is 
 * defined as w = 2 * ln(p) / (p + 1). Thus we want to find the root of
 *   
 * <p>
 * 2 * ln(p) / (p + 1) - w 
 * 
 * <p>
 * That is, p such that the function = 0. This object represents this function.  
 * 
 * @author echng
 *
 */
public class LogicleWidthPFunction implements UnivariateRealFunction {
	private double w;
	
	/**
	 * Constructor.
	 * @param w See class documentation.
	 */
	public LogicleWidthPFunction(double w) {
		this.w = w;
	}

	public double value(double p) throws FunctionEvaluationException {
		return 2 * p * Math.log(p) / (p + 1) - w;
	}
}
