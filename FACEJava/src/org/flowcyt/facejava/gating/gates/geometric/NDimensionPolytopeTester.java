package org.flowcyt.facejava.gating.gates.geometric;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.ListIterator;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.gates.GateSubPopulation;
import org.flowcyt.facejava.gating.jaxb.Coordinate;
import org.flowcyt.facejava.gating.jaxb.Point;

import qs.Problem;
import qs.QS;
import qs.QSException;

/**
 * <p>
 * For 3 or more dimensions, we solve an LP to determine if an event is inside the Gate
 * since we can't do the convex hull computation for higher dimensions (JTS only supports up to
 * 2 dimensions). This tester can actually perform the test correctly for arbitrary
 * dimensions (hence, "n-dimension"), however, it is slow for low dimensions. 
 * 
 * @author echng
 */
public class NDimensionPolytopeTester extends PolytopeGateTester {
	/**
	 * The wrapper interface to QSopt. This contains the final LP that we'll use to 
	 * solve the problem except for the objective function and the final constraint which
	 * both depend on the query point. It will contain the optimal solution and objective
	 * value for the last time solve() was called.
	 */
	private LPWrapper lpWrapper;
	
	/**
	 * The number of dimensions in the gate.
	 */
	private int dimensionCount;
	
	/**
	 * Creates a n-dimension PolytopeGateTester.
	 * 
	 * @param gate The PolytopeGate being tested.
	 * @param pointList The points in the polytope.
	 */
	public NDimensionPolytopeTester(PolytopeGate gate, List<Point> pointList) {
		super(gate);
		this.dimensionCount = gate.getDimensions().size();
		
		removeRedundancies(pointList);
		this.lpWrapper = new QSOptWrapper(pointList, -1);
	}

	/**
	 * <p>
	 * This method removes redundant points to decrease the number of constraints to the
	 * minimum needed to determine if a point is in the convex hull. A point q in S is
	 * redundant iff q is in conv(S - {q}} (i.e., the convex hull is the same with or 
	 * without q in the set of points).
	 * 
	 * <p>
	 * Thus, given S (the points), for each point p in S, we build the LP using
	 * S - {p} as the hull points and test using p as the query point. If it is within
	 * conv(S - {p}), then we can remove it from S for points after p.
	 * 
	 * @param pointList The input point list. Any redundant points will be removed when
	 * this method returns.
	 */
	private void removeRedundancies(List<Point> pointList) {
		ListIterator<Point> removalIterator = pointList.listIterator();
		while (removalIterator.hasNext()) {
			int testPointIndex = removalIterator.nextIndex();
			Point testPoint = removalIterator.next();
			
			LPWrapper wrapper = new QSOptWrapper(pointList, testPointIndex);
			double[] obj = new double[dimensionCount + 1];
			for (int i = 0; i < obj.length; ++i) {
				if (i == dimensionCount) {
					obj[i] = -1;
				} else {
					obj[i] = testPoint.getCoordinate().get(i).getValue();
				}			
			}
			if (wrapper.solve(obj) && wrapper.getOptimalValue() <= 0) {
				removalIterator.remove();
			}
		}
	}
	
	/**
	 * <p>
	 * We can optimize our gate testing for Polytopes by not solving the LP for each Event.
	 * First, we keep solving until we find an event that is NOT in the convex hull. Then
	 * our LP has found a separating hyperplane, H. We can test if there are any other
	 * points that are also separated by H from conv(s). For all the points found that
	 * are separated, we save the time spent solving the LP since we know they can not be
	 * in conv(S). Depending on the distribution of the events and the convex hull, this
	 * can save *a lot* of time.
	 * 
	 * <p>
	 * We know H separates conv(S) from a point q, iff z_transpose * q > z_0. (From the
	 * objective function of the LP.)
	 */
	public GateSubPopulation isInside(Population population, DataRetriever retriever) throws DataRetrievalException {
		List<Event> insideEvents = new ArrayList<Event>();
		LinkedList<Event> eventsToTest = new LinkedList<Event>(population);
		
		double[] currentSolution = new double[dimensionCount + 1];
		
		while (!eventsToTest.isEmpty()) {
			// Get the first event and remove it from the list of Events to be tested.
			// Must be there since we tested for emptiness.
			Event testEvent = eventsToTest.removeFirst();			
			
			if (this.isInside(testEvent, retriever)) {
				insideEvents.add(testEvent);
			} else if (lpWrapper.wasSolved()){
				lpWrapper.getOptimalSolution(currentSolution);
				 
				// Find events which are separated by the same hyperplane found for testEvent
				// and remove them.
				ListIterator<Event> eventsToTestIter = eventsToTest.listIterator();
				while (eventsToTestIter.hasNext()) {
					Event ev = eventsToTestIter.next();
					double solnDotEvent = 0;
					for (int i = 0; i < dimensionCount; ++i) {
						solnDotEvent += retriever.getScale(gate.getDimensions().get(i), ev) * currentSolution[i];
					}
					if (solnDotEvent >= currentSolution[dimensionCount])
						eventsToTestIter.remove();
				}
			}
		}
		
		return new GateSubPopulation(population, retriever, gate, insideEvents);
	}

