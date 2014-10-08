package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * Applies a Linear Transformation to a Parameter value. The transformation applied is:
 * 
 * <p>
 * a * parameterValue + b
 * 
 * @author echng
 */
public class LinearTransformation extends SingleParameterTransformation {
	private double a;
	
	private double b;
	
	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 * @param parameterReference A reference to the parameter it transforms. 
	 * @param a See class documentation.
	 * @param b See class documentation.
	 */
	public LinearTransformation(String name, ParameterReference parameterReference, double a, double b) {
		super(name, parameterReference);
		this.a = a;
		this.b = b;
	}
	
	protected double applyTransformation(double parameterValue) {
		return a * parameterValue + b;
	}

	public String toString() {
		return "Linear " + super.toString();
	}
}
