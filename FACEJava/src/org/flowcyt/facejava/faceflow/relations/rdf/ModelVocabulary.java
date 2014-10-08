package org.flowcyt.facejava.faceflow.relations.rdf;

import java.net.URL;

import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.rdf.model.ModelFactory;
import com.hp.hpl.jena.rdf.model.Property;
import com.hp.hpl.jena.rdf.model.Resource;
import com.hp.hpl.jena.rdf.model.ResourceFactory;

/**
 * <p>
 * Provides constants for the Properties and Resource types as well as the Namespace
 * for the Flow Relations RDFS. 
 * 
 * @author echng
 */
public class ModelVocabulary {
	
	public static final String NAMESPACE = "http://www.isac-net.org/std/rdf/meta-relations/1.0/flow#";
	
	public static final URL FLOW_RELATIONS_RDFS_URL = ModelVocabulary.class.getClassLoader().getResource("schemas/RDFFlow/schema/FcmMDR.v.1.0.rdfs");
	
	private static Model rdfsModel;
	
	public static Model getRDFSModel() {
		if (rdfsModel == null) {
			rdfsModel = ModelFactory.createDefaultModel();
			rdfsModel.read(FLOW_RELATIONS_RDFS_URL.toString());
		}
		return rdfsModel;		
	}
	
	protected static Resource createResource(String localName) {
		return ResourceFactory.createResource(NAMESPACE + localName);
	}
	
	protected static Property createProperty(String localName) {
		return ResourceFactory.createProperty(NAMESPACE, localName);
	}
	
	public static final Resource DATA_SET = createResource("dataset");
	public static final Resource DATA_FILE = createResource("datafile");
	
	public static final Property GATED_BY = createProperty("gated_by");
	public static final Property COMPENSATED_BY = createProperty("compensated_by");
	public static final Property TRANSFORMED_BY = createProperty("transformed_by");
	public static final Property INSTRUMENTATION = createProperty("generated_by_instrument_settings");
	public static final Property EXPERIMENT = createProperty("generated_within_experiment");
}
