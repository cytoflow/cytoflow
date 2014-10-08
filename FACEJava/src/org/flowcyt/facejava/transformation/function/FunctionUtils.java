package org.flowcyt.facejava.transformation.function;

import org.apache.commons.math.ConvergenceException;
import org.apache.commons.math.FunctionEvaluationException;
import org.apache.commons.math.analysis.UnivariateRealFunction;
import org.apache.commons.math.analysis.UnivariateRealSolver;
import org.apache.commons.math.analysis.UnivariateRealSolverFactory;
import org.flowcyt.facejava.transformation.exception.RootFindingException;

/**
 * <p>
 * A simple adapter into the Commons Math root finding functionality. 
 * 
 * @author echng
 */
public class FunctionUtils {
	/**
	 * The maximum number of bracketing growths before the root bracket finding stops.
	 */
	public static final int MAX_BRACKETING_ITERATIONS = 100;
	
	/**
	 * Used to create solvers to find roots.
	 */
	public static UnivariateRealSolverFactory solverFactory = UnivariateRealSolverFactory.newInstance();
	
	/**
	 * Finds an appropriate interval/bracket around a root for the given function. The
	 * returned root bracket will be appropriate to initialize the root finding algorithm
	 * with.
	 * 
	 * @param func The function to find the Rootbracket for.
	 * @return Returns the found RootBracket.
	 * @throws FunctionEvaluationException Thrown if there was a problem evaluating the
	 * function.
	 * @throws RootFindingException Thrown if the maximum number of growths was reached.
	 */
	public static RootBracket findRootBracket(UnivariateRealFunction func) throws FunctionEvaluationException, RootFindingException {
		return findRootBracket(func, RootBracket.INITIAL_LOWER_GUESS, RootBracket.INITIAL_UPPER_GUESS);
	}
	
	/**
	 * Finds an appropriate interval/bracket around a root for the given function. The
	 * returned root bracket will be appropriate to initialize the root finding algorithm
	 * with.
	 * 
	 * @param func The function to find the Rootbracket for.
	 * @param initialLower An initial guess to use for the lower bound on the interval
	 * containing the root
	 * @param initialUpper An initial guess to use for the upper bound on the interval
	 * containing the root
	 * @return Returns the found RootBracket.
	 * @throws FunctionEvaluationException Thrown if there was a problem evaluating the
	 * function.
	 * @throws RootFindingException Thrown if the maximum number of growths was reached.
	 */
	public static RootBracket findRootBracket(UnivariateRealFunction func, double initialLower, double initialUpper) throws FunctionEvaluationException, RootFindingException {
		RootBracket rv = new RootBracket();
		rv.lowerBound = initialLower;
		rv.upperBound = initialUpper;
		
		int i = 0;
		while (true) {
			double lowerFuncVal = func.value(rv.lowerBound);
			double upperFuncVal = func.value(rv.upperBound);
			
			if ((lowerFuncVal < 0 && upperFuncVal > 0) || (lowerFuncVal > 0 && upperFuncVal < 0))
				break;
			
			// Find out which bound is closer to 0.
			if (Math.abs(lowerFuncVal) <= Math.abs(upperFuncVal))
				rv.growLowerBound();
			else
				rv.growUpperBound();
			
			// XXX: Use max and min double as limits instead of an iterations bound? 
			if (i++ >= MAX_BRACKETING_ITERATIONS) {
				throw new RootFindingException("Could not find appropriate Root Bracket.");
			}
		}		
		return rv;
	}
	
	/**
	 * Finds the root for the given function.
	 * 
	 * @param func The function to find the root for.
	 * @return Returns the root.
	 * @throws RootFindingException Thrown if there was a problem finding the root,
	 * which happens when:
	 * <ul>
	 * <li>the root finding algorithm does not converge.
	 * <li>there is a problem evaluating the function.
	 * <li>no appropriate RootBracket (one that straddles y=0) could be found within the maximum number of iterations.
	 * </ul> 
	 */
	public static double findRoot(UnivariateRealFunction func) throws RootFindingException {
		return findRoot(func, RootBracket.INITIAL_LOWER_GUESS, RootBracket.INITIAL_UPPER_GUESS);		
	}
	
	/**
	 * Finds the root for the given function.
	 * 
	 * @param func The function to find the root for.
	 * @param lowerBoundGuess An initial guess to use for the lower bound on the interval
	 * containing the root
	 * @param upperBoundGuess An initial guess to use for the upper bound on the interval
	 * containing the root
	 * @return Returns the root.
	 * @throws RootFindingException Thrown if there was a problem finding the root,
	 * which happens when:
	 * <ul>
	 * <li>the root finding algorithm does not converge.
	 * <li>there is a problem evaluating the function.
	 * <li>no appropriate RootBracket (one that straddles 0) could be found within the maximum number of iterations.
	 * </ul> 
	 */
	public static double findRoot(UnivariateRealFunction func, double lowerBoundGuess, double upperBoundGuess) throws RootFindingException {
		RootBracket bracket;
		try {
			bracket = FunctionUtils.findRootBracket(func, lowerBoundGuess, upperBoundGuess);
			UnivariateRealSolver solver = solverFactory.newBrentSolver(func);
			return solver.solve(bracket.lowerBound, bracket.upperBound);
		} catch (FunctionEvaluationException e) {
			throw new RootFindingException("Could not evaluate function", e);
		} catch (ConvergenceException e) {
			throw new RootFindingException("Root Finder did not converge", e);
		}		
	}

}
