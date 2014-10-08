package org.flowcyt.facejava.faceflow.relations.rdf;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashSet;
import java.util.Set;

import org.flowcyt.facejava.faceflow.exception.DuplicateRelationException;
import org.flowcyt.facejava.faceflow.relations.Relation;
import org.flowcyt.facejava.faceflow.relations.RelationCollection;
import org.flowcyt.facejava.faceflow.relations.RelationsRepository;

import com.hp.hpl.jena.rdf.model.InfModel;
import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.rdf.model.ModelFactory;
import com.hp.hpl.jena.rdf.model.RDFNode;
import com.hp.hpl.jena.rdf.model.Resource;
import com.hp.hpl.jena.rdf.model.Statement;
import com.hp.hpl.jena.rdf.model.StmtIterator;
import com.hp.hpl.jena.reasoner.ValidityReport;
import com.hp.hpl.jena.util.FileManager;
import com.hp.hpl.jena.vocabulary.RDF;

/**
 * <p>
 * RdfRelationsRepository is used to store and query for Relations which are backed by
 * an RDF file (i.e., one RDF statement corresponds to one Relation). Since RDF uses
 * URIs for identification, this class elso explicitly uses URIS for all file
 * locations.
 * 
 * @author echng
 */
public class RdfRelationsRepository implements RelationsRepository {
	/**
	 * The fragment delimiter character for URIs. 
	 */
	public static final char URI_FRAGMENT_DELIMITER = '#';
	
	/**
	 * Extracts the non-fragment portion from a URIRef string.
	 * 
	 * @param uriref THe URIRef
	 * @return Returns THE URIRef minus the fragment (if any) and  minus the delimiter
	 */
	public static String uriFromUriRef(String uriref) {
		int hashPos = uriref.indexOf(URI_FRAGMENT_DELIMITER);
		
		if (hashPos == -1)
			return uriref;
		
		return uriref.substring(0, hashPos);
	}
	
	/**
	 * Extracts the fragment from a URIref string.
	 * 
	 * @param uriref The URIref
	 * @return Returns the fragment (without the delimiter) of the URIref. If a
	 * fragment is not present or empty null is returned.
	 */
	public static String fragmentFromUriRef(String uriref) {
		int hashPos = uriref.indexOf(URI_FRAGMENT_DELIMITER);
		
		if (hashPos == -1 || hashPos == uriref.length() - 1)
			return null;
		
		return uriref.substring(hashPos + 1, uriref.length());
	}
	
	/**
	 * The JENA Model object for RDF models.
	 */
	private InfModel rdfModel;
	
	/**
	 * Used to create corresponding Statements from Relations. 
	 */
	private StatementFactoryVisitor statementFactory;
	
	/**
	 * Used to create corresponding Relations from Statements.
	 */
	private RdfRelationFactory relationFactory;
	
	/**
	 * Creates an RdfRelationsRepository. By default, the repository will use 
	 * StatementFactoryVisitorImpl to create statements and a RdfRelationFactory
	 * with the default creators to create Relations.
	 * 
	 * The Statement factory can be changed using setStatementFactory(). The Relation
	 * factory can be obtained through getRelatioNFactory() and can have new
	 * RelationCreators registered. The Relation factory ibject itself can also be
	 * changed using setRelationFactory().
	 * @param rdfFilePath The path to the instance RDF document containing the Flow
	 * Relations.
	 * @throws FileNotFoundException Thrown if the given path cannot be read.
	 */
	public RdfRelationsRepository(String rdfFilePath) throws IOException {
		InputStream in = FileManager.get().open(rdfFilePath);
		if (in == null)
			throw new IOException(rdfFilePath);
		
		Model instanceModel = ModelFactory.createDefaultModel();
		instanceModel.read(in, "");		
		
		this.rdfModel = ModelFactory.createRDFSModel(ModelVocabulary.getRDFSModel(), instanceModel);
		this.statementFactory = new StatementFactoryVisitorImpl();
		this.relationFactory = RdfRelationFactory.newInstance(true);
	}
	
	/**
	 * Changes the StatementFactoryVisitor used to create Statements from Relations.
	 * 
	 * @param factory The new factory to use.
	 */
	public void setStatementFactory(StatementFactoryVisitor factory) {
		this.statementFactory = factory;
	}
	
	/**
	 * Changes the RdfRelationFactory used to create Relations from Statements.
	 *
	 * @param factory The new factory to use.
	 */
	public void setRelationFactory(RdfRelationFactory factory) {
		this.relationFactory = factory;
	}
	
