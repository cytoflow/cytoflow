package org.flowcyt.facejava.gating.gates.geometric;

import java.util.Collections;
import java.util.List;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.geometric.GeometricGate;
import org.flowcyt.facejava.gating.jaxb.Point2D;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.LinearRing;
import com.vividsolutions.jts.geom.Point;
import com.vividsolutions.jts.geom.Polygon;


/**
 * <p>
 * Represents a PolygonGate. An event is inside the gate if it is in the interior
 * of the region created by the given points (where the interior of non-simple
 * polygons are defined by the alternate filling method). Boundaries are considered
 * part of the region.
 * 
 * @author sli (original author), echng (heavily modified)
 */
public class PolygonGate extends GeometricGate{
	
	/**
	 * JTS object used to create JTS geometries. 
	 */
	private GeometryFactory factory;
	
	/**
	 * JTS Polygon which represents the gate's region.
	 */
	private Polygon polygon;
	
	private List<Point2D> pointList;
		
	/**
	 * Creates a PolygonGate object.
	 * 
	 * @param gateId The gate's id.
	 * @param dimList The gate's dimensions.
	 * @param pointList The gate's points used to determine boundaries.
	 * @throws InvalidGateDescriptionException Thrown if there are not two and only
	 * two dimensions specified OR each point does not have two and only two
	 * coordinates.
	 */
	public PolygonGate(String gateId, List<ParameterReference> dimList, List<Point2D> pointList) throws InvalidGateDescriptionException {
		super(gateId, dimList);
		
		this.pointList = pointList;
		
		validate();
		
		factory = new GeometryFactory();
		polygon = formPolygon(pointList);
	}
	
	public void validate() throws InvalidGateDescriptionException {
		if (this.dimensions.size() != 2)
			throw new InvalidGateDescriptionException(this.getId(), 
					"Polygon Gates must have two and only two dimensions");
		
		for (Point2D pt : pointList) {
			if (pt.getCoordinate().size() != 2)
				throw new InvalidGateDescriptionException(this.getId(), 
					"Points in Polygon Gates must have two and only two coordinates");
		}
	}
	
	public Set<Gate> getDirectDependencies() {
		return Collections.emptySet();
	}
	
	/**
	 * Uses JTS to form the Polygon object to be used for hit-testing when events
	 * are checked.
	 * @param pointList The points along the boundaries.
	 * @return Returns the polygon for the gate.
	 */
	private Polygon formPolygon(List<Point2D> pointList) {
		Coordinate[] coordinates = new Coordinate[pointList.size()+1]; // one more spot for closed point
		
		int i = 0;
		for(Point2D pt : pointList) {
			double x = pt.getCoordinate().get(0).getValue();
			double y = pt.getCoordinate().get(1).getValue();

			coordinates[i++] = new Coordinate(x, y);
		}
		//	copy the first point to the end because LinearRing has to be closed.
		coordinates[i] = coordinates[0];
		
		LinearRing lr = factory.createLinearRing(coordinates);
		
		return new Polygon(lr, null, factory);
	}
	
	/**
	 * An event is inside the gate if it is in the interior of the region created
	 * by the given points (where the interior of non-simple polygons are defined
	 * by the alternate filling method). Boundaries are considered part of the region.
	 */
	public boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException {
		// There must be two points since the xml file is validated by the schema.
		double firstDatum = retriever.getScale(this.dimensions.get(0), ev);
		double secondDatum = retriever.getScale(this.dimensions.get(1), ev);
		
		Point testPoint = factory.createPoint(new Coordinate(firstDatum, secondDatum));	
		
		// contains() considers coundaries to be exterior regions but we want them
		// to be interior, so we need touches() to tell us if it's on the boundary.
		return polygon.contains(testPoint) || polygon.touches(testPoint);		
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		
		builder.append("Polygon ");
		builder.append(super.toString());
		builder.append("\nPoints:\n");
		
		Coordinate[] coords = polygon.getCoordinates();
		for (int i = 0; i < coords.length; ++i) {
			builder.append(coords[i]);
			builder.append("\n");
		}
		return builder.toString();
	}
}