	/**
	 * <p>
	 * An event is inside if it is inside the convex hull of the polytope generated
	 * by the given points (where only the data in the given dimensions are considered).
	 * 
	 * <p>
	 * Because we allow gates in arbitrarily high dimensions, we'll use Linear Programming
	 * to solve the problem since the Convex Hull computation has bad worst-case complexity
	 * in high dimensions. See http://www.ifor.math.ethz.ch/~fukuda/polyfaq/node22.html.
	 * 
	 * <p>
	 * For the set of points, S = {s_1, s_2, ..., s_n}, which define the
	 * convex hull, a point q is not in conv(S) if and only if the following LP has a
	 * optimal objective value > 0 (strictly).
	 * <pre>
	 *      max z_transpose * q - z_0
	 *      subject to
	 *           z_transpose * p_i - z_0 <= 0 for i = 1, ..., n
	 *           z_transpose * q   - z_0 <= 1
	 *           z free
	 *           z_0 free
	 * </pre>
	 * 
	 * 
	 * <p>
	 * The set H = { x in R^d | z_transpose * x = z_0 } is a hyperplane which separates
	 * q from conv(S) and therefore q is not in conv(S).
	 */
	public boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException {
		double[] obj = new double[dimensionCount + 1];
		for (int i = 0; i < obj.length; ++i) {
			if (i == dimensionCount) {
				obj[i] = -1;
			} else {
				obj[i] = retriever.getScale(gate.getDimensions().get(i), ev);
			}			
		}
		return lpWrapper.solve(obj) && lpWrapper.getOptimalValue() <= 0;
	}
	
	public String toString() {		
		return lpWrapper.toString();
	}
	
	/**
	 * A generic wrapper to interface with a LP library to solve the convex hull LP.
	 * 
	 * @author echng
	 */
	public static interface LPWrapper {
		/**
		 * <p>
		 * Solves the Problem using the given objective function. i.e., tests if the point
		 * q given in the objective function is within the convex hull of the points given
		 * in the constructor. It automatically also fills in the last constraint.
		 * 
		 * <p>
		 * If the solver does not find an optimal value then we know there was some error
		 * and false is returned. Then getOptimalValue() and getOptimalSolution() will return
		 * values that can not be used.
		 * 
		 * <p>
		 * We know that an optimal value must always be found since the LP always has a 
		 * feasible solution with z = 0 (vector) and z_0 = 0. Furthermore, it cannot be
		 * unbounded since the last constraint  z_transpose * q   - z_0 <= 1 puts an 
		 * upper bound on the objective function of 1.  
		 * 
		 * @param obj The objective function.
		 * @return Returns true if it was solved correctly and thus whether or not
		 * getOptimalValue() and getOptimalSolution() will return values that can be used.
		 */
		public boolean solve(double[] obj);
		
		/**
		 * @return Returns true if the last call to solve() was solved correctly.
		 */
		public boolean wasSolved();
		
		/**
		 * @return Returns the objective function value for the last call to solve().
		 * If the last solve() failed and the LP was not solved correctly, then NaN
		 * is returned.
		 */
		public double getOptimalValue();
		/**
		 * @param soln Will be filled with the optimal soln to the last call to solve().
		 * If the last solve() failed and the LP was not solved correctly, then soln
		 * is filled with zeroes.
		 */
		public void getOptimalSolution(double[] soln);
	}
	
	/**
	 * <p>
	 * Interfaces with the QSopt library. It is specifically designed to solve LPs of the
	 * form that we care about for PolytopeGates. It is *NOT* a general interface to
	 * QSopt. Each QSoptWrapper object wraps an LP for one set of constraint points (i.e.,
	 * points that are used to determine the convex hull).
	 * 
	 * @author echng
	 */
	class QSOptWrapper implements LPWrapper {
		/**
		 * See the QSopt documentation for the format of the following members.
		 */
		
		private static final int OBJ_SENSE = QS.MAX;
		
		private int numConstraints;
		
		private int[] nonZerosPerCol;
		
		private int[] colStartIndices;
		
		private int[] colNonZeroEntryIndex;
		
		private double[] values;
		
		private double[] rhs;
		
		private char[] sense;
		
		private double[] lowerBounds;
		
		private double[] upperBounds;
		
		/**
		 * The QSopt Problem the object wraps.
		 */
		private Problem finalProblem;
		
		/**
		 * Is true when QSopt correctly solves the LP. 
		 */
		private boolean solvedCorrectly = false;
		
