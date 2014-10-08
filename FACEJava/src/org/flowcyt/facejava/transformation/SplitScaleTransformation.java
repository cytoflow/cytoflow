package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * Applies a Split-Scale Transformation to a Parameter value. The transformation applied is:
 * 
 * <pre>
 * a * parameterValue + b        if parameter < t
 * log(c * parameter) * r / d    otherwise
 * </pre>
 * 
 * <p>
 * where log() is in base 10.
 *  
 * <p>
 * Given transitionChannel, maxChannel and maxValue, the constants a, b, c, d, r and t
 * are calculated as follows:
 * 
 * <ul>
 * <li>b = transitionChannel / 2
 * <li>r = maxChannel - transitionChannel
 * <li>d = 2 * log(e) * r / transitionChannel
 * <li>log(t) = -2 * log (e) * r / transitionchannel + log(maxValue)
 *    <ul>
 *    <li>then t = 10 ^ log(t)
 *    </ul>
 * </li>
 * <li>a = transitionChannel / (2 * t)
 * <li>log(ct) = (a * t + b) * d / r
 *     <ul>
 *     <li>then c = (10 ^ log(ct)) / t
 *     </ul>
 * </li>
 * </ul>
 * 
 * <p>
 * where all log()s are in base 10.
 * 
 * @author echng
 */
public class SplitScaleTransformation extends SingleParameterTransformation {
	
	private static final double TWO_LOG_E = 2 * Math.log10(Math.E);
	
	private static final double E_SQUARED = Math.pow(Math.E, 2);
	
	private double a;
	
	private double b;
	
	private double c;
	
	private double rDivD;
	
	private double t;
	
	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 * @param parameterReference A reference to the parameter it transforms.
	 * @param r See class documentation.
	 * @param maxValue See class documentation.
	 * @param transitionChannel See class documentation.
	 */
	public SplitScaleTransformation(String name, ParameterReference parameterReference, double r, double maxValue, double transitionChannel) {
		super(name, parameterReference);
		
		this.b = transitionChannel / 2;
		
		double d = TWO_LOG_E * r / transitionChannel;
		
		// simplify r/d.
		this.rDivD = transitionChannel / TWO_LOG_E;
			
		this.t = Math.pow(10, -d + Math.log10(maxValue));
		
		this.a = transitionChannel / (2 * this.t);
		
		// Simplifying the equation for log(ct) yields 2 * log(e) = log(e^2)
		this.c = E_SQUARED / this.t;
	}

	protected double applyTransformation(double parameterValue) {
		if (parameterValue <= t)
			return a * parameterValue + b;
		return Math.log10(c * parameterValue) * rDivD;
	}

	public String toString() {
		return "Split Scale " + super.toString();
	}
}
