package org.flowcyt.facejava.gating.gates.geometric;

import java.util.List;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.jaxb.Point;

import com.vividsolutions.jts.algorithm.ConvexHull;
import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.geom.GeometryFactory;

/**
 * <p>
 * In 2D, we can do the convex hull computation quickly, so we'll special case it. We use
 * JTS to calculate the convex hull of the 2D points and we can use the returned Geometry for
 * all further point tests.
 * 
 * @author echng
 */
public class TwoDimensionPolytopeTester extends PolytopeGateTester {
	
	/**
	 * JTS GeometryFactory for creating points to test against the convex hull.
	 */
	private GeometryFactory geomFact;
	
	/**
	 * The convex hull found by JTS.
	 */
	private Geometry convexHull;

	/**
	 * Creates a 2-D PolytopeGateTester.
	 * @param gate The PolytopeGate the Tester is for. Must have only two dimensions.
	 * @param pointList The points in the polytope.
	 */
	public TwoDimensionPolytopeTester(PolytopeGate gate, List<Point> pointList) {
		super(gate);
		
		if (gate.getDimensions().size() != 2)
			throw new IllegalArgumentException("TwoDimensionPolytopeTester only suuport 2-dimensional gates.");
		
		geomFact = new GeometryFactory();
		formConvexHull(pointList);
	}
	
	/**
	 * Uses JTS to calculate the Convex Hull.
	 * 
	 * @param pointList The points to calculate the convex hull of.
	 */
	private void formConvexHull(List<Point> pointList) {
		Coordinate[] coordinates = new Coordinate[pointList.size()];
		
		int i = 0;
		for (Point pt : pointList) {
			double x = pt.getCoordinate().get(0).getValue();
			double y = pt.getCoordinate().get(1).getValue();

			coordinates[i++] = new Coordinate(x, y);
		}
		
		ConvexHull algo = new ConvexHull(coordinates, geomFact);
		convexHull = algo.getConvexHull();
	}

	public boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException {
		// There must be two dimensions since we check in the constructor.
		double firstDatum = retriever.getScale(gate.getDimensions().get(0), ev);
		double secondDatum = retriever.getScale(gate.getDimensions().get(1), ev);
		
		com.vividsolutions.jts.geom.Point testPoint = geomFact.createPoint(new Coordinate(firstDatum, secondDatum));	
		
		// contains() considers coundaries to be exterior regions but we want them
		// to be interior, so we need touches() to tell us if it's on the boundary.
		return convexHull.contains(testPoint) || convexHull.touches(testPoint);
	}

	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("Convex Hull Points: ");
		builder.append(convexHull.toString());
		return builder.toString();
	}
}
