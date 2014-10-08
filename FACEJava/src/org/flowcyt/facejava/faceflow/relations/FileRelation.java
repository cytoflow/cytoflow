package org.flowcyt.facejava.faceflow.relations;

/**
 * <p>
 * An abstract class for Relations which associate an external file to a data set.
 * Note that no assumptions are made about how the location is identified (it could
 * be a filepath, or URI) so a String is used. When the external file needs to be
 * loaded care should be taken to ensure that the location string is used as the
 * correct type of location (file, URI, etc.). 
 * 
 * @author echng
 */
public abstract class FileRelation implements Relation {
	/**
	 * The location of the external file.
	 */
	private String location;
	
	/**
	 * Constructor.
	 * 
	 * @param location The location of the external file.
	 */
	public FileRelation(String location) {
		this.location = location;
	}
	
	/**
	 * @return Returns the location of the external file.
	 */
	public String getLocation() {
		return location;
	}
}
