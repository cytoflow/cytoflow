package org.flowcyt.facejava.gating.xmlio;

import java.util.ArrayList;
import java.util.List;

import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.bool.AndOperator;
import org.flowcyt.facejava.gating.gates.bool.BooleanGateOperator;
import org.flowcyt.facejava.gating.gates.bool.NotOperator;
import org.flowcyt.facejava.gating.gates.bool.OrOperator;
import org.flowcyt.facejava.gating.gates.bool.ProxyGate;
import org.flowcyt.facejava.gating.jaxb.BooleanGate;
import org.flowcyt.facejava.gating.jaxb.GateReference;
import org.flowcyt.facejava.gating.jaxb.OneOperandBoolGate;
import org.flowcyt.facejava.gating.jaxb.TwoAndMoreOperandsBoolGate;

/**
 * <p>
 * Responsible for creating BooleanGateOperators from the JAXB BooleanGate.
 *  
 * @author echng
 */
public class OperatorFactory {
	// XXX: This is pretty ugly. Play "Count the if-else-ifs" and "Find the typecheck
	// and downcast" (and "Where in the code this was copied from" -- Answer: Gatefactory)
	// to see why. 
	//   - JAXB gate elements have no (useful) common supertype. Thus we get that...
	//       - ... for one operand gates we have to check each of the possible JAXB gates
	//         it could be to find the non-null element (and there is only one). Thus, the
	//         if-else-ifs.
	//       - ... for two or more operand gates there is no way to distinguish between
	//         a gate and a gateReference since we are only given a list of Objects (nor 
	//         if it is actually a gate or gateReference element). Thus, we rely on the
	//         exception that GateFactory throws to determine if the object was not a JAXB
	//         gate element. If not, then we must try to cast it as a GateReference.
	//   - Operators have no common supertype. Thus the if-else-ifs to determine which 
	//     of the operators are actually specified in the JAXB gate.
	// If any one can figure out how to avoid any of that crap, please fix it.
	//
	// (Somewhat) luckily, all the crap is isolated in this class (and in GateFactory) 
	// to avoid contaminating the content classes.
	
	/**
	 * Creates the correct BooleanGateOperator used by the given JAXB BooleanGate. 
	 * 
	 * @param jaxbGate The JAXB BooleanGate that contains the operator to be created.
	 * @param factory The GateFactory to use to create any gates defined within the 
	 * jaxb element.
	 * @return Returns the new BooleanGateOperator.
	 * @throws InvalidGateDescriptionException Thrown if one of the gates defined within
	 * the BooleanGate is invalid with respect to the specification.
	 */
	public static BooleanGateOperator createOperator(BooleanGate jaxbGate, GateFactory factory) throws InvalidGateDescriptionException {
		BooleanGateOperator operator;
		try {
			// Find the not null operator.
			if (jaxbGate.getNot() != null)
				operator = createNotOperator(jaxbGate.getNot(), factory);
			else if (jaxbGate.getOr() != null)
				operator = createOrOperator(jaxbGate.getOr(), factory);
			else if (jaxbGate.getAnd() != null)
				operator = createAndOperator(jaxbGate.getAnd(), factory);
			else 
				throw new InvalidGateDescriptionException(jaxbGate.getId(), "Boolean Gate missing one of <and>, <or> or <not>.");
		} catch (IllegalArgumentException e) {
			throw new InvalidGateDescriptionException(jaxbGate.getId(), e.getMessage());
		}
		return operator;
	}
	
	/**
	 * Creates a NotOperator from the given JAXB element.
	 * 
	 * @param jaxbOperator The jaxb element to use.
	 * @param factory The GateFactory to use to create any gates defined within the 
	 * jaxb element.
	 * @return Returns the new NotOperator.
	 * @throws InvalidGateDescriptionException Thrown if one of the gates defined within
	 * the BooleanGate is invalid with respect to the specification.
	 */
	private static NotOperator createNotOperator(OneOperandBoolGate jaxbOperator, GateFactory factory) throws IllegalArgumentException, InvalidGateDescriptionException {
		
		// Let's play a little game called "Find The Non-Null Gate."
		// XXX: Any new gate types must be added here.
		Object gateOrReference;
		if (jaxbOperator.getGateReference() != null)
			gateOrReference = jaxbOperator.getGateReference();
		else if (jaxbOperator.getBooleanGate() != null)
			gateOrReference = jaxbOperator.getBooleanGate();
		else if (jaxbOperator.getDecisionTreeGate() != null)
			gateOrReference = jaxbOperator.getDecisionTreeGate();
		else if (jaxbOperator.getEllipsoidGate() != null)
			gateOrReference = jaxbOperator.getEllipsoidGate();
		else if (jaxbOperator.getRectangleGate() != null)
			gateOrReference = jaxbOperator.getRectangleGate();
		else if (jaxbOperator.getPolygonGate() != null)
			gateOrReference = jaxbOperator.getPolygonGate();
		else if (jaxbOperator.getPolytopeGate() != null)
			gateOrReference = jaxbOperator.getPolytopeGate();
		else
			throw new IllegalArgumentException("Does not contain a gateReference nor any Gate element");
		
		return new NotOperator(getOperand(gateOrReference, factory)); 		
	}
	
