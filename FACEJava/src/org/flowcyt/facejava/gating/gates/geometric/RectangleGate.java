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

/**
 * <p>
 * Represents a rectangle gate. An event is inside the gate if for each rectangle gate 
 * dimension specified, the event data corresponding to its paramter is within the range
 * [min, max] where min = -inf and max = +inf if min or max is not specified, respectively
 * (at least one must be specified).
 * 
 * <p>
 * RectangleGates use a different type of dimension element than GeometricGates so it does
 * not inherit from GeometricGate.
 *  
 * @author sli (original author), echng (heavily modified)
 */

public class RectangleGate extends GeometricGate {
	/**
	 * The dimensions of the gate.
	 */
	List<RectangleDimensionRange> dimensionRanges;
	
	/**
	 * Creates a RectangleGate.
	 * 
	 * @param gateId The gate's id.
	 * @param dimList The gate's dimensions.
	 * @param dimensionRanges A list of the ranges for each of the dimensions. The order here
	 * corresponds to the order in the dimension list.
	 * @throws InvalidGateDescriptionException Thrown if
	 * - at least one of the dimensions does not specify both min and max.
	 */
	public RectangleGate(String gateId, List<ParameterReference> dimList, List<RectangleDimensionRange> dimensionRanges) throws InvalidGateDescriptionException { 
		super(gateId, dimList);
		
		this.dimensionRanges = dimensionRanges;
		validate();
	}
	
	public void validate() throws InvalidGateDescriptionException {
		int i = 0;
		for (RectangleDimensionRange range : dimensionRanges) {
			if (range.getLower() == Double.NEGATIVE_INFINITY && range.getUpper() == Double.POSITIVE_INFINITY)
				throw new InvalidGateDescriptionException(this.getId(), 
						this.dimensions.get(i) + " - At least one of min and max must be specified.");
			++i;
		}
	}

	/**
	 * An event is inside the gate if for each rectangle gate dimension specified, the
	 * event data corresponding to its paramter is within the range [min, max] where
	 * min = -inf and max = +inf if min or max is not specified, respectively (at least
	 * one must be specified).
	 */
	public boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException {
		int i = 0;
		for (ParameterReference rectDim : this.dimensions) {
			double data = retriever.getScale(rectDim, ev);
			if (!dimensionRanges.get(i++).inRange(data))
				return false;
		}
		return true;
	}
	
	public Set<Gate> getDirectDependencies() {
		return Collections.emptySet();
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		
		builder.append("Rectangle ");
		builder.append(super.toString());
		builder.append("\nDimensions:\n");
		for (RectangleDimensionRange rectDim : this.dimensionRanges) {
			builder.append("Min: ");
			builder.append(rectDim.getLower());
			builder.append("; Max: ");
			builder.append(rectDim.getUpper());
			builder.append("\n");
		}
		return builder.toString();
	}
	
	/**
	 * Helper class used to specify the range (upper and lower) for each of the dimensions in the
	 * gate. Lower is inclusive while the upper is exclusive. 
	 * 
	 * @author echng
	 */
	public static class RectangleDimensionRange {
		private double lower;
		
		private double upper;
		
		public RectangleDimensionRange(Double lower, Double upper) {
			if (lower == null)
				this.lower = Double.NEGATIVE_INFINITY;
			else
				this.lower = lower;
			
			if (upper == null)
				this.upper = Double.POSITIVE_INFINITY;
			else
				this.upper = upper;
		}
		
		public double getLower() {
			return lower;
		}
		
		public double getUpper() {
			return upper;
		}	
		
		public boolean inRange(double val) {
			return val >= lower && val < upper;
		}
	}
}
