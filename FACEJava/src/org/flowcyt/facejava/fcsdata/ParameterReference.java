package org.flowcyt.facejava.fcsdata;

/**
 * <p>
 * ParameterReferences are used as a way to identify which Parameters should be used when
 * retrieving data. A ParameterReference is a thin wrapper around a String. The empty
 * string is reserved for use as a reference value for unreferencable ParameterReferences.
 * I.e. Parameters that cannot be referenced must return ParameterReference.UNREFERENCABLE.
 * 
 * <p>
 * ParameterReferences are equal if they have the same reference value which may *not* necessarily
 * result in the same Parameter. The actual Parameter being referenced depends on which 
 * ParameterCollection the reference is passed to. If two different ParameterCollections each
 * have a Parameter that can be referred to by the same reference (same as in object equality,
 * not necessarily reference equality) then the ParameterReference can refer to *both*
 * depending on which collection we use to grab a Parameter.
 *  
 * <p>
 * The main point of the class is to explicitly have Parameters and ParameterReferences as
 * different things. Populations have Parameters through which data can be retrieved but, for
 * example, gating (or compensation or transformation) files only refer to Parameters. However, 
 * the actual Parameter to use when data is required depends on what Population is being operated
 * upon. For gating (and etc.), it can be thought of as two stages, the file itself deals with
 * ParameterReferences which can only be resolved to actual Parameters at runtime (more
 * specifically, when the gate (or its transformation/compensation equivalent) is actually used).  
 * 
 * @author echng
 */
public class ParameterReference {
	/**
	 * The ParameterReference to use for Parameters which cannot be referenced. The 
	 * reference value is the empty string, so if ParameterReferences are created
	 * manually with empty strings as reference values, they will be equal to
	 * this UNREFERENCABLE ParameterReference.
	 */
	public static final ParameterReference UNREFERENCABLE = new ParameterReference("");
	
	/**
	 * The string version of the reference.
	 */
	private String reference;
		
	/**
	 * General Constructor will try to determine if the string can be interpreted as a number.
	 * @param referenceValue The reference as a string.
	 */
	public ParameterReference(String referenceValue) {
		this.reference = referenceValue;
	}
		
	/**
	 * @return Returns the reference value as a string.
	 */
	public String getValue() {
		return reference;
	}
	
	public boolean equals(Object obj) {
		return obj instanceof ParameterReference &&
			this.reference.equals(((ParameterReference)obj).reference);
	}
	
	public int hashCode() {
		return reference.hashCode();
	}
	
	public String toString() {
		return reference;
	}
}
