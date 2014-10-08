package org.flowcyt.facejava.faceflow.relations.rdf;

import org.flowcyt.facejava.faceflow.relations.Relation;
import org.flowcyt.facejava.faceflow.relations.RelationVisitor;

import com.hp.hpl.jena.rdf.model.Property;
import com.hp.hpl.jena.rdf.model.RDFNode;
import com.hp.hpl.jena.rdf.model.Resource;
import com.hp.hpl.jena.rdf.model.ResourceFactory;
import com.hp.hpl.jena.rdf.model.Statement;

/**
 * <p>
 * StatementFactoryVisitors are used by RdfRelationsRepository to create an RDF
 * Statement corresponding to a given Relation. The class leverages the logic in
 * RelationsVisitor to process the Relations in their concrete form. Also, the
 * return type of the visit() methods has been restricted to Statements.
 * 
 * <p>
 * A default implementation which handles Gating, Compensation, Transformation,
 * Instrumentation and ExperimentDescriptions has been provided in
 * StatementFactoryVisitorImpl. To handle storing new Relation types in an RDF file,
 * a visit() method which takes as an argument that type of Relation must be added
 * to a class providing the implementations for the visit() methods. (e.g., 
 * StatementFactoryVisitorImpl can be extended with a new subclass which provides visit()
 * methods for the new types of Relations). 
 * 
 * <p>
 * The visitor requires that setSubject (with the proper Resource) be called *prior*
 * to dispatch() being called for a Relation because Statements cannot have their
 * subject changed after creation. 
 * 
 * @author echng
 */
public abstract class StatementFactoryVisitor extends RelationVisitor {
	/**
	 * The subject of the next Statement to be created.
	 */
	protected Resource subject;

	/**
	 * Sets the subject of the next Statement to be created during a visit to be
	 * the given Resource.  
	 * 
	 * @param subject The Resource to use as the subject of the next created Statement
	 */
	public void setSubject(Resource subject) {
		this.subject = subject;
	}
	
	/**
	 * Creates a new Statement using the subject set through setSubject() and the given
	 * Property and Object. For use by sub-classes.
	 *  
	 * @param prop The Property of the Statement
	 * @param obj The object of the Statement
	 * @return Returns the new Statment.
	 */
	protected Statement createStatement(Property prop, RDFNode obj) {
		return ResourceFactory.createStatement(subject, prop, obj);
	}
	
	/**
	 * Since Statements are returned we need to cast the return of the dispatch
	 * to be a Statement.
	 */
	public Statement dispatch(Relation rel) {
		return (Statement) super.dispatch(rel);
	}
	
	/**
	 * Called when no visit method could be found (see class comments) that can handle
	 * the type of given Relation. By default a IllegalArgumentException is thrown.
	 * If a new type of Relation is created that needs to be stored in the file, a
	 * visit method must be created for it.
	 * 
	 * @param rel The Relation to be visited.
	 * @return Returns nothing. An IllegalArgumentException will always be thrown.
	 * @throws IllegalArgumentException The visitor does not try and store relations
	 * whose types are not known about.
	 */
	public Statement defaultVisit(Relation rel) {
		throw new IllegalArgumentException("Do not know how to map a " + rel.getClass().getSimpleName() + " to a RDF property.");
	}	
}
