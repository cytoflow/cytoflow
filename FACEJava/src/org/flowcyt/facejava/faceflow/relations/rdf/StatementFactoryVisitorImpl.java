package org.flowcyt.facejava.faceflow.relations.rdf;

import org.flowcyt.facejava.faceflow.relations.CompensationRelation;
import org.flowcyt.facejava.faceflow.relations.ExperimentDescriptionRelation;
import org.flowcyt.facejava.faceflow.relations.GatingRelation;
import org.flowcyt.facejava.faceflow.relations.InstrumentationRelation;
import org.flowcyt.facejava.faceflow.relations.TransformationRelation;
import org.flowcyt.facejava.faceflow.relations.UnknownRelation;
import org.flowcyt.facejava.faceflow.relations.VisitMethod;

import com.hp.hpl.jena.rdf.model.Property;
import com.hp.hpl.jena.rdf.model.RDFNode;
import com.hp.hpl.jena.rdf.model.Resource;
import com.hp.hpl.jena.rdf.model.ResourceFactory;
import com.hp.hpl.jena.rdf.model.Statement;

/**
 * <p>
 * Provides a default implementation for StatementFactoryVisitor which can handle
 * the creation of the approppriate Statements for Gating, Compensation, Transformation,
 * Instrumentation and ExperimetnDescription Relations. This class can be subclassed
 * to provide visit() methods for new types of Relations.
 * 
 * <p>
 * UnknownRelations are also handled by treating its identifier as a Property URI
 * and the value as the object. If the value is an RDFNode, it is used as is for the
 * object of the statement. If not, it is changed to a plain RDF literal which contains
 * the value of relation.getValue().toString(). 
 * 
 * @author echng
 */
public class StatementFactoryVisitorImpl extends StatementFactoryVisitor {

	/**
	 * A visit method for CompensationRelations. Will be called when dispatch is
	 * given a CompensationRelation.
	 *  
	 * @param rel The CompensationRelation to be visited.
	 * @return A JENA RDF Statement for the relation.
	 */
	@VisitMethod
	public Statement visit(CompensationRelation rel) {
		Resource obj = ResourceFactory.createResource(rel.getLocation() + RdfRelationsRepository.URI_FRAGMENT_DELIMITER + rel.getMatrixId());
		return createStatement(ModelVocabulary.COMPENSATED_BY, obj);
	}

	/**
	 * A visit method for GatingRelations. Will be called when dispatch is
	 * given a GatingRelation.
	 *  
	 * @param rel The GatingRelation to be visited.
	 * @return A JENA RDF Statement for the relation.
	 */
	@VisitMethod
	public Statement visit(GatingRelation rel) {
		Resource obj = ResourceFactory.createResource(rel.getLocation());
		return createStatement(ModelVocabulary.GATED_BY, obj);
	}

	/**
	 * A visit method for TransformationRelations. Will be called when dispatch is
	 * given a TransformationRelation.
	 *  
	 * @param rel The TransformationRelation to be visited.
	 * @return A JENA RDF Statement for the relation.
	 */
	@VisitMethod
	public Statement visit(TransformationRelation rel) {
		Resource obj = ResourceFactory.createResource(rel.getLocation());
		return createStatement(ModelVocabulary.TRANSFORMED_BY, obj);
	}
	
	/**
	 * A visit method for InstrumentationRelations. Will be called when dispatch is
	 * given a InstrumentationRelation.
	 *  
	 * @param rel The InstrumentationRelation to be visited.
	 * @return A JENA RDF Statement for the relation.
	 */
	@VisitMethod
	public Statement visit(InstrumentationRelation rel) {
		Resource obj = ResourceFactory.createResource(rel.getLocation());
		return createStatement(ModelVocabulary.INSTRUMENTATION, obj);
	}
	
	/**
	 * A visit method for ExperimentDescriptionRelations. Will be called when dispatch is
	 * given a ExperimentDescriptionRelation.
	 *  
	 * @param rel The ExperimentDescriptionRelation to be visited.
	 * @return A JENA RDF Statement for the relation.
	 */
	@VisitMethod
	public Statement visit(ExperimentDescriptionRelation rel) {
		Resource obj = ResourceFactory.createResource(rel.getLocation());
		return createStatement(ModelVocabulary.EXPERIMENT, obj);
	}
	
	/**
	 * The returned Statement for the UnknownRelation will have its Property's URI be
	 * the relation's identifier and its object be the relation's value. If the value
	 * is an RDFNode, it is used as is for the object of the statement. If not, it is
	 * changed to a plain RDF literal which contains the value of 
	 * relation.getValue().toString(). 
	 * 
	 * @param rel The UnknownRelation
	 * @return Returns the new Statement.
	 */
	@VisitMethod
	public Statement visit(UnknownRelation rel) {
		Property prop = ResourceFactory.createProperty(rel.getIdentifier());
		RDFNode obj;
		
		if (rel.getValue() instanceof RDFNode)
			obj = (RDFNode) rel.getValue();
		else
			obj = ResourceFactory.createPlainLiteral(rel.getValue().toString());
		
		return createStatement(prop, obj);
	}

}
