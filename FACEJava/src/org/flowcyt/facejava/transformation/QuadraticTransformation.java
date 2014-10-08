package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * Applies a Quadratic Transformation to a Parameter value. The transformation applied is:
 * 
 * <p>
 * a * parameterValue ^ 2 + b * parameterValue + c
 *
 * @author echng
 */
public class QuadraticTransformation extends SingleParameterTransformation {
	
	private double a;
	
	private double b;
	
	private double c;
	
	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 * @param parameterReference A reference to the parameter it transforms. 
	 * @param a See class documentation.
	 * @param b See class documentation.
	 * @param c See class documentation.
	 */
	public QuadraticTransformation(String name, ParameterReference parameterReference, double a, double b, double c) {
		super(name, parameterReference);
		this.a = a;
		this.b = b;
		this.c = c;
	}
	
	protected double applyTransformation(double parameterValue) {
		return a * Math.pow(parameterValue, 2) + b * parameterValue + c;
	}
	
	public String toString() {
		return "Quadratic " + super.toString();
	}	
}
