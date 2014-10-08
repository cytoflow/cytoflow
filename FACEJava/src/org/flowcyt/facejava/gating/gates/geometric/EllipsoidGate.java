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
import org.flowcyt.facejava.gating.jaxb.Coordinate;
import org.flowcyt.facejava.gating.jaxb.Point;

/**
 * <p>
 * Represents an ellipsoid gate. An event is considered in the gate if the sum
 * of the euclidean distance from the event to the gate's two foci is less than
 * or equal to the gate's distance limit, where only the event data
 * corresponding to the gate's dimensions are considered in the computation.
 * 
 * @author echng
 */
public class EllipsoidGate extends GeometricGate {
	/**
	 * The limit for the sum of the distances from the two focis. Defines the outer
	 * border of the (hyper-)ellipsoid.
	 */
	private double distanceSum;

	/**
	 * One focus of the ellipsoid. Must have the same number of coordinates as there are
	 * dimensions.
	 */
	//private Point firstFocus;

	/**
	 * The other focus of the ellipsoid. Must have the same number of coordinates as
	 * there are dimensions.
	 */
	//private Point secondFocus;
	
	private List<Point> fociList;
	
	/**
	 * Creates an ElllipsoidGate with the given foci and distance.
	 * @param gateId The id for the gate.
	 * @param dimList The dimensions that should be considered when distances
	 * are computed.
	 * @param fociList The two foci of the ellipse.
	 * @param distanceSum The maximum sum of the distances for any event from the
	 * two foci.
	 * @throws InvalidGateDescriptionException Thrown if there are not two and only
	 * two foci given or the foci do not have the same number of coordinates as there
	 * are dimensions. 
	 */
	public EllipsoidGate(String gateId, List<ParameterReference> dimList, List<Point> fociList, double distanceSum) throws InvalidGateDescriptionException {
		super(gateId, dimList);
	
		this.fociList = fociList;
		this.distanceSum = distanceSum;
		
		validate();
	}
	
	public void validate() throws InvalidGateDescriptionException {
		if (fociList.size() != 2)
			throw new InvalidGateDescriptionException(this.getId(),
					"Ellipsoid Gates must have two and only two foci");
		if (fociList.get(0).getCoordinate().size() != dimensions.size())
			throw new InvalidGateDescriptionException(
					this.getId(),
					"First Focus does not have the same number of coordinates as there are dimensions");
		if (fociList.get(1).getCoordinate().size() != dimensions.size())
			throw new InvalidGateDescriptionException(
					this.getId(),
					"Second Focus does not have the same number of coordinates as there are dimensions");
	}
	
	public Set<Gate> getDirectDependencies() {
		return Collections.emptySet();
	}

	/**
	 * Computes the euclidean distance between the given Point and event data, where
	 * data points at corresponding indexes are assumed to correspond in their dimension.
	 * @param focus The focus.
	 * @param data The event data, filtered so that indexes in data correspond to 
	 * the same dimension as the same index in the focus.  
	 * @return Returns the euclidean distance between the focus and the data.
	 */
	private double computeEuclideanDistance(Point focus, double[] data) {
		double rv = 0;

		for (int i = 0; i < this.dimensions.size(); ++i) {
			rv += Math.pow(data[i] - focus.getCoordinate().get(i).getValue(), 2);
		}
		return Math.sqrt(rv);
	}

	/**
	 * An event is considered in the gate if the sum of the euclidean distance
	 * from the event to the gate's two foci is less than or equal to the gate's
	 * distance limit, where only the event data corresponding to the gate's
	 * dimensions are considered in the computation.
	 */
	public boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException {
		double[] retrievedData = new double[this.dimensions.size()];

		for (int i = 0; i < this.dimensions.size(); ++i) {
			retrievedData[i] = retriever.getScale(dimensions.get(i), ev);
		}

		return (computeEuclideanDistance(fociList.get(0), retrievedData) + 
				computeEuclideanDistance(fociList.get(1), retrievedData)) <= distanceSum;
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();

		builder.append("Ellipsoid ");
		builder.append(super.toString());
		builder.append("\nFocus 1: ");
		for (Coordinate coord : fociList.get(0).getCoordinate()) {
			builder.append(coord.getValue());
			builder.append(" ");
		}
		builder.append("\nFocus 2: ");
		for (Coordinate coord : fociList.get(1).getCoordinate()) {
			builder.append(coord.getValue());
			builder.append(" ");
		}
		builder.append("\nDistance Sum: ");
		builder.append(distanceSum);

		return builder.toString();
	}
}
