package org.flowcyt.facejava.faceflow.relations;

import java.util.AbstractCollection;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

/**
 * <p>
 * A Collection class for storing a set of Relations. The class performs duplicate
 * checking on the relations when being added and will never contain a duplicate
 * Relation when that type of Relation does not allow duplicates.
 * 
 * <p>
 * Although Relations are naturally unordered, an order may be applied to the
 * Relations in the collection by using applyOrder() which will return the
 * ordered result as a List. 
 * 
 * <p>
 * Note that this class is not meant for general purpose use for storing Relations by
 * clients. Clients should be using RelationsRepository. It is only meant to be used
 * as a container for Relations when they are returned by RelationsRepository and as a 
 * helper class for implementations of RelationsRepository.
 * 
 * <p>
 * The Collection does not support the remove() method. add() is supported though
 * (but with duplicate checking).
 * 
 * @author echng
 */
public class RelationCollection extends AbstractCollection<Relation> {
	/**
	 * Holds the added Relations.
	 */
	private Set<Relation> relations = new HashSet<Relation>();
	
	/**
	 * Keeps track of the Classes of the Relations that have been added. Used
	 * to perform duplicate checks.
	 */
	private Set<Class<? extends Relation>> addedRelationTypes = new HashSet<Class<? extends Relation>>();
	
	/**
	 * Adds the Relation to the collection. If the relation does not allow
	 * duplicates, it will only be added if a Relation of the same type has
	 * not already been added.
	 * 
	 * @param rel The Relation to add.
	 * @return Reeturns true if the Relation was added and false if the Relation
	 * does not allow duplicates but a Relation of the same type has already been
	 * added.
	 */
	public boolean add(Relation rel) {
		if (!rel.duplicatesAllowed() && addedRelationTypes.contains(rel.getClass())) {
			return false;
		}
		
		relations.add(rel);
		addedRelationTypes.add(rel.getClass());
		return true;
	}
	
	@Override public boolean contains(Object obj) {
		return relations.contains(obj);
	}

	/**
	 * The returned iterator does not support removal.
	 */
	@Override public Iterator<Relation> iterator() {
		return new RelationIterator();
	}

	@Override public int size() {
		return relations.size();
	}
	
	/**
	 * Applys an ordering to the Relations in the collection and returns the result
	 * as a List containing the Relations in the correct order.
	 * 
	 * @param order The RelationOrder to use to order the Relations.
	 * @return Returns a List containing all the Relations in the collection sorted
	 * according to the given RelationOrder.
	 */
	public List<Relation> applyOrder(RelationOrder order) {
		List<Relation> rv = new ArrayList<Relation>(relations);
		Collections.sort(rv, order);
		return rv;
	}
	
	/**
	 * Merges this RelationCollection with another to produce a new Relation
	 * Collection. The Relations in this collection take precedence over the
	 * Relations in the other collection, i.e., if there is a Relation in the other
	 * collection which has the same type as one in this collection, it is not added
	 * to the returned collection.  
	 * 
	 * @param mergedColl The collection to merge into this one.
	 * @return Returns a new RelationCollection containing the Relations in this
	 * collection merged with those in the other collection.
	 */
	public RelationCollection merge(RelationCollection mergedColl) {
		RelationCollection rv = new RelationCollection();
		rv.relations = new HashSet<Relation>(this.relations);
		rv.addedRelationTypes = new HashSet<Class<? extends Relation>>(this.addedRelationTypes);
		
		for (Relation mergedRel : mergedColl) {
			if (!this.addedRelationTypes.contains(mergedRel.getClass()))
				rv.add(mergedRel);
		}
		
		return rv;
	}
	
	/**
	 * A simple wrapper class for the iterator of the internal Set of Relations.
	 * Removal is not supported so we need to override the default behavior for the
	 * Set's iterator.
	 * 
	 * @author echng
	 */
	private class RelationIterator implements Iterator<Relation> {
		private Iterator<Relation> setIterator;
		
		public RelationIterator() {
			setIterator = relations.iterator();
		}

		public boolean hasNext() {
			return setIterator.hasNext();
		}

		public Relation next() {
			return setIterator.next();
		}

		public void remove() {
			throw new UnsupportedOperationException("remove() not supported by RelationCollection.");			
		}		
	}
}
