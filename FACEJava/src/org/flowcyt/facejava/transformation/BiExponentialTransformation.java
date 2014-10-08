package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.transformation.exception.RootFindingException;
import org.flowcyt.facejava.transformation.function.BiexponentialFunction;
import org.flowcyt.facejava.transformation.function.FunctionUtils;

/**
 * <p>
 * Applies a Bi-Exponential Transformation to a Parameter value. The transformation applied is:
 *  
 * <p>
 * root(B(y; a, b, c, d, f) - parameterValue) where
 * 
 * <ul>
 * <li>root() finds the root of the given function
 * <li>B(y; a, b, c, d, f) = a * e ^ (b * y) - c * e^(-d * y) + f. Note that
 *        a, b, c, d, and f are given constants and thus B only varies in y.
 * </ul>
 * 
 * <p>
 * Thus, the transformation returns y such that, given a, b, c, d, and f,
 * B(y; a, b, c, d, f) = parameterValue
 * 
 * @author echng
 */
public class BiExponentialTransformation extends SingleParameterTransformation {
	/**
	 * The function (with only a, b, c, d, f specified) to use with the root finder. The
	 * Parameter Value must be specified for each Event before calling the root finder
	 * since it changes for each Event.
	 */
	private BiexponentialFunction biex;
	
	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 * @param parameterReference A reference to the parameter it transforms. 
	 * @param a See class documentation.
	 * @param b See class documentation.
	 * @param c See class documentation.
	 * @param d See class documentation.
	 * @param f See class documentation.
	 */
	public BiExponentialTransformation(String name, ParameterReference parameterReference, double a, double b, double c, double d, double f) {
		super(name, parameterReference);
		biex = new BiexponentialFunction(a, b, c, d, f);
	}
	
	protected double applyTransformation(double parameterValue) throws RootFindingException {
		biex.setParameterValue(parameterValue);
		try {
			return FunctionUtils.findRoot(biex);
		} catch (RootFindingException ex) {
			throw new RootFindingException(this.toString() + ex.getMessage());
		}
	}
	
	public String toString() {
		return "Biexponential " + super.toString();
	}
}
