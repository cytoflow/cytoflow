package org.flowcyt.facejava.faceflow.relations;

/**
 * <p>
 * A Relation between an FcsDataSet and a Transformation-ML file which has
 * transformations that transform the data.
 * 
 * @author echng
 */
public class TransformationRelation extends FileRelation {

	/**
	 * Constructor.
	 * 
	 * @param location The location of the Transformation-ML file.
	 */
	public TransformationRelation(String location) {
		super(location);
	}

	public boolean duplicatesAllowed() {
		return false;
	}
}
