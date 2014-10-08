package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * Applies a Ln Transformation to a Parameter value. The transformation applied is:
 * 
 * <pre>
 * ln(parameterValue) * r / d    if parameterValue >= 1
 * 0                             otherwise
 * </pre>
 *     
 * <p>
 * where ln() is the natural logarithm.
 *     
 * @author echng
 */
public class LnTransformation extends SingleParameterTransformation {
	/**
	 * Save r / d  instead of separately since it is constant for all applications of
	 * this transformation.
	 */
	private double rDivD;
	
	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 * @param parameterReference A reference to the parameter it transforms. 
	 * @param r See class documentation.
	 * @param d See class documentation.
	 */
	public LnTransformation(String name, ParameterReference parameterReference, double r, double d) {
		super(name, parameterReference);
		this.rDivD = r/d;
	}
	
	protected double applyTransformation(double parameterValue) {
		if (parameterValue < 1)
			return 0;
		return Math.log(parameterValue) * rDivD;
	}
	
	public String toString() {
		return "Ln " + super.toString();
	}
}
