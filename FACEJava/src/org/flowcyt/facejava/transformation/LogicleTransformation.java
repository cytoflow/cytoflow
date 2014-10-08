package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.transformation.exception.InvalidTransformationException;
import org.flowcyt.facejava.transformation.exception.RootFindingException;
import org.flowcyt.facejava.transformation.function.FunctionUtils;
import org.flowcyt.facejava.transformation.function.LogicleFunction;

/**
 * <p>
 * Applies a Logicle Transformation to a Parameter value. The transformation applied is:
 * 
 * <p>
 * root(S(y; T, w, m) - parameterValue) where
 * 
 * <ul>
 * <li>root() finds the root of the given function
 * <li>
 *     <pre>
 * S(y; T, w, m) = { T * e ^ -(m - w) * (e ^ (y - w) - p ^ 2 * e ^ (-(y - w)/p) + p^2 - 1    if y >=w
 *                 { -(T * e ^ -(m - w) * (e ^ (w - y) - p ^ 2 * e ^ (-(w - y)/p) + p^2 - 1) otherwise
 *     </pre>
 * </li>
 * <li>p is defined as w = 2 * ln(p) / (p + 1)
 * </ul>
 *  
 * Thus, the transformation returns y such that, given T, w, and m,
 * S(y; T, w, m) = parameterValue 
 *        
 * @author echng
 */
public class LogicleTransformation extends SingleParameterTransformation {
	/**
	 * The function (with only T, w, and m specified) to use with the root finder. The
	 * Parameter Value must be specified for each Event before calling the root finder
	 * since it changes for each Event.
	 */
	private LogicleFunction logicle;
	
	/**
	 * We can use w to make our root finding guess slightly better. The Logicle function
	 * grows exponentially around w (in both directions) where it = 0 (when there is no
	 * parameterValue (i.e., parameterValue = 0). So we'll use a small interval
	 * around w as our initial guess since it will, in most cases contain the root.
	 */
	private double w;

	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 * @param parameterReference A reference to the parameter it transforms. 
	 * @param t See class documentation.
	 * @param w See class documentation.
	 * @param m See class documentation.
	 * @throws InvalidTransformationException Thrown if the value for p (given w) could not
	 * be calculated.
	 */
	public LogicleTransformation(String name, ParameterReference parameterReference, double t, double w, double m) throws InvalidTransformationException {
		super(name, parameterReference);
		
		this.w = w;
		try {
			logicle = new LogicleFunction(t, w, m);
		} catch (RootFindingException ex) {
			throw new InvalidTransformationException("Logicle Transformation " + name + " could not solve for p value. " + ex.getMessage());
		}
	}

	protected double applyTransformation(double parameterValue) throws RootFindingException {
		logicle.setParameterValue(parameterValue);
		try {
			return FunctionUtils.findRoot(logicle, w - 10, w + 10);
		} catch (RootFindingException ex) {
			throw new RootFindingException(this.toString() + ex.getMessage());
		}
	}
	
	public String toString() {
		return "Logicle " + super.toString();
	}
}
