package org.flowcyt.facejava.faceflow.relations;

/**
 * <p>
 * A Relation between a FcsDataSet and a Gating-ML file that contains the Gates
 * to use on the data.
 * 
 * @author echng
 */
public class GatingRelation extends FileRelation {

	private String gateId;
	
	/**
	 * Constructor. 
	 * 
	 * @param location The location of the Gating-ML file.
	 * @param gateId The id of the gate to use. If null, all agtes in the file are used.  
	 */
	public GatingRelation(String location, String gateId) {
		super(location);
		this.gateId = gateId;
	}
	
	public boolean duplicatesAllowed() {
		return false;
	}
	
	public String getGateId() {
		return gateId;
	}
}
