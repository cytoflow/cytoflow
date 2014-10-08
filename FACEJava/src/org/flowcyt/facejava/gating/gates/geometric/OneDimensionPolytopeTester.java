package org.flowcyt.facejava.gating.gates.geometric;

import java.util.List;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.jaxb.Point;

/**
 * <p>
 * Since arbitrary dimensional Polytope gates take a while to solve, we'll special case
 * 1-D gates since they are just range gates between the min and max of the points given.
 * 
 * @author echng
 */
class OneDimensionPolytopeTester extends PolytopeGateTester {

	/**
	 * The minimum coordinate of the given points.
	 */
	private double min;
	
	/**
	 * The maximum coordinate of the given points.
	 */
	private double max;
	
	/**
	 * Constructor.
	 * 
	 * @param gate The PolytopeGate the Tester is for. Must have only one dimension.
	 * @param pointList The points in the polytope.
	 */
	public OneDimensionPolytopeTester(PolytopeGate gate, List<Point> pointList) {
		super(gate);
		
		if (gate.getDimensions().size() != 1)
			throw new IllegalArgumentException("OneDimensionPolytopeTester can only support 1-dimensional gates.");
		
		min = Double.POSITIVE_INFINITY;
		max = Double.NEGATIVE_INFINITY;
		
		for (Point pt : pointList) {
			double coord = pt.getCoordinate().get(0).getValue();
			min = Math.min(min, coord);
			max = Math.max(max, coord);
		}
	}

	public boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException {
		double data = retriever.getScale(gate.getDimensions().get(0), ev);
		return data >= this.min && data <= this.max;
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("[Min: ");
		builder.append(min);
		builder.append("; Max: ");
		builder.append(max);
		builder.append("]");
		return builder.toString();
	}

}
