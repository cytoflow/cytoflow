package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * Applies a Log Transformation to a Parameter value. The transformation applied is:
 * 
 * <pre>
 * log(parameterValue) * r / d    if parameterValue >= 1
 * 0                              otherwise
 * </pre>
 * 
 * <p>
 * where log() is in base logbase.
 * 
 * @author echng
 */
public class LogTransformation extends SingleParameterTransformation {
	/**
	 * Since log(x) in base b = log(x) / log(b) in any base, we can save the constant
	 * multiplier rather than each of the components. 
	 * i.e., multiplier = r / (d * log(logbase)). The (arbitrary) base used for the
	 * conversion is e. 
	 */
	private double multiplier;
	
	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 * @param parameterReference A reference to the parameter it transforms. 
	 * @param r See class documentation.
	 * @param d See class documentation.
	 * @param logbase See class documentation.
	 */
	public LogTransformation(String name, ParameterReference parameterReference, double r, double d, double logbase) {
		super(name, parameterReference);
		// log (x) in base b = (log x)/(log b)	
		this.multiplier = r / (d * Math.log(logbase));
	}

	protected double applyTransformation(double parameterValue) {
		if (parameterValue < 1)
			return 0;
		return Math.log(parameterValue) * multiplier;
	}

	public String toString() {
		return "Log " + super.toString();
	}
}
