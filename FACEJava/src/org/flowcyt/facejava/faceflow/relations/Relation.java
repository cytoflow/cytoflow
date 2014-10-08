package org.flowcyt.facejava.faceflow.relations;


/**
 * <p>
 * A Relation relates a data set to some other information. Concrete Relations 
 * determine what information they store. To process the information in Relations,
 * use a RelationsVisitor.  
 * 
 * @author echng
 */
public interface Relation {
	
	/**
	 * @return Returns true iff multiple relations of the same type are allowed
	 * to be associated with the same data set in a RelationsRepository (after
	 * overriding rules are applied).
	 */
	public boolean duplicatesAllowed();
		
}
