package org.flowcyt.facejava.faceflow.relations;

import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;

/**
 * <p>
 * A DataSetRelations object maps an FcsDataSet to the RelationCollection containing the
 * Relations that are associated in some RelationsRepository. To process the 
 * information in the object and its Relations a DataSetRelationsVisitor should be used.
 * However, the FcsDataSet and its Relations can be obtained directly for manual
 * processing, if needed.
 * 
 * @author echng
 */
public class DataSetRelations {
	/**
	 * The data file location of the data file containing the FcsDataSet.
	 */
	private String location;
	
	/**
	 * The FcsDataSet to which the Relations are associated.
	 */
	private FcsDataSet dataSet;
	
	/**
	 * The Relations associated with the FcsDataSet.
	 */
	private RelationCollection relations;
	
	/**
	 * Constructor.
	 * 
	 * @param location The location of the data file (as it is in the
	 * RelationsRepository) that contains the data set
	 * @param dataSet The FcsDataSet that the Relations are associated with.
	 * @param relations The RelationCollection containing the associated Relations.
	 */
	public DataSetRelations(String location, FcsDataSet dataSet, RelationCollection relations) {
		this.location = location;
		this.dataSet = dataSet;
		this.relations = relations;
	}
	
	/**
	 * @return Returns the location of the data file containing the FcsDataSet.
	 */
	public String getDataFileLocation() {
		return location;
	}
	
	/**
	 * @return Returns the FcsDataSet to which the Relations are associated.
	 */
	public FcsDataSet getDataSet() {
		return dataSet;
	}
	
	/**
	 * @return Returns a RelationCollection containing the Relations associated
	 * with the FcsDataSet.
	 */
	public RelationCollection getRelations() {
		return relations;
	}
	
	/**
	 * Accepts a DataSetRelationsVisitor which will process the Relations in
	 * this DataSetRelations.
	 * 
	 * accept() will first sort the Set of Relations according to the RelationOrder
	 * defined by the visitor's getVisitOrder(). Then it will call visitor.startVisit(),
	 * and, in order, visitor.dispatch() for each of the Relations (which will use
	 * reflection to invoke the correct relation-type-specific method in the visitor).
	 * It ends with a call to visitor.endVisit().
	 * 
	 * @param visitor The DataSetRelationsVisitor that is visiting this object.
	 */
	public void accept(DataSetRelationsVisitor visitor) {
		visitor.startVisit(this);
		
		for (Relation rel : relations.applyOrder(visitor.getVisitOrder())) {
			visitor.dispatch(rel);
		}
		
		visitor.endVisit(this);
	}
	
}
