package org.flowcyt.facejava.transformation.function;

import org.apache.commons.math.FunctionEvaluationException;
import org.apache.commons.math.analysis.UnivariateRealFunction;

/**
 * <p>
 * The function whose root needs to be found for Biexponential Transformations.
 * The function is defined as 
 *    
 * <p>
 * B(y; a, b, c, d, f) - parameterValue, where 
 *      
 * <pre>
 * B(y; a, b, c, d, f) = a * e ^ (b * y) - c * e^(-d * y) + f.
 * </pre>
 * 
 * <p>
 * The constants a, b, c, d, and f are specified at the time of construction, while
 * parameterValue is specified later since it changes for each event. Thus, this object
 * actually specifies a *family* of functions -- one for each different value of
 * parameterValue. Therefore, before performing the root finding, parameterValue must
 * be set to specify which of the functions in the family should be solved.
 * 
 * @author echng
 */
public class BiexponentialFunction implements UnivariateRealFunction {
	private double a;

	private double b;
	
	private double c;
	
	private double d;
	
	private double f;
	
	private double parameterValue;

	/**
	 * Constructor.
	 * @param a See class documentation.
	 * @param b See class documentation.
	 * @param c See class documentation.
	 * @param d See class documentation.
	 * @param f See class documentation.
	 */
	public BiexponentialFunction(double a, double b, double c, double d, double f) {
		this.a = a;
		this.b = b;
		this.c = c;
		this.d = d;
		this.f = f;
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
		return a * Math.exp(b * y) - c * Math.exp(-d * y) + f - parameterValue;
	}
}
