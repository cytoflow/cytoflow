package org.flowcyt.facejava.faceflow.relations;

/**
 * <p>
 * A Relation between a FcsDataSet and a SpilloverMatrix in a Compensation-ML file
 * which can compensated the data.
 * 
 * @author echng
 */
public class CompensationRelation extends FileRelation {

	/**
	 * The id of the spilloverMatrix element within the Compensation-ML file.
	 */
	private String matrixId;
	
	/**
	 * Constructor.
	 * 
	 * @param location The location of the Compensation-ML file.
	 * @param matrixId The id of the spilloverMatrix element within the
	 * Compensation-ML file.
	 */
	public CompensationRelation(String location, String matrixId) {
		super(location);
		this.matrixId = matrixId;
	}
	
	/**
	 * @return Returns the id of the spilloverMatrix element within the
	 * Compensation-ML file.
	 */
	public String getMatrixId() {
		return matrixId;
	}
		
	public boolean duplicatesAllowed() {
		return false;
	}
}