	/**
	 * @return Returns the RdfRelationFactory being used. 
	 */
	public RdfRelationFactory getRelationFactory() {
		return relationFactory;
	}
	
	/**
	 * @return Returns a JENA ValidityReport for the RDF model based on the Flow
	 * Relations RDFS schema. 
	 */
	public ValidityReport getValidityReport() {
		return rdfModel.validate();
	}

	public void addRelation(String dataFileLocation, Relation relation) throws DuplicateRelationException {
		Resource dataFileRes = makeResource(dataFileLocation);
		statementFactory.setSubject(dataFileRes);
		Statement stmt = statementFactory.dispatch(relation);
		
		if (!relation.duplicatesAllowed() && 
				rdfModel.contains(dataFileRes, stmt.getPredicate(), (RDFNode) null))
			throw new DuplicateRelationException(dataFileLocation, relation.getClass());
		
		rdfModel.add(stmt);
	}

	public void addRelation(String dataFileLocation, int dataSetNumber, Relation relation) throws DuplicateRelationException {
		Resource dataSetRes = makeResource(dataFileLocation, dataSetNumber);
		statementFactory.setSubject(dataSetRes);
		Statement stmt = statementFactory.dispatch(relation);
		
		if (!relation.duplicatesAllowed() && 
				rdfModel.contains(dataSetRes, stmt.getPredicate(), (RDFNode) null))
			throw new DuplicateRelationException(dataFileLocation, dataSetNumber, relation.getClass());
		
		rdfModel.add(stmt);
	}

	public Set<String> getDataFileLocations() {
		Set<String> rv = new HashSet<String>();
		
		StmtIterator iter = rdfModel.listStatements(null, RDF.type, ModelVocabulary.DATA_FILE);
		while (iter.hasNext()) {
			rv.add(iter.nextStatement().getSubject().getURI());
		}
		
		iter = rdfModel.listStatements(null, RDF.type, ModelVocabulary.DATA_SET);
		while (iter.hasNext()){
			rv.add(uriFromUriRef(iter.nextStatement().getSubject().getURI()));
		}
		
		return rv;
	}

	public RelationCollection getRelations(String dataFileLocation, int dataSetNumber) throws DuplicateRelationException {
		Resource dataSetRes = makeResource(dataFileLocation, dataSetNumber);
		RelationCollection rv = new RelationCollection();
		
		StmtIterator iter = rdfModel.listStatements(dataSetRes, null, (RDFNode) null);
		while (iter.hasNext()) {
			Relation rel = relationFactory.createRelation(iter.nextStatement());
			
			// Relations associated with the data set can not be overriden so we
			// no that it's a duplicate if it wasn't added.
			if (!rv.add(rel))
				throw new DuplicateRelationException(dataFileLocation, dataSetNumber, rel.getClass());
		}
		
		Resource dataFileRes = makeResource(dataFileLocation);
		Set<Class<? extends Relation>> addedFileRelationTypes = new HashSet<Class<? extends Relation>>();
		
		iter = rdfModel.listStatements(dataFileRes, null, (RDFNode) null);
		while (iter.hasNext()) {
			Relation rel = relationFactory.createRelation(iter.nextStatement());
			
			// For data file relations, it may not be a duplicate because it may have
			// been overriden by a relation from the data set. So, we keep track of which
			// types of Relations have been added for the data file and only throw when
			// an add is unsuccessful for a Relation which was duplicated by another
			// data file relation.
			if (!rv.add(rel) && addedFileRelationTypes.contains(rel.getClass()))
				throw new DuplicateRelationException(dataFileLocation, rel.getClass());
			
			addedFileRelationTypes.add(rel.getClass());
		}
		
		return rv;
	}
	
	/**
	 * Creates a Resource for the given data file location. The location is assumed to
	 * be a URI and so it is used as the new Resource's URI.
	 * 
	 * @param dataFileLocation The location of the Data file (assumed to be a URI)
	 * @return Returns the created resource
	 */
	protected Resource makeResource(String dataFileLocation) {
		return rdfModel.createResource(dataFileLocation);
	}
	
	/**
	 * Creates a Resource for the given data set at the given location with the given
	 * number. The location is assumed to be a URI and "location#number" is used as
	 * the new Resource's URI.
	 * 
	 * @param dataFileLocation The location of the Data file (assumed to be a URI)
	 * @param dataSetNumber The number of the dataset within the file.
	 * @return Returns the created resource
	 */
	protected Resource makeResource(String dataFileLocation, int dataSetNumber) {
		return rdfModel.createResource(dataFileLocation + URI_FRAGMENT_DELIMITER + dataSetNumber);
	}
}
