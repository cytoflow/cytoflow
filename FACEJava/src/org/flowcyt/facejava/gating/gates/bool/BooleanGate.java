package org.flowcyt.facejava.gating.gates.bool;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import java.util.Stack;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.gates.AbstractGate;
import org.flowcyt.facejava.gating.gates.Gate;

/**
 * <p>
 * Implements a BooleanGate as defind by the specification. An event is inside the 
 * BoooleanGate if the boolean operation (and, or, not) of the boolean gate is true
 * for the event.    
 * 
 * <p>
 * BooleanGates cannot have circular dependencies where the gate depends (even indirectly)
 * on itself. That is, in the dependecy graph where a directed edge [u, v] exists between
 * gates u and v if and only if u depends on v, there can be no cycle.  
 *
 * <p>
 * BooleanGates are defined in terms of other gates. Thus, when loading from a Gating-ML
 * file, they cannot be validated until all other gates that it refers to are also
 * loaded (if creating programmatically, it should be easy to sequence the creations so
 * that this doesn't matter).
 * 
 * 
 * @author echng
 */
public class BooleanGate extends AbstractGate {
	
	/**
	 * The boolean operator used by the gate.
	 */
	private BooleanGateOperator operator;
	
	/**
	 * Creates a BooleanGate. Note that unlike some other Gate tyeps, BooleanGates
	 * are not validated upon construction since it may refer to gates that aren't
	 * yet loaded. validate() should be called manually when all Gates are finished
	 * loading.
	 * 
	 * @param gateId The gate's id.
	 * @param operator The BooleanGateOperator that defines the boolean operation to
	 * be performed upon the operand gates.
	 */
	public BooleanGate(String gateId, BooleanGateOperator operator) {
		super(gateId);
		this.operator = operator;
	}
	
	public void validate() throws InvalidGateDescriptionException {
		Stack<Gate> workingPath = new Stack<Gate>();
		if (dependencyCycleCheck(this, workingPath)) {
			// If there's a cycle, rebuild it to tell the user.
			Gate cycleGate = workingPath.pop();
			String message = cycleGate.getId();
			while (!workingPath.empty()) {
				Gate previousGate = workingPath.pop();
				message = previousGate.getId() + " -> " + message;
				if (previousGate.equals(cycleGate))
					break;
			}
			message = "Gate Dependency Cycle found: " + message;
			throw new InvalidGateDescriptionException(this.getId(), message);
		}
	}
	
	/**
	 * Checks if the BooleanGate has a cycle in its dependencies. It is a recursive helper
	 * function. It performs a simple Depth First Search through the dependency graph 
	 * to find cycles. 
	 *  
	 * @param currentGate The current Gate that is the last gate on the current path 
	 * through the graph.
	 * @param pathToCurrentGate The path starting from this BooleanGate (bottom of the
	 * stack) to the Gate that is before the current Gate on the current path (top of
	 * the stack).
	 * @return Returns true if a cycle was found. The path to currentGate will contain
	 * the cycle at the top of the stack (that is, the gate at the top of the stack
	 * appears somewhere else in the stack and the gates in between the two occurrences
	 * form the cycle). 
	 * @throws InvalidGateDescriptionException 
	 */
	private boolean dependencyCycleCheck(Gate currentGate, Stack<Gate> pathToCurrentGate) throws InvalidGateDescriptionException {
		// If we've already visited the gate on the current path, it's a cycle.
		if (pathToCurrentGate.contains(currentGate)) {
			// Push it on so we know which gate started the cycle. 
			pathToCurrentGate.push(currentGate);
			return true;
		}
		
		if (currentGate.getDirectDependencies().size() > 0) {
			// Push it on since we'll be travelling down to any Gates the current gate depends
			// on.
			pathToCurrentGate.push(currentGate);
			for (Gate dependency : currentGate.getDirectDependencies()) {
				// Recursively check the dependency to see if there's a cycle. If one is
				// found we can stop our check and return.
				if (dependencyCycleCheck(dependency, pathToCurrentGate))
					return true;
			}
			// No cycles were found branching out from the current gate, so remove it from
			// the current path and backtrack to the previous gate.
			pathToCurrentGate.pop();
		}
		
		return false;
	}

	/**
	 * An event is inside the BoooleanGate if the boolean operation (and, or, not) of
	 * the boolean gate is true for the event. 
	 */
	public boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException {
		return operator.isTrue(ev, retriever);
	}
	
	public Set<Gate> getDirectDependencies() {
		return Collections.unmodifiableSet(new HashSet<Gate>(operator.getOperands()));
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("Boolean ");
		builder.append(super.toString());
		builder.append("\n");
		builder.append(operator.toString());
		builder.append("\n");
		return builder.toString();
	}
	
}
