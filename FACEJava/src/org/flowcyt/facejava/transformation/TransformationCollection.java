package org.flowcyt.facejava.transformation;

import java.util.AbstractCollection;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.ParameterCollection;
import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * A ParameterCollection which stores Transformations. TransformationCollection is
 * modifiable and supprots addition and removal.
 * 
 * <p>
 * Although TransformationCollection does not allow Transformations that have the
 * same ParameterReference as one already in the collection to be added (by the
 * ParameterCollection contract), it does not throw an Exception when the Constructor
 * that takes a Collection is used (and there is a duplicate Reference) since the
 * Collection does not explicitly represent the Transformations in a Transformation-ML
 * file (since it's modifiable in can be used for other purposes).
 * 
 * <p>
 * Note: Transformations are only checked for circular dependency when the collection
 * is given to a DataRetriever since they may depend on Parameters not in this
 * collection.
 * 
 * @author echng
 */
public class TransformationCollection extends AbstractCollection<Transformation> implements ParameterCollection<Transformation> {
	/**
	 * Maps the tranformation's newName attribute (i.e., its name) to the
	 * Transformation with that name. May not contain all Transformations in the
	 * Collection (ther are all in the Set, however), since some Transformations
	 * may be unreferencable. 
	 */
	private Map<ParameterReference, Transformation> refToTransformationMap;
	
	/**
	 * The Set containing all added Transformations.
	 */
	private Set<Transformation> transformations;
	
	/**
	 * Constructor. Creates an empty TransformationCollection.
	 */
	public TransformationCollection() {
		this.refToTransformationMap = new HashMap<ParameterReference, Transformation>();
		this.transformations = new HashSet<Transformation>();
	}
	
	/**
	 * Constructor. Creates a TransformationCollection containing the Transformations
	 * in the given Collection. If there are multiple Transformations with equal
	 * ParameterReferences only one of the Transformations will be in the created
	 * collection.
	 * 
	 * @param coll A Collection containing the Transformations that will be in the
	 * new Collection.
	 */
	public TransformationCollection(Collection<? extends Transformation> coll) {
		this();
		this.addAll(coll);
	}
	
	/**
	 * Nulls are not allowed to be added and a NullPointerExcception is thrown. 
	 * 
	 * If a Transformation with the same ParameterReference as the given
	 * Transformation already exists in the collection, the given Transformation
	 * not added and false is returned.
	 * 
	 * Unreferencable Transformations are added but will not be able to be looked
	 * up/removed by their reference.
	 */
	public boolean add(Transformation trans) {
		if (refToTransformationMap.containsKey(trans.getReference()))
			return false;
		
		transformations.add(trans);
		if (!trans.getReference().equals(ParameterReference.UNREFERENCABLE))
			refToTransformationMap.put(trans.getReference(),trans);
		return true;
	}
	
	public boolean contains(Object o) {
		return o != null && 
			transformations.contains(o);
	}
	
	public boolean remove(Object o) {
		if (transformations.remove(o)) {
			refToTransformationMap.remove(((Transformation)o).getReference());
			return true;
		}
		return false;
	}
	
	@Override public Iterator<Transformation> iterator() {
		return new TransformationCollectionIterator();
	}

	@Override public int size() {
		return transformations.size();
	}
	
	/**
	 * Removes the Transformation with the given ParameterReference from the collection
	 * if it is in it. If the given reference is equal to
	 * ParameterReference.UNREFERENCABLE, nothing is removed (use remove(Object) if
	 * you want to remove an unreferencable Transformation).
	 * 
	 * @param ref The reference of the Parameter to be removed
	 * @return Returns true iff a Transformation was removed.
	 */
	public boolean removeByReference(ParameterReference ref) {
		if (!refToTransformationMap.containsKey(ref))
			return false;
		
		return remove(refToTransformationMap.get(ref));
	}

	public boolean containsByReference(ParameterReference ref) {
		return refToTransformationMap.containsKey(ref);
	}
	
	public Set<ParameterReference> getParameterReferences() {
		return refToTransformationMap.keySet();
	}
	
	public Transformation get(ParameterReference reference) {
		if (reference.equals(ParameterReference.UNREFERENCABLE))
    		return null;
    	
    	return refToTransformationMap.get(reference);
	}
	
	/**
	 * An Iterator class for TransformationCollection. We need special code for
	 * remove() to remove the Transformation from both the set and the lookup Map.
	 * It wraps the Set's iterator and uses it for next() and hasNext() but uses
	 * the Collection's remove() method for remove().
	 * 
	 * @author echng
	 */
	private class TransformationCollectionIterator implements Iterator<Transformation> {
		/**
		 * The iterator through the transformations Set.
		 */
		private Iterator<Transformation> wrappedIter = transformations.iterator();
		
		/**
		 * The last Transformation returned by next(). Need to save it for remove()
		 * to work. If null, then remove() is not valid (either it was already removed
		 * or next() has not been called).
		 */
		private Transformation last;
		
		public boolean hasNext() {
			return wrappedIter.hasNext();
		}

		public Transformation next() {
			last = wrappedIter.next();
			return last;
		}

		public void remove() {
			if (last == null) {
				throw new IllegalStateException();
			}
			TransformationCollection.this.remove(last);
			last = null;
		}		
	}
}
