package org.flowcyt.facejava.faceflow.relations;

/**
 * <p>
 * A Relation between an FcsDataSet and an ExperimentDescription File.
 * 
 * @author echng
 */
public class ExperimentDescriptionRelation extends FileRelation {

	/**
	 * Constructor.
	 * 
	 * @param location The location of the file.
	 */
	public ExperimentDescriptionRelation(String location) {
		super(location);
	}

	public boolean duplicatesAllowed() {
		return false;
	}
}