		/**
		 * Creates a QSOptWrapper object. It initializes the values needed to solve the LP
		 * except for the objective function and the last constraint which both depend
		 * on the query point. (i.e., only the following is set-up for the LP
		 *       
		 *       z_transpose * p_i - z_0 <= 0 for i = 1, ..., n
		 *       z free
		 *       z_0 free
		 * 
		 * and the rest will get filled in when solve() is called.)
		 * 
		 * @param constraintPoints The points to use 
		 * @param ignoreIndex Ignores the point at the given index when creating the LP. 
		 * This is used when we want to remove redundant points from a given set of points,
		 * where each point is left out of the constraints and is tested like any other
		 * point would be.
		 */
		public QSOptWrapper(List<Point> constraintPoints, int ignoreIndex) {
			int colCount = dimensionCount + 1;
			numConstraints = constraintPoints.size();
			if (ignoreIndex < 0)
				++numConstraints;
			
			nonZerosPerCol = new int[colCount];
			colStartIndices = new int[colCount];
			colNonZeroEntryIndex = new int[colCount * numConstraints];
			
			values = new double[colCount * numConstraints];
			rhs = new double[numConstraints];
			sense = new char[numConstraints];
			lowerBounds = new double[colCount];
			upperBounds = new double[colCount];
			
			/**
			 * See the QSopt documentation for the format of the following members.
			 */
						
			for (int i = 0; i < numConstraints; ++i) {
				rhs[i] = 0;
				sense[i] = 'L';
			}
			rhs[numConstraints - 1] = 1;
			
			for (int i = 0; i < colCount; ++i) {
				nonZerosPerCol[i] = numConstraints;
				colStartIndices[i] = numConstraints * i;
				lowerBounds[i] = -QS.MAXDOUBLE;
				upperBounds[i] = QS.MAXDOUBLE;
			}
			
			for (int i = 0; i < constraintPoints.size(); ++i) {
				if (i == ignoreIndex)
					continue;
				List<Coordinate> coords = constraintPoints.get(i).getCoordinate();
				
				int constraintNumber = ignoreIndex >= 0 && i > ignoreIndex ? (i - 1) : i;
				for (int j = 0; j < colCount; ++j) {
					int oneDimIndex = constraintNumber + (j * numConstraints);
					if (j == dimensionCount) {
						colNonZeroEntryIndex[oneDimIndex] = constraintNumber;
						values[oneDimIndex] = -1;
					} else {
						colNonZeroEntryIndex[oneDimIndex] = constraintNumber;
						values[oneDimIndex] = coords.get(j).getValue();
					}
				}				
			}
			
			for (int i = 0; i < colCount; ++i) {
				colNonZeroEntryIndex[(i * numConstraints) + numConstraints - 1] = numConstraints - 1;
			}
		}
		
		public boolean solve(double[] obj) {
			for (int i = 0; i <= dimensionCount; ++i) {
				int index = (i * numConstraints) + numConstraints - 1;
				if (i == dimensionCount) {
					values[index] = -1;
				} else {
					values[index] = obj[i];
				}			
			}
			
			try {
				finalProblem = new Problem(null,
						dimensionCount + 1,
						numConstraints,
						nonZerosPerCol,
						colStartIndices,
						colNonZeroEntryIndex,
						values,
						OBJ_SENSE,
						obj,
						rhs,
						sense,
						lowerBounds,
						upperBounds,
						null,
						null);
				finalProblem.opt_primal();
				solvedCorrectly = finalProblem.get_status() == QS.LP_OPTIMAL;
				return solvedCorrectly;
			} catch (QSException e) {
				return false;
			}			
		}
		
		public boolean wasSolved() {
			return solvedCorrectly;
		}
		
		public double getOptimalValue() {
			if (solvedCorrectly) {
				try {
					return finalProblem.get_objval();
				} catch (QSException e) {}
			}
			return Double.NaN;
		}
		
		public void getOptimalSolution(double[] soln) {
			if (solvedCorrectly) {
				try {
					finalProblem.get_x_array(soln);
					return;
				} catch (QSException e) {}
			}
			Arrays.fill(soln, 0);
		}
		
		public String toString() {
			StringBuilder builder = new StringBuilder();
			
			builder.append("\nDimensions: ");
			builder.append(dimensionCount);
			
			builder.append("\nConstraints: ");
			builder.append(numConstraints);
			
			builder.append("\n# Non Zeros Per Column: ");
			builder.append(Arrays.toString(nonZerosPerCol));
			
			builder.append("\nColumn Start indices: ");
			builder.append(Arrays.toString(colStartIndices));
			
			builder.append("\nNon Zero Entries Per Column: ");
			builder.append(Arrays.toString(colNonZeroEntryIndex));
			
			builder.append("\nConstraint Matrix: ");
			builder.append(Arrays.toString(values));
			
			builder.append("\nRHS: ");
			builder.append(Arrays.toString(rhs));
			
			builder.append("\nSense: ");
			builder.append(Arrays.toString(sense));
			
			builder.append("\nLower Bounds: ");
			builder.append(Arrays.toString(lowerBounds));
			
			builder.append("\nUpper Bounds: ");
			builder.append(Arrays.toString(upperBounds));
			
			return builder.toString();
		}
	}
}
