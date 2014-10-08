package org.flowcyt.facejava.gating.xmlio;

import java.util.ArrayList;
import java.util.List;

import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.gates.bool.BooleanGate;
import org.flowcyt.facejava.gating.gates.decisiontree.DecisionTreeGate;
import org.flowcyt.facejava.gating.gates.geometric.EllipsoidGate;
import org.flowcyt.facejava.gating.gates.geometric.PolygonGate;
import org.flowcyt.facejava.gating.gates.geometric.PolytopeGate;
import org.flowcyt.facejava.gating.gates.geometric.RectangleGate;
import org.flowcyt.facejava.gating.jaxb.Dimension;
import org.flowcyt.facejava.gating.jaxb.RectangleGateDimension;

/**
 * <p>
 * GateFactories create and add to the GateSet the proper concrete Gate class that 
 * corresponds to the auto-generated JAXB class for one of the gate elements. 
 * Each GateFactory is tied to one GateSet and any created Gates will be added to that
 * GateSet. The factory abstracts out the ugly JAXB-gate-element-object to
 * our-Gate-object mapping from the content classes.
 *
 * @author echng
 */
public class GateFactory {
	
	/**
	 * The GateSet that the gates will be added to after creation.
	 */
	private GateSet gateColl;
	
	/**
	 * Private so it can only be obtained through newInstance()
	 * 
	 * @param gateColl The GateSet that the gates will be added to after creation.
	 */
	private GateFactory(GateSet gateColl) {
		this.gateColl = gateColl;
	}
	
	/**
	 * Obtains a new GateFactory instance for the given GateSet.
	 * 
	 * @param gateColl The GateSet that the gates will be added to after creation.
	 * @return Returns the new GateFactory instance.
	 */
	public static GateFactory newInstance(GateSet gateColl) {
		return new GateFactory(gateColl);
	}
	
	/**
	 * @return Returns the GateSet that this GateFacotry is creating Gates for.
	 */
	public GateSet getGateSet() {
		return gateColl;
	}
	
	/**
	 * Method to create a method based on the type of the object. The given object
	 * must be one of the auto-generated JAXB objects that corresponds to one of the gate
	 * elements. Once the gate is created, it is automatically added to the GateSet
	 * specified when obtaining the GateFactory object.
	 * 
	 * @param jaxbGate The object to use to create the returned gate.
	 * @return Returns the new gate for the given object. It has already been added to
	 * the GateSet (if it is valid).
	 * @throws InvalidGateDescriptionException Thrown if the gate element isn't valid
	 * according to the specification.
	 * @throws IllegalArgumentException Thrown if the given object does not correspond
	 * to one of the gate elements (that we know how to create).
	 */
	public Gate createAndAddGate(org.flowcyt.facejava.gating.jaxb.AbstractGate jaxbGate) throws InvalidGateDescriptionException, IllegalArgumentException {
		Gate newGate = null;
		
		// XXX: Ugh. If you can think of another way to avoid the typecheck and downcast,
		// please, please (I'm beggin' here) change it.
		//
		// The problem is that the JAXB Gates do not have a common supertype of any use
		// and furthermore, each gate has different needs (parameters) for construction.
		// So even if there was a common supertype it wouldn't help much since it would
		// need to have a way to supply all the different types for all gates and that
		// would result in a brittle superclass.
		//
		// XXX: *****Note: If a new gate type is added here it MUST also be added to 
		//           gating.bool.OperatorFactory.
		if (jaxbGate instanceof org.flowcyt.facejava.gating.jaxb.EllipsoidGate)
			newGate = createGate((org.flowcyt.facejava.gating.jaxb.EllipsoidGate) jaxbGate);
		else if (jaxbGate instanceof org.flowcyt.facejava.gating.jaxb.PolygonGate)
			newGate = createGate((org.flowcyt.facejava.gating.jaxb.PolygonGate) jaxbGate);
		else if (jaxbGate instanceof org.flowcyt.facejava.gating.jaxb.PolytopeGate)
			newGate = createGate((org.flowcyt.facejava.gating.jaxb.PolytopeGate) jaxbGate);
		else if (jaxbGate instanceof org.flowcyt.facejava.gating.jaxb.RectangleGate)
			newGate = createGate((org.flowcyt.facejava.gating.jaxb.RectangleGate) jaxbGate);
		else if (jaxbGate instanceof org.flowcyt.facejava.gating.jaxb.DecisionTreeGate)
			newGate = createGate((org.flowcyt.facejava.gating.jaxb.DecisionTreeGate) jaxbGate);
		else if (jaxbGate instanceof org.flowcyt.facejava.gating.jaxb.BooleanGate)
			newGate = createGate((org.flowcyt.facejava.gating.jaxb.BooleanGate) jaxbGate);
		else
			throw new IllegalArgumentException(jaxbGate.getId() + "(" + jaxbGate.getClass() + ") cannot be created as a gate.");
		
		gateColl.add(newGate);
		return newGate;
	}
	
