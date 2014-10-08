package org.flowcyt.facejava.faceflow.relations;

/**
 * <p>
 * A Relation between an FcsDataSet and an Instrumentation File.
 * 
 * @author echng
 */
public class InstrumentationRelation extends FileRelation {

	/**
	 * Constructor.
	 * 
	 * @param location The location of the Instrumentation file.
	 */
	public InstrumentationRelation(String location) {
		super(location);
	}
	
	public boolean duplicatesAllowed() {
		return false;
	}
}
