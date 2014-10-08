package org.flowcyt.facejava.fcsdata;

import java.util.Collection;
import java.util.Set;

/**
 * <p>
 * A specialized Collection class which keeps Parameters and can return the correct
 * Parameter that is in the collection and has a given reference. The collection must
 * not allow for the same ParameterReference (except ParameterReference.UNREFERENCABLE)
 * to refer to two different Parameters in the collection.
 * 
 * <p>
 * ParameterCollection takes a type parameter which is constrained to be a subtype of
 * Parameter. This is so ParameterCollections can be declared to hold more specific
 * Parameter types.
 * 
 * <p>
 * Note that order for the Parameters in the collection <i>may</i> matter. So, where
 * possible, Parameters should be used in the order returned by the Collection's
 * iterator. If order does matter, the implementer should also implement List.
 * 
 * <p>
 * ParameterCollections may or may not be unmodifiable. As stated by the Collections
 * framework, modifying methods should throw UnsupportedOperationException.
 * 
 * <p>
 * Unreferencable Parameters (those that return ParameterReference.UNREFERENCABLE as
 * their reference) must not be able to be returned through get(ParameterReference)
 * nor be able to referred to through any method which uses a ParameterReference
 * argument to refer to an actual Parameter (e.g., containsByReference should return
 * false for ParameterReference.UNREFERENCABLE). Unreferencable Parameters can be
 * dealt with by using the actual Parameter object rather than the reference (e.g.,
 * the contains(Object) method from Collection should return true if the argument
 * is an Unreferencable Parameter in the Collection). Unreferencable Parameters should
 * be returned by the Iterator for the collection.
 * 
 * @author echng
 */
public interface ParameterCollection<T extends Parameter> extends Collection<T> {
	
	/**
	 * Determines if a Parameter with the given ParameterReference is in the collection.
	 * Always returns false for ParameterReference.UNREFERENCABLE.
	 * 
	 * @param ref The ParameterReference to check.
	 * @return Returns true iff a Parameter with the given ParameterReference is in the
	 * collection and the reference is not equal to ParameterReference.UNREFERENCABLE.
	 */
	public boolean containsByReference(ParameterReference ref);
	
	/**
	 * @param reference The ParameterReference to find a Parameter for.
	 * @return Returns the Parameter that's being referenced. Returns null if no
	 * Parameter is in the collection with the given reference (i.e., reference is not in 
	 * the set returned by getParameterReferences()). If reference is equal to 
	 * ParameterReference.UNREFERENCABLE, the ParameterCollection must return
	 * null, and not any unreferencable Parameter it may contain.
	 */
	public T get(ParameterReference reference);

	/**
	 * @return Returns a Set containing all possible ParameterReferences for which a
	 * non-null Parameter will be returned when called as an argument to getParameter(). 
	 * ParameterReference.UNREFERENCABLE must not be in the returned set as a Parameter
	 * can never be returned for it with getParameter().
	 */
	public Set<ParameterReference> getParameterReferences();
}
