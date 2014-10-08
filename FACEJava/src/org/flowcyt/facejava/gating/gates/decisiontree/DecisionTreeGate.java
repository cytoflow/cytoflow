package org.flowcyt.facejava.gating.gates.decisiontree;

import java.util.Collections;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.gates.AbstractGate;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.jaxb.LeafNode;
import org.flowcyt.facejava.gating.jaxb.TreeNode;

/**
 * <p>
 * Implements decision tree gates as defined by the specification. An event is inside the
 * decision tree if the leaf node that is reached by traversing the tree has an inside
 * attribute that is true. The tree is traversed by comparing the event's value for the
 * parameter to the threshold, both of which are specified at each non-leaf node. If
 * the event's value is less than the threshold, the "Less Than" branch is taken, 
 * otherwise the "Greater Than Or Equal" branch is taken.
 * 
 * @author echng
 */
public class DecisionTreeGate extends AbstractGate {
	
	/**
	 * We'll simply use the JAXB representation since it is (reasonably) suited for 
	 * our purposes and easy to traverse the tree.
	 */
	private TreeNode root;
	
	/**
	 * Constructor. Creates a Decision Tree Gate.
	 * 
	 * @param gateId The Gate's id.
	 * @param rootNode The root node of the decision tree.
	 */
	public DecisionTreeGate(String gateId, TreeNode rootNode) {
		super(gateId);
		this.root = rootNode;
	}

	/**
	 * An event is inside the decision tree if the leaf node that is reached by 
	 * traversing the tree has an inside attribute that is true. The tree is traversed
	 * by comparing the event's value for the parameter to the threshold, both of
	 * which are specified at each non-leaf node. If the event's value is less than
	 * the threshold, the "Less Than" branch is taken, otherwise the "Greater Than Or
	 * Equal" branch is taken.
	 */
	public boolean isInside(Event ev, DataRetriever retriever) throws DataRetrievalException {
		TreeNode curr = root;
		LeafNode leaf = null;
		while (leaf == null) {
			double data = retriever.getScale(new ParameterReference(curr.getParameter()), ev);
			// One and only one of leaf or node can be set for LessThan and for 
			// GreaterThanOrEqual. This should be validated by the schema when JAXB
			// unmarshals it.
			if (data >= curr.getThreshold()) {
				if (curr.getNodeGTE() != null)
					curr = curr.getNodeGTE();
				else
					leaf = curr.getLeafGTE();
			} else {
				if (curr.getNodeLT() != null)
					curr = curr.getNodeLT();
				else
					leaf = curr.getLeafLT();				
			}
		}
		return leaf.isInside();
	};
	
	public void validate() {
		// If the decision tree gate passed schema validation then there are no other
		// requirements to be checked.
	}
	
	public Set<Gate> getDirectDependencies() {
		return Collections.emptySet();
	}
	
	public String toString() {
		// This may be a bit much for a toString but it is useful for debugging
		// ... and I don't think we;'ll be printing gates anytime soon.
		StringBuilder builder = new StringBuilder();
		builder.append("Decision Tree ");
		builder.append(super.toString());
		builder.append("\n");
		toStringHelper(builder, root, 0, true, false);
		return builder.toString();
	}
	
	/**
	 * A recursive helper function that traverses the tree and makes a string description
	 * for it.  
	 * @param builder The StringBuilder that is used as an accumulator to build the
	 * string representation. It will contain the final result.
	 * @param current The current node we are going to add to the StringBuilder
	 * @param tabLevel The number of tabs to prepend to the line. Indicates the depth
	 * in the tree.
	 * @param isRoot Is true if current is the root node.
	 * @param isLessThanNode Is true if current was reached through the Less Than
	 * branch. (This value is ignored if isRoot is true.) 
	 */
	private void toStringHelper(StringBuilder builder, TreeNode current, int tabLevel, boolean isRoot, boolean isLessThanNode) {
		for (int i = 0; i < tabLevel; ++i) 
			builder.append("  ");
		
		// How to abuse the ternary operator...
		builder.append(isRoot ? "Root -- " : (isLessThanNode ? "< -- " : ">= -- "));
		builder.append("Parameter: ");
		builder.append(current.getParameter());
		builder.append("; Threshold: ");
		builder.append(current.getThreshold());
		builder.append("\n");
		
		if (current.getNodeLT() != null) {
			toStringHelper(builder, current.getNodeLT(), tabLevel + 1, false, true);
		} else {
			for (int i = 0; i < tabLevel + 1; ++i) 
				builder.append("  ");
			builder.append("< Leaf -- Inside: ");
			builder.append(current.getLeafLT().isInside());
			builder.append("\n");
		}
		
		if (current.getNodeGTE() != null) {
			toStringHelper(builder, current.getNodeGTE(), tabLevel + 1, false, false);
		} else {
			for (int i = 0; i < tabLevel + 1; ++i) 
				builder.append("  ");
			builder.append(">= Leaf -- Inside: ");
			builder.append(current.getLeafGTE().isInside());
			builder.append("\n");
		}
	}
}
