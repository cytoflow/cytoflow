package org.flowcyt.facejava.faceflow.exception;

import org.flowcyt.facejava.faceflow.relations.Relation;

/**
 * <p>
 * Thrown by RelationRepositories when it determines that there are multiple
 * Relations of the same type, which does not allow duplicates, associated with either
 * a data file or a data set within a data file. This Exception can be thrown either
 * when adding a new Relation or when Relations are being retrieved. 
 * 
 * @author echng
 */
public class DuplicateRelationException extends Exception {
	private static final long serialVersionUID = 7353144672851179668L;
	
	/**
	 * Constructor. Used when the duplicate Relations are associated with the whole
	 * data file.
	 *  
	 * @param location The data file location.
	 * @param type The Class of Relation that had duplicates.
	 */
	public DuplicateRelationException(String location, Class<? extends Relation> type) {
		super("Duplicate " + type.getSimpleName() + " for " + location);
	}
	
	/**
	 * Constructor. Used when the duplicate Relations are associated with a specific
	 * data set within a data file.
	 * 
	 * @param location The data file location. 
	 * @param dataSetNumber The number of the data set within the data file.
	 * @param type The Class of Relation that had duplicates.
	 */
	public DuplicateRelationException(String location, int dataSetNumber, Class<? extends Relation> type) {
		super("Duplicate " + type.getSimpleName() + " for Data Set #" + dataSetNumber + " in " + location);
	}
}
