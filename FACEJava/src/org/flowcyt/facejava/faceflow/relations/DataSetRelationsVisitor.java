package org.flowcyt.facejava.faceflow.relations;

/**
 * <p>
 * A DataSetRelationsVisitor is a RelationVisitor which is specialized for use of
 * processing the data in a DataSetRelations object which is presented by a
 * RelationsRepositoryIterator. It inherits the same dispatch mechanism for
 * arbitrary Relations as RelationVisitor so see its class comments for more info.
 * 
 * @author echng
 */
public abstract class DataSetRelationsVisitor extends RelationVisitor {
	
	/**
	 * @return Returns the RelationOrder which specifies the order in which the 
	 * visitor wishes to visit the Relations in a DataSetRelations.
	 */
	public abstract RelationOrder getVisitOrder();
	
	/**
	 * Called when the visitor first visits a DataSetRelations and before dispatch
	 * has been called for any of the Relations within it.
	 * 
	 * @param relations The DataSetRelations that is going to be visited.
	 * @return An arbitrary return value that is defined by the concrete Visitor 
	 * (use null if it doesn't make sense).
	 */
	public abstract Object startVisit(DataSetRelations relations);
	
	/**
	 * Called when all Relations in the DataSetRelations have been visited.
	 * 
	 * @param relations The DataSetRelations that has been visited.
	 * @return An arbitrary return value that is defined by the concrete Visitor 
	 * (use null if it doesn't make sense).
	 */
	public abstract Object endVisit(DataSetRelations relations);
	
}