	// Actual gate-specific creation methods are below ... should be straightforward

	private EllipsoidGate createGate(org.flowcyt.facejava.gating.jaxb.EllipsoidGate jaxbGate) throws InvalidGateDescriptionException {
		return new EllipsoidGate(jaxbGate.getId(), toReferenceList(jaxbGate.getDimension()), jaxbGate.getFocus(), jaxbGate.getDistance());
	}
	
	private PolygonGate createGate(org.flowcyt.facejava.gating.jaxb.PolygonGate jaxbGate) throws InvalidGateDescriptionException {
		return new PolygonGate(jaxbGate.getId(), toReferenceList(jaxbGate.getDimension()), jaxbGate.getVertex());
	}
	
	private PolytopeGate createGate(org.flowcyt.facejava.gating.jaxb.PolytopeGate jaxbGate) throws InvalidGateDescriptionException {
		return new PolytopeGate(jaxbGate.getId(), toReferenceList(jaxbGate.getDimension()), jaxbGate.getPoint());	
	}
	
	private RectangleGate createGate(org.flowcyt.facejava.gating.jaxb.RectangleGate jaxbGate) throws InvalidGateDescriptionException {
		// RectangleGate dimensions also have their range so we need to extract those
		// as well.
		List<RectangleGate.RectangleDimensionRange> ranges = new ArrayList<RectangleGate.RectangleDimensionRange>();
		for (RectangleGateDimension rectDim : jaxbGate.getDimension()) {
			ranges.add(new RectangleGate.RectangleDimensionRange(rectDim.getMin(), rectDim.getMax()));
		}
		
		return new RectangleGate(jaxbGate.getId(), toReferenceList(jaxbGate.getDimension()), ranges);		
	}
	
	private DecisionTreeGate createGate(org.flowcyt.facejava.gating.jaxb.DecisionTreeGate jaxbGate) throws InvalidGateDescriptionException {
		return new DecisionTreeGate(jaxbGate.getId(), jaxbGate.getRootNode());		
	}
	
	private BooleanGate createGate(org.flowcyt.facejava.gating.jaxb.BooleanGate jaxbGate) throws InvalidGateDescriptionException {
		return new BooleanGate(jaxbGate.getId(), OperatorFactory.createOperator(jaxbGate, this));		
	}
	
	/**
	 * Converts a list of Dimensions to a list containing ParameterReferences to the parameters
	 * that define those dimensions (in the same order)
	 * 
	 * @param dimensions The dimensions to be changed.
	 * @return Returns the converted list of ParameterReferences
	 */
	private List<ParameterReference> toReferenceList(List<? extends Dimension> dimensions) {
		List<ParameterReference> rv = new ArrayList<ParameterReference>();
		for (Dimension dim : dimensions) {
			rv.add(new ParameterReference(dim.getParameter()));
		}
		return rv;
	}
}
