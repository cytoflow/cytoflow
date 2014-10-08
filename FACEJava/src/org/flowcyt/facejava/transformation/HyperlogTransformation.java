package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.transformation.exception.RootFindingException;
import org.flowcyt.facejava.transformation.function.FunctionUtils;
import org.flowcyt.facejava.transformation.function.HyperlogFunction;

/**
 * <p>
 * Applies a Hyperlog Transformation to a Parameter value. The transformation applied is:
 * 
 * <p>
 * root(EH(y; b, d, r) - parameterValue) where
 * <ul>
 * <li>root() finds the root of the given function
 * <li>
 *    <pre>
 * EH(y; b, d, r) = { 10 ^ (y * d / r) + b * (d / r) * y - 1        if y >= 0   
 *                  { -(10 ^ (-y * d / r)) + b * (d / r) * y + 1    otherwise
 *    </pre>
 * </ul>
 *                            
 * <p>
 * Thus, the transformation returns y such that, given b, d, and r,
 * EH(y; b, d, r) = parameterValue
 *                          
 * @author echng
 */
public class HyperlogTransformation extends SingleParameterTransformation {
	/**
	 * The function (with only b, d, and r specified) to use with the root finder. The
	 * Parameter Value must be specified for each Event before calling the root finder
	 * since it changes for each Event.
	 */
	private HyperlogFunction hl;
	
	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 * @param parameterReference A reference to the parameter it transforms. 
	 * @param b See class documentation.
	 * @param d See class documentation.
	 * @param r See class documentation.
	 */
	public HyperlogTransformation(String name, ParameterReference parameterReference, double b, double d, double r) {
		super(name, parameterReference);
		hl = new HyperlogFunction(b, d, r);
	}

	protected double applyTransformation(double parameterValue) throws RootFindingException {
		hl.setParameterValue(parameterValue);
		try {
			return FunctionUtils.findRoot(hl);
		} catch (RootFindingException ex) {
			throw new RootFindingException(this.toString() + ex.getMessage());
		}
	}
	
	public String toString() {
		return "Hyperlog " + super.toString();
	}
}
