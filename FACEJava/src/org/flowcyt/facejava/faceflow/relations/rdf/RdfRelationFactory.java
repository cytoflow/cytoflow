package org.flowcyt.facejava.faceflow.relations.rdf;

import java.util.HashMap;
import java.util.Map;

import org.flowcyt.facejava.faceflow.relations.CompensationRelation;
import org.flowcyt.facejava.faceflow.relations.ExperimentDescriptionRelation;
import org.flowcyt.facejava.faceflow.relations.GatingRelation;
import org.flowcyt.facejava.faceflow.relations.InstrumentationRelation;
import org.flowcyt.facejava.faceflow.relations.Relation;
import org.flowcyt.facejava.faceflow.relations.TransformationRelation;
import org.flowcyt.facejava.faceflow.relations.UnknownRelation;

import com.hp.hpl.jena.rdf.model.Property;
import com.hp.hpl.jena.rdf.model.Statement;

/**
 * <p>
 * A class use to create the appropriate relations for an RDF Statement based on the
 * Property of the statement. The factory is used by the RdfRelationsRepository when
 * it queries the RDF model for statements about a data set to convert them into the
 * Relations that are returned.
 * 
 * <p>
 * To perform the actual Relation creation, the factory allows clients to register a
 * RelationCreator for an RDF Property. When it is passed a Statement whose Property
 * matches a Property that has been registered, the Statement is passed to the
 * associated RelationCreator for processing. When a Statement's Property has not been
 * registered, the factory defaults to creating an UnknownRelation whose identifier
 * is the Property's URI and its value is the object of the Statement (the RDFNode).
 * 
 * <p>
 * Default RelationCreators are provided for the standard Flow Relations properties
 * as nested classes.
 * 
 * @author echng
 */
public class RdfRelationFactory {
	
	/**
	 * Maps a Property to the RelationCreator which can handle it.
	 */
	private Map<Property, RelationCreator> propertyToCreatorMap;
	
	/**
	 * Constructor. Instances can be obtained through newInstance(). 
	 */
	protected RdfRelationFactory() {
		propertyToCreatorMap = new HashMap<Property, RelationCreator>();
	}
	
	/**
	 * @return Returns a new instance of the factory with no RelationCreators
	 * registered for any Properties.
	 */
	public static RdfRelationFactory newInstance() {
		return newInstance(false);
	}
	
	/**
	 * @param registerDefaultCreators If true, the default RelationCreators for Gating,
	 * Transformation, Compensation, Instrumentation and Experiment Description will
	 * be registered for their corresponding Properties. Otherwise, no RelationCreators
	 * will be registered for any Properties.
	 * @return Returns a new instance of the factory. The factory will have default
	 * creators registered for the standard properties if registerDefaultCreators is
	 * true.
	 */
	public static RdfRelationFactory newInstance(boolean registerDefaultCreators) {
		RdfRelationFactory rv = new RdfRelationFactory();
		
		if (registerDefaultCreators) {
			rv.register(ModelVocabulary.GATED_BY, new GatingRelationCreator());
			rv.register(ModelVocabulary.COMPENSATED_BY, new CompensationRelationCreator());
			rv.register(ModelVocabulary.TRANSFORMED_BY, new TransformationRelationCreator());
			rv.register(ModelVocabulary.INSTRUMENTATION, new InstrumentationRelationCreator());
			rv.register(ModelVocabulary.EXPERIMENT, new ExperimentDescriptionRelationCreator());
		}
		
		return rv;
	}
	
	/**
	 * Registers a RelationCreator to handle the creation of Relations for Statements
	 * with the given Property. If another RelationCreator has already been registered
	 * for the Property it is replaced by the given creator.
	 * 
	 * @param property The Property of the Statement that can be handled by the
	 * RelationCreator
	 * @param relCreator The RelationCreator that creation is delegated to.
	 */
	public void register(Property property, RelationCreator relCreator) {
		propertyToCreatorMap.put(property, relCreator);
	}
	
	public Relation createRelation(Statement stmt) {
		RelationCreator creator = propertyToCreatorMap.get(stmt.getPredicate());
		
		Relation rv;
		if (creator == null)
			rv = createUnknownRelation(stmt);
		else
			rv = creator.create(stmt);
		
		return rv;
	}
	
	/**
	 * Handles the creation of a Relation for a Statement whose Property has not been
	 * registered. The returned Unknown Relation will have the Property's URI for
	 * an identifier and the object (as in Statement.getObject()) of the statement
	 * as its value. (The Object is usually but maybe not always an RDFNode.)
	 * 
	 * @param stmt The Statement to get the info from.
	 * @return Returns the created UnknownRelation.
	 */
	protected UnknownRelation createUnknownRelation(Statement stmt) {
		String id = stmt.getPredicate().getURI();
		return new UnknownRelation(id, stmt.getObject());
	}
	
	/**
	 * A default implementation of RelationCreator for creating GatingRelations.
	 * The URI of the object of the Statement is taken to be the file's location. 
	 * 
	 * @author echng
	 */
	public static class GatingRelationCreator implements RelationCreator {
		public GatingRelation create(Statement stmt) {
			String uriref = stmt.getResource().getURI();
			return new GatingRelation(RdfRelationsRepository.uriFromUriRef(uriref),
					RdfRelationsRepository.fragmentFromUriRef(uriref));
		}
	}
	
	/**
	 * A default implementation of RelationCreator for creating TransformationRelations.
	 * The URI of the object of the Statement is taken to be the file's location. 
	 * 
	 * @author echng
	 */
	public static class TransformationRelationCreator implements RelationCreator {
		public TransformationRelation create(Statement stmt) {
			return new TransformationRelation(stmt.getResource().getURI());
		}
	}
	
	/**
	 * A default implementation of RelationCreator for creating CompensationRelations.
	 * The URI (minus the fragment) of the object of the Statement is taken to be the
	 * file's location. While the fragment is taken to be the id for the spilloverMatrix. 
	 * 
	 * @author echng
	 */
	public static class CompensationRelationCreator implements RelationCreator {
		public CompensationRelation create(Statement stmt) {
			String uriref = stmt.getResource().getURI();
			return new CompensationRelation(RdfRelationsRepository.uriFromUriRef(uriref),
					RdfRelationsRepository.fragmentFromUriRef(uriref));
		}
	}
	
	/**
	 * A default implementation of RelationCreator for creating InstrumentationRelations.
	 * The URI of the object of the Statement is taken to be the file's location. 
	 * 
	 * @author echng
	 */
	public static class InstrumentationRelationCreator implements RelationCreator {
		public InstrumentationRelation create(Statement stmt) {
			return new InstrumentationRelation(stmt.getResource().getURI());
		}
	}
	
	/**
	 * A default implementation of RelationCreator for creating ExperimentDescriptionRelations.
	 * The URI of the object of the Statement is taken to be the file's location. 
	 * 
	 * @author echng
	 */
	public static class ExperimentDescriptionRelationCreator implements RelationCreator {
		public ExperimentDescriptionRelation create(Statement stmt) {
			return new ExperimentDescriptionRelation(stmt.getResource().getURI());
		}
	}
}
