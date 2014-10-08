package org.flowcyt.facejava.fcsdata.exception;

import java.util.Arrays;
import java.util.Collections;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * Thrown if there is a reference collision between two Parameters in the same
 * ParameterCollection or in different ParameterCollections that are used together
 * in the same DataRetriever.
 * 
 * <p>
 * This exception can also handle multiple duplicate ParameterReferences.
 * 
 * @author echng
 */
public class DuplicateParameterReferenceException extends Exception {
	private static final long serialVersionUID = 4265903893186947149L;
	
	private Set<ParameterReference> duplicateRefs;
	
	public DuplicateParameterReferenceException(ParameterReference duplicateRef) {
		super("Duplicate Parameter Name: " + duplicateRef);
		this.duplicateRefs = Collections.singleton(duplicateRef);
	}
	
	public DuplicateParameterReferenceException(Set<ParameterReference> duplicateRefs) {
		super("Duplicate Parameter Names: " + Arrays.toString(duplicateRefs.toArray()));
		this.duplicateRefs = duplicateRefs;
	}
	
	public Set<ParameterReference> getDuplicateParameterReferences() {
		return this.duplicateRefs;
	}
}
