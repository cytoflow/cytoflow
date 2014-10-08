package org.flowcyt.facejava.transformation.function;

import org.apache.commons.math.FunctionEvaluationException;
import org.apache.commons.math.analysis.UnivariateRealFunction;
import org.flowcyt.facejava.transformation.exception.RootFindingException;

/**
 * <p>
 * The function whose root needs to be found for Logicle Transformations.
 * The function is defined as 
 *    
 * <p>
 * S(y; T, w, m) - parameterValue where
 * 
 * <pre>
 * S(y; T, w, m) = { T * e ^ -(m - w) * (e ^ (y - w) - p ^ 2 * e ^ (-(y - w)/p) + p^2 - 1    if y >=w
 *                 { -(T * e ^ -(m - w) * (e ^ (w - y) - p ^ 2 * e ^ (-(w - y)/p) + p^2 - 1) otherwise
 * </pre>
 * 
 * <p>
 * p is defined as w = 2 * ln(p) / (p + 1)
 * 
 * <p>
 * The constants T, w (and thus, p), and m are specified at the time of construction, while
 * parameterValue is specified later since it changes for each event. Thus, this object
 * actually specifies a *family* of functions -- one for each different value of
 * parameterValue. Therefore, before performing the root finding, parameterValue must
 * be set to specify which of the functions in the family should be solved.
 * 
 * @author echng
 *
 */
public class LogicleFunction implements UnivariateRealFunction {
	private double t;
	
	private double w;
	
	private double p;
	
	private double m;
	
	private double parameterValue;
	
	/**
	 * Constructor.
	 * @param t See class documentation.
	 * @param w See class documentation.
	 * @param m See class documentation.
	 * @throws RootFindingException Thrown if p couldn't be calculated.
	 */
	public LogicleFunction(double t, double w, double m) throws RootFindingException {
		this.t = t;
		this.w = w;
		this.m = m;
		
		LogicleWidthPFunction pFunc = new LogicleWidthPFunction(w);
		this.p = FunctionUtils.findRoot(pFunc, 1, 1024);
	}

	/**
	 * Sets the parameterValue. That is, it specifies which of the functions in the 
	 * family should be solved when performing the root finding.
	 *  
	 * @param parameter The parameterValue.
	 */
	public void setParameterValue(double parameter) {
		this.parameterValue = parameter;
	}

	public double value(double y) throws FunctionEvaluationException {
		if (y >= w )
			return calculateS(y - w) - parameterValue;
		return -calculateS(w - y) - parameterValue;
	}
	
	/**
	 * Implements the S function for y >= w.
	 * 
	 * @param y The function argument.
	 * @return The function value for the given argument.
	 */
	private double calculateS(double exponent) {
		return t * Math.exp(-(m - w)) * 
				(Math.exp(exponent) - Math.pow(p, 2) * Math.exp(-(exponent) / p) +  Math.pow(p, 2) - 1);
	}
}
