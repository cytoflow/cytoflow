package org.flowcyt.facejava.faceflow.relations;

/**
 * <p>
 * A Relation between an FcsDataSet and some other piece of information (as an Object).
 * What the information represents is not known, however. This class allows
 * RelationsRepositories to save Relations whose types are not known at compile-time
 * and thus, no class has been created for it. This is different from a Relation which
 * has a class for it (and thus, not unknown) but is not known how it should be dealt
 * with (e.g., when UnknownRelations are created for properties in RDF files for which
 * a RelationCreator is not registerd).
 * 
 * @author echng
 */
public class UnknownRelation implements Relation {

	/**
	 * Some string which identifies the type of relation it is. (e.g., for RDF
	 * it may the URI of the unknown property.)
	 */
	private String identifier;
	
	/**
	 * The information associated with the DataSet.
	 */
	private Object value;
	
	public UnknownRelation(String identifier, Object value) {
		this.identifier = identifier;
		this.value = value;
	}
	
	/**
	 * @return Returns a String which should identify the type of the Relation
	 */
	public String getIdentifier() {
		return identifier;
	}

	/**
	 * @return Returns the associated information as an Object.
	 */
	public Object getValue() {
		return value;
	}
	
	public boolean duplicatesAllowed() {
		return true;
	}
}
