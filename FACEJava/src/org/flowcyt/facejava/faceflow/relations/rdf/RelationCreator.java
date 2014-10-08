package org.flowcyt.facejava.faceflow.relations.rdf;

import org.flowcyt.facejava.faceflow.relations.Relation;

import com.hp.hpl.jena.rdf.model.Statement;

/**
 * <p>
 * RelationCreators are responsible for creating Relations for a given RDF Statement.
 * They are to be used in conjunction with a RdfRelationFactory where they are
 * registered as being able to handle Statements with some specific type of Property. 
 * 
 * @author echng
 */
public interface RelationCreator {
	/**
	 * Creates a Relation for the given Statement.
	 * 
	 * @param stmt The Statement to be handled.
	 * @return Returns the new Relation.
	 */
	public Relation create(Statement stmt);
}
