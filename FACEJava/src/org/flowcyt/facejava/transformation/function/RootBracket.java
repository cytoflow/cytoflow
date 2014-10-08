package org.flowcyt.facejava.transformation.function;

/**
 * <p>
 * An object which represents an interval. It's used to find an interval (bracket) around
 * the root of a function to initialize the Root Finder with.
 * 
 * @author echng
 */
class RootBracket {
	/**
	 * The starting lower guess.
	 */
	public static final double INITIAL_LOWER_GUESS = -10;
	
	/**
	 * The starting upper guess.
	 */
	public static final double INITIAL_UPPER_GUESS = 1024;
	
	/**
	 * How fast to grow the interval. The size of the interval will multiply by this
	 * factor upon each growth.
	 */
	public static final double INTERVAL_GROW_FACTOR = 2;
	
	/**
	 * We'll simply use public members for access since it's basically a struct (in the
	 * C-sense).
	 */
	public double lowerBound = INITIAL_LOWER_GUESS;
	
	public double upperBound = INITIAL_UPPER_GUESS;
	
	/**
	 * Grows the lower end of the interval. upperBound remains the same. The interval's
	 * size will will be multiplied byu the factor.
	 */
	public void growLowerBound() {
		lowerBound = upperBound - INTERVAL_GROW_FACTOR * (upperBound - lowerBound);
	}
	
	/**
	 * Grows the upper end of the interval. lowerBound remains the same. The interval's
	 * size will will be multiplied byu the factor.
	 */
	public void growUpperBound() {
		upperBound = lowerBound + INTERVAL_GROW_FACTOR * (upperBound - lowerBound);
	}
	
}
