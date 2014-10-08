package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * An abstract super-class which should be extended by any Transformation. This class
 * implements the basic functionality to do with naming.
 * 
 * @author echng
 */
public abstract class AbstractTransformation implements Transformation {
	
	/**
	 * The name of the Transformation.
	 */
	private ParameterReference reference;
	
	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 */
	public AbstractTransformation(String name) {
		this.reference = new ParameterReference(name);
	}
	
	/**
	 * Transformations are identified by their name (from the newName attribute).
	 */
	public ParameterReference getReference() {
		return reference;
	}
	
	public String toString() {
		return "Transformation \"" + reference + "\"";
	}
}
