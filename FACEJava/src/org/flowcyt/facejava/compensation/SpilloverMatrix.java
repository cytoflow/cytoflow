package org.flowcyt.facejava.compensation;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * Stores the spillover coefficients specified in one spilloverMatrix
 * element in a Compensation-ML file.
 * 
 * From the standard:
 * 
 * <pre>
 * &lt;spillover parameter="X"&gt;
 *   ...
 *   &lt;coefficient parameter="Y" value="V" /&gt;
 *   ...
 * &lt;/spillover&gt;
 * </pre>
 * 
 * <p>
 * The semantic of this entry is that V is the ratio of the amount of X signal in the Y channel
 * to the amount of X signal in the X channel for an X-stained cell (V is called the spillover
 * coefficient between X and Y).
 * 
 * <p>
 * This example (specifically the names X, Y and V) is used in the rest of the comments.
 * 
 * <p>
 * This relation is not symmetric so order matters (i.e., which parameter is in the spillover
 * element and which is in the coefficient element).
 * 
 * <p>
 * <b>Note:</b> The SpilloverMatrix only maps ParameterReferences to their spillover value,
 * not actual FcsParameters. The actual FcsParameters can only be determined when an actual
 * FcsDataSet is compensated.
 * 
 * A SpilloverMatrix is equal to another SpilloverMatrix if their ids are equal, since
 * ids must be unique (wrt some SpilloverMatrixSet).
 * 
 * @author echng
 */
public class SpilloverMatrix {
	
	/**
	 * The default spillover for any two parameters X, Y when the spillover coefficient
	 * between X and Y (i.e., X is in spillover and Y is in coefficient) is not
	 * specified and X != Y.
	 */
	private static final double DEFAULT_SPILLOVER = 0;
	
	/**
	 * The default spillover for a parameter X and itself (i.e., X is in spillover and X
	 * is in coefficient) when the coefficient is not specified. 
	 */
	private static final double DEFAULT_SELF_SPILLOVER = 1;
	
	/**
	 * The id of the spilloverMatrix element.
	 */
	private String id;
	
	/**
	 * This data structure stores the spillover coefficient V between parameters X and Y
	 * by using the ordered pair (X, Y) as the key and V as the value in the map.
	 */
	private Map<ParameterReferenceOrderedPair, Double> spilloverMap;
	
	/**
	 * A set containing all the parameter references that were part of any spillover
	 * coefficient (i.e., any parameter references that appeared as either X or Y). 
	 */
	private Set<ParameterReference> specifiedParameterReferences;
	
	/**
	 * Creates a new empty SpilloverCoefficients object with the given id.
	 * @param id The id for the object from the XMl file.
	 */
	public SpilloverMatrix(String id) {
		this.id = id;
		
		spilloverMap = new HashMap<ParameterReferenceOrderedPair, Double>();
		specifiedParameterReferences = new HashSet<ParameterReference>();
	}
	
	/**
	 * @return Returns the id.
	 */
	public String getId() {
		return id;
	}
	
	/**
	 * Sets the spillover value between parameterReference and otherParameterReference
	 * (where firstReference is X and secondParameterRefernce is Y) to be the given value
	 * (V).
	 * 
	 * @param firstReference Corresponds to X. That is, the parameter in the spillover
	 * element.
	 * @param secondReference Corresponds to Y. That is, the parameter in the
	 * coefficient element.
	 * @param spillover The spillover coefficient (V) between parameterReference and
	 * otherParameterReference.
	 */
	public void setSpilloverValue(ParameterReference firstReference, ParameterReference secondReference, double spillover) {
		ParameterReferenceOrderedPair key = new ParameterReferenceOrderedPair(firstReference, secondReference);
		spilloverMap.put(key, spillover);
		
		specifiedParameterReferences.add(firstReference);
		specifiedParameterReferences.add(secondReference);
	}
	
	/**
	 * <p>  
	 * The spillover coefficient between X and Y is determined as follows:
	 * <ul>
	 * <li>If it was specified through setSpilloverValue() with X as parameterReference and
	 *   Y as otherParameterReference then that value is returned.
	 * <li>If X = Y, the spillover coefficient defaults to DEFAULT_SELF_SPILLOVER  (= 1).
	 * <li>otherwise, the spillover coefficient defaults to DEFAULT_SPILLOVER (= 0).
	 * </ul> 
	 * 
	 * @param firstReference Corresponds to X. That is, the parameter in the spillover
	 * element.
	 * @param secondReference Corresponds to Y. That is, the parameter in the
	 * coefficient element.
	 * @return Returns the spillover coefficient (V) between parameterReference and
	 * otherParameterReference. Note that by the specification, V exists for *any* two
	 * parameters X and Y, even if it was not specified through a call to 
	 * setSpilloverValue().
	 */
	public double getSpilloverValue(ParameterReference firstReference, ParameterReference secondReference) {
		ParameterReferenceOrderedPair key = new ParameterReferenceOrderedPair(firstReference, secondReference);
		
		if (!spilloverMap.containsKey(key)) {
			if (firstReference.equals(secondReference))
				return DEFAULT_SELF_SPILLOVER;
		
			return DEFAULT_SPILLOVER;
		}
		
		return spilloverMap.get(key);
	}
	
	/**
	 * @return Returns an unmodifiable set containing all the parameter references that
	 * were given as either parameter reference parameter in setSpilloverValue().
	 */
	public Set<ParameterReference> getSpecifiedParameterReferences() {
		return Collections.unmodifiableSet(specifiedParameterReferences);
	}
	
	public boolean equals(Object other) {
		return other instanceof SpilloverMatrix && this.getId().equals(((SpilloverMatrix)other).getId());		
	}
	
	public int hashCode() {
		return id.hashCode();
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("Spillover Matrix ");
		builder.append(this.getId());
		builder.append("\n\t");
		
		List<ParameterReference> params = new ArrayList<ParameterReference>(getSpecifiedParameterReferences());
		for (ParameterReference param : params) {
			builder.append(param);
			builder.append("\t");
		}
		builder.append("\n");
		
		for (ParameterReference param : params) {
			builder.append(param);
			
			for (ParameterReference otherParam : params) {
				builder.append("\t");
				builder.append(getSpilloverValue(param,  otherParam));
			}
			builder.append("\n");
		}
		
		return builder.toString();
	}
	
	/**
	 * An internal class used as a key to map pairs of ParameterReferences to their spillovers.
	 * The pairs are equals if their first references are equal and the second references are
	 * equal.
	 * 
	 * @author echng
	 */
	private static class ParameterReferenceOrderedPair {
		private ParameterReference firstRef;
		
		private ParameterReference secondRef;
		
		public ParameterReferenceOrderedPair(ParameterReference firstRef, ParameterReference secondRef) {
			this.firstRef = firstRef;
			this.secondRef = secondRef;
		}
		
		public boolean equals(Object other) {
			if (other instanceof ParameterReferenceOrderedPair) {
				ParameterReferenceOrderedPair otherPair = (ParameterReferenceOrderedPair) other;
				return this.firstRef.equals(otherPair.firstRef) && 
						this.secondRef.equals(otherPair.secondRef);
			}
			return false;
		}
		
		public int hashCode() {
			return firstRef.hashCode() ^ secondRef.hashCode();
		}
	}
}