	/**
	 * Creates an AndOperator from the given JAXB element.
	 * 
	 * @param jaxbOperator The jaxb element to use.
	 * @param factory The GateFactory to use to create any gates defined within the 
	 * jaxb element.
	 * @return Returns the new AndOperator.
	 * @throws InvalidGateDescriptionException Thrown if one of the gates defined within
	 * the BooleanGate is invalid with respect to the specification.
	 */
	private static AndOperator createAndOperator(TwoAndMoreOperandsBoolGate jaxbOperator, GateFactory factory) throws InvalidGateDescriptionException {
		return new AndOperator(
				makeOperandList(
						jaxbOperator.getGateReferenceOrRectangleGateOrPolygonGate(),
						factory));
	}
	
	/**
	 * Creates an OrOperator from the given JAXB element.
	 * 
	 * @param jaxbOperator The jaxb element to use.
	 * @param factory The GateFactory to use to create any gates defined within the 
	 * jaxb element.
	 * @return Returns the new OrOperator.
	 * @throws InvalidGateDescriptionException Thrown if one of the gates defined within
	 * the BooleanGate is invalid with respect to the specification.
	 */
	private static OrOperator createOrOperator(TwoAndMoreOperandsBoolGate jaxbOperator, GateFactory factory) throws InvalidGateDescriptionException {
		return new OrOperator(
				makeOperandList(
						jaxbOperator.getGateReferenceOrRectangleGateOrPolygonGate(),
						factory));
	}
	
	/**
	 * Process the List of objects that should contain only jaxb gates or gateReferences
	 * and obtain the real objects.
	 * 
	 * @param input The input list of gates or gate references.
	 * @param factory The GateFactory used to create any JAXB gates that are defined
	 * within the Boolean Gate.
	 * @return A List that will contain all the Gates to use as operands. Any Gates
	 * defined within the boolean gate will have been created by the GateFactory and
	 * added to its GateSet. ProxyGates will be in the list for any gateReferences.
	 * @throws InvalidGateDescriptionException Thrown if one of the gates defined within
	 * the BooleanGate is invalid with respect to the specification.
	 * @throws IllegalArgumentException Thrown if one of the objects in the input list
	 * is not a JAXB gate element nor a gateReference element.
	 */
	private static List<Gate> makeOperandList(List<Object> input, GateFactory factory) throws InvalidGateDescriptionException {
		List<Gate> rv = new ArrayList<Gate>();
		for (Object gateOrReference : input) {
			rv.add(getOperand(gateOrReference, factory));
		}
		return rv;
	}
	
	/**
	 * Returns the appropriate Gate to use as an operand. If gateOrReference is a 
	 * JAXB gate, the GateFactory is used to create and add the corresponding Gate
	 * then the created Gate is returned. If gateOrReference is a GateReference,
	 * a ProxyGate is created for it and returned.
	 * 
	 * @param gateOrReference Must be either a JAXB AbstractGate or a GateReference
	 * @param factory The GateFactory to use to create a Gate from the JAXB Gate.
	 * @return Returns the Gate to use as an operand.
	 * @throws InvalidGateDescriptionException Thrown if the gate defined within
	 * the BooleanGate is invalid with respect to the specification.
	 * @throws IllegalArgumentException Thrown if one of the objects in the input list
	 * is not a JAXB gate element nor a gateReference element.
	 */
	private static Gate getOperand(Object gateOrReference, GateFactory factory) throws InvalidGateDescriptionException, IllegalArgumentException {
		if (gateOrReference instanceof org.flowcyt.facejava.gating.jaxb.AbstractGate)
			return factory.createAndAddGate((org.flowcyt.facejava.gating.jaxb.AbstractGate)  gateOrReference);
		else if (gateOrReference instanceof GateReference)
			return new ProxyGate(getIdOfReference((GateReference) gateOrReference), factory.getGateSet());
		else
			throw new IllegalArgumentException(gateOrReference.getClass() + " is neither a gateReference element nor a Gate element");			
	}
	
	/**
	 * Determines which JAXB gate the gateReference refers to and returns the id of that
	 * gate.
	 *  
	 * @param ref The GateReference to get the gate id for.
	 * @return Returns the id of the referenced gate.
	 * @throws IllegalArgumentException Thrown if the gateReference does not refer to
	 * a JAXB gate.
	 */
	private static String getIdOfReference(GateReference ref) {
		Object obj = ref.getRef();
		
		String id;
		
		if (obj instanceof org.flowcyt.facejava.gating.jaxb.AbstractGate)
			id = ((org.flowcyt.facejava.gating.jaxb.AbstractGate) obj).getId();
		else 
			throw new IllegalArgumentException(obj.getClass() + " -- Not a reference to a Gate element");
		return id;
	}
}
