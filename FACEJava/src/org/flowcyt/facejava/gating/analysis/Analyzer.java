package org.flowcyt.facejava.gating.analysis;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.ParameterCollection;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.CircularParameterDependencyException;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSet;

/**
 * <p>
 * An Analyzer object is used to analyze event data using a given collection of Gates.
 * That is, it determines which events are in which gate. It is tied to a single
 * GateSet which contains the gates that will be used for analysis. ParameterCollections
 * can be added to the Analyzer (or specified at construction) to add Parameters that can be used
 * when performing the gating in addition to those in the population's DataRetriever that is 
 * being analyzed.
 * 
 * <p>
 * An Analyzer can be used for multiple PopulationCollections or Populations.
 * 
 * @author sLi (original author), 
 * 			Josef Spidlen - BC Cancer Research Centre (small corrections),
 * 			echng (heavily modified)
 */
public class Analyzer {
	
	/**
	 * The GateSet which has the gates that will be used to analyze any event data.
	 */
	private GateSet gateColl;
	
	/**
	 * The Parameters to use during analysis in addition to the ParameterCollection(s) in the
	 * analyzed Population's default DataRetriever.
	 */
	private List<ParameterCollection<?>> parameterCollections;

	/**
	 * Constructor. Creates an Analyzer object which will use the gates in the given collection
	 * and no additional Parameters than those in the analyzed Population's default DataRetriever.
	 * To add some, use addParameterCollection().
	 * 
	 * @param collection The GateSet which has the gates that will be used to analyze
	 * any event data.
	 */
	public Analyzer(GateSet collection) {
		this(collection, new ArrayList<ParameterCollection<?>>());
	}
	
	/**
	 * Constructor. Creates an Analyzer object which will use the gates in the given collection
	 * and the Parameters in the given ParameterCollection in addition to the
	 * ParameterCollection(s) in the analyzed Population's default DataRetriever.
	 * 
	 * @param collection The GateSet which has the gates that will be used to analyze
	 * any event data.
	 * @param parameterCollection A ParameterCollection containing Parameters to use during
	 * analysis in addition to the ParameterCollection(s) in the analyzed Population's default
	 * DataRetriever.
	 */
	public Analyzer(GateSet collection, ParameterCollection<?> parameterCollection) {
		this(collection, new ArrayList<ParameterCollection<?>>());
		this.parameterCollections.add(parameterCollection);
	}
	
	/**
	 * Constructor. Creates an Analyzer object which will use the gates in the given collection
	 * and all the Parameters in the given ParameterCollections in addition to
	 * the ParameterCollection(s) in the analyzed Population's default DataRetriever.
	 * 
	 * @param collection The GateSet which has the gates that will be used to analyze
	 * any event data.
	 * @param parameterCollections A List containing the ParameterCollections that contain 
	 * Parameters to use during analysis in addition to the ParameterCollection(s) in the
	 * analyzed Population's default DataRetriever.
	 */
	public Analyzer(GateSet collection, List<ParameterCollection<?>> parameterCollections) {
		this.gateColl = collection;
		this.parameterCollections = parameterCollections;
	}
	
	/**
	 * Adds a ParameterCollection whose Parameters will be used during anlaysis in addition to
	 * the ParameterCollection(s) in the analyzed Population's default DataRetriever.
	 * 
	 * @param parameterColl The ParameterCollection to add.
	 */
	public void addParameterCollection(ParameterCollection<?> parameterColl) {
		parameterCollections.add(parameterColl);
	}
	
	/**
	 * Analyzes all the Collection of Populations in the given list.
	 * 
	 * @param popColls A List containing the Collection of Populations to analyze
	 * @return Returns a List containing a list of the population collection results from the analysis
	 * of each population in each collection. Corresponding entries in the list match each other,
	 * i.e., the collection at index 2 will have its analysis result at index 2 in the returned
	 * list.
	 */
	public List<PopulationCollectionAnalysisResult> analyze(List<Collection<? extends Population>> popColls) {
		List<PopulationCollectionAnalysisResult> results = new ArrayList<PopulationCollectionAnalysisResult>(popColls.size());
		
		for (Collection<? extends Population> coll : popColls) {
			results.add(this.analyze(coll)); 
		}
		
		return results;
	}
	
	/**
	 * Analyzes each Population in a Collection of Populations.
	 *  
	 * @param popColl A Collection containing the Populations to be analyzed.
	 * @return Returns a a DataFileAnalysisResult containing the results of the analysis
	 * on each data set in the data file.
	 */
	public PopulationCollectionAnalysisResult analyze(Collection<? extends Population> popColl) {
		PopulationCollectionAnalysisResult result = new PopulationCollectionAnalysisResult(popColl);
		
		for (Population pop : popColl) {
			result.addPopulationResult(this.analyze(pop)); 
		}
		
		return result;
	}
	
	/**
	 * <p>
	 * Analyzes the given Population using the GateSet specified during construction. 
	 * 
	 * <p>
	 * If there is an error that prevents analysis of the entire Population (e.g., duplicate
	 * parameter names) then an empty result will be returned which contains only the error.
	 * It will have no GateAnalysisResults.
	 * 
	 * <p>
	 * If there is an error processing one of the gates, that gate's inside events will
	 * be all events that were determined inside that gate up until the error. (That is,
	 * analysis stops using that gate once an error occurs.)
	 * 
	 * <p>
	 * Use the error methods in the Population and Gate AnalysisResult classes to determine if
	 * any errors exist and what they are.
	 * 
	 * <p>
	 * <b>Note:</b> The DataRetriever used for the analysis will use the ParameterCollections used by
	 * the DataRetriever returned by pop.getRetriever() and all ParameterCollections added to
	 * the analyzer.
	 * 
	 * @param pop The Population to be analyzed.
	 * @return Returns the PopulationAnalysisResult object for the analysis of this data
	 * set.
	 */
	public PopulationAnalysisResult analyze(Population pop) {
		DataRetriever retriever = null;
		PopulationAnalysisResult result = new PopulationAnalysisResult(gateColl, pop);
		try {
			retriever = new DataRetriever(pop.getRetriever(), parameterCollections);
		} catch (DuplicateParameterReferenceException ex) {
			result.addAnalysisError(new AnalysisError(ex));
			return result;
		} catch (CircularParameterDependencyException ex) {
			result.addAnalysisError(new AnalysisError(ex));
			return result;
		}
		
		for (Gate gate : gateColl) {
			try {
				result.addGateResult(gate.isInside(pop, retriever));
			} catch (DataRetrievalException ex) {
				result.addAnalysisError(new GateAnalysisError(gate, ex));
			}
		}
		
		return result;
	}
}
