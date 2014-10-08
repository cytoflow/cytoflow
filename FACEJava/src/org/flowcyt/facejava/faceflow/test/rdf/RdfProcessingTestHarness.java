package org.flowcyt.facejava.faceflow.test.rdf;

import java.io.IOException;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.flowcyt.facejava.faceflow.application.LayerFactoryVisitor;
import org.flowcyt.facejava.faceflow.application.Logger;
import org.flowcyt.facejava.faceflow.application.outputlayers.OutputLayer;
import org.flowcyt.facejava.faceflow.loader.FileLoader;
import org.flowcyt.facejava.faceflow.loader.URIFileLoader;
import org.flowcyt.facejava.faceflow.relations.DataSetRelations;
import org.flowcyt.facejava.faceflow.relations.RelationsRepositoryIterator;
import org.flowcyt.facejava.faceflow.relations.rdf.RdfRelationsRepository;
import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.Population;
import org.junit.Assert;

public class RdfProcessingTestHarness {
	
	private RdfRelationsRepository repository;
	
	private LayerFactoryVisitor visitor;
	
	private Map<String, OutputLayer> layerLookupTable;
	
	public static final double EPSILON = 0.0000005;
	
	public RdfProcessingTestHarness(String rdfFile) throws IOException {
		repository = new RdfRelationsRepository(rdfFile);
		
		FileLoader loader = new URIFileLoader();
		visitor = new LayerFactoryVisitor(new Logger(null), loader);
		
		RelationsRepositoryIterator iterator = new RelationsRepositoryIterator(repository, loader);
		while (iterator.hasNext()) {
			DataSetRelations relations = iterator.next();
			relations.accept(visitor);
		}
		
		layerLookupTable = new HashMap<String, OutputLayer>();
		for (OutputLayer layer : visitor.getFinalLayers()) {
			layerLookupTable.put(layer.getResultBaseName(), layer);
		}
	}
	
	public void testExpectedValues(String layerBaseName, List<ParameterReference> expectedReferences, Set<double[]> expectedEventValues) throws Exception {
		Assert.assertTrue(layerLookupTable.containsKey(layerBaseName));
		
		Population result = layerLookupTable.get(layerBaseName).getResultPopulation();
		
		DataRetriever retriever = result.getRetriever();
		Assert.assertEquals(expectedReferences.size(), retriever.getAllParameters().size());
		
		Collection<Event> popCopy = new HashSet<Event>(result);
		
		for (double[] expected : expectedEventValues) {
			Collection<Event> filteredEvents = popCopy; 
			int i = 0;
			for (ParameterReference ref : expectedReferences) {
				filteredEvents = filter(filteredEvents, retriever, ref, expected[i++]);
			}
			
			Assert.assertEquals(1, filteredEvents.size());
		}
	}
	
	private Collection<Event> filter(Collection<Event> input, DataRetriever retriever, ParameterReference ref, double expectedValue) throws Exception {
		Collection<Event> rv = new HashSet<Event>();
		
		for (Event ev : input) {			
			double actual = retriever.getScale(ref, ev);
			double diff = actual - expectedValue;
			if (Math.abs(diff) <= EPSILON)
				rv.add(ev);				
		}
		
		return rv;
	}
}
