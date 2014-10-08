package org.flowcyt.facejava.gating.gates.geometric;

import java.util.Collections;
import java.util.List;

import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.gating.gates.AbstractGate;

/**
 * <p>
 * Abstract super-class for gates which have Dimension elements.
 * 
 * @author echng
 */
public abstract class GeometricGate extends AbstractGate {	 
	/**
	 * The dimensions of the geometeric gate as ParameterReferences. Order matters, since the 
	 * other portions of the gate which determine inside-ness often correspond to this dimension
	 * order in some way (e.g., the order for coordinates in points for correspond to this order). 
	 */
	protected List<ParameterReference> dimensions;
	 
	/**
	 * Constructor.
	 * 
	 * @param gateId The gate's id.
	 * @param dimList The dimensions for the geometric gates as ParameterReferences. Order matters.
	 */
	public GeometricGate(String gateId, List<ParameterReference> dimList) {
		super(gateId);
		
		dimensions = dimList;
	}
	
	/**
	 * @return Returns the dimensions that the GeometricGate gates upon. i.e., which 
	 * ParameterReferences each dimension of the Gate is for. The order of the returned
	 * List matters since for most gates the order of the coordinates in points
	 * being tested must correspond to the order of this dimension list.
	 */
	public List<ParameterReference> getDimensions() {
		return Collections.unmodifiableList(dimensions);
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append(super.toString());
		builder.append("\nDimensions: ");
		for (ParameterReference dim : dimensions) {
			builder.append(dim);
			builder.append(" ");
		}
		return builder.toString();
	}
	
}
