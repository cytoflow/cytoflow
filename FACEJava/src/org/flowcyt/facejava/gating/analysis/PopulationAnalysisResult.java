package org.flowcyt.facejava.gating.analysis;

import java.util.AbstractCollection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.gates.GateSubPopulation;

/**
 * <p>
 * Contains the results of analyzing a Population with the Gates in a GateSet.
 * It will contain GateSubPopulations for each of the gates in the GateGollection.
 * 
 * <p>
 * Since GateSubPopulations are Populations, and this result contains them, Collection
 * is implemented. Note that this is not quite the same "kind" of collection as a FcsDataFile.
 * In the FcsDataFile, Populations are related because they are all in the same file 
 * (but they have nothing intrinsically in common with each other). Here the
 * Populations are related because they all have the same parent population and each of the
 * contained Populations are (most likely) different subsets of that parent (based on which gate
 * was applied).
 *  
 * @author echng
 */
public class PopulationAnalysisResult extends AbstractCollection<GateSubPopulation>  {
	
	/**
	 * The Population that was analyzed.
	 */
	private Population pop;
	
	/**
	 * A Map from a Gate to its GateSubPopulation.
	 */
	private Map<Gate, GateSubPopulation> gateResults;
	
	/**
	 * A Set containing all the errors found during analysis.
	 */
	private Set<AnalysisError> errors;
	
	/**
	 * The GateSet containing the Gates used during Analysis
	 */
	private GateSet gateColl;
	
	/**
	 * Constructor. Protected so that it is only created by Analyzer. Consumers only
	 * need to read the info from the result returned by Analyzer.
	 *  
	 * @param gateColl The GateSet which contains the Gates used during analysis of the
	 * Populated.
	 * @param pop The Population being analyzed
	 */
	protected PopulationAnalysisResult(GateSet gateColl, Population pop) {
		this.pop = pop;
		this.gateColl = gateColl;
		gateResults = new HashMap<Gate, GateSubPopulation>();
		errors = new HashSet<AnalysisError>();
	}
	
	/**
	 * Adds a GateSubPopulation which is the result of applying one Gate to the
	 * events in the analyzed Population. This method is protected since it should only be
	 * used by Analyzer during analysis time. Consumers only need to read the results
	 * from this object.
	 *  
	 * @param gateResult The GateSubPopulation to be added.
	 */
	protected void addGateResult(GateSubPopulation gateResult) {
		gateResults.put(gateResult.getGate(), gateResult);
	}
	
	/**
	 * @return Returns the Population that was analyzed.
	 */
	public Population getPopulation() {
		return pop;
	}
	
	/**
	 * @return Returns the GateSet containing the Gates used to analyze the Population.
	 */
	public GateSet getGateCollection() {
		return gateColl;
	}
	
	/**
	 * Adds an AnalysisError to the Result. Errors which prevent a whole Population from being
	 * analyzed should be added here. Errors which happened to Gates should be added to the
	 * corresponding to GateSubPopulation. This method is protected since it should only be
	 * used by Analyzer during analysis time. Consumers only need to read the results
	 * from this object.
	 * 
	 * @param err
	 */
	protected void addAnalysisError(AnalysisError err) {
		errors.add(err);
	}
	
	/**
	 * @return Returns a set containing all the errors that occured during analysis
	 */
	public Set<AnalysisError> getAnalysisErrors() {
		return Collections.unmodifiableSet(errors);
	}
	
	/**
	 * @return Returns true if any errors occured during analysis. 
	 */
	public boolean hasErrors() {
		if (errors.size() > 0)
			return true;
		
		return false;
	}
	
	/**
	 * @param gateId The id of the Gate whose GateSubPopulation should be returned.
	 * @return Returns the GateSubPopulation for the Gate with the given id or null if no
	 * such Gate (or result) exists.
	 */
	public GateSubPopulation getGateResult(String gateId) {
		Gate g = gateColl.get(gateId);
		if (g == null)
			return null;
		return this.getGateResult(g);
	}
	
	/**
	 * @param gate The Gate whose GateAnalysisRsult should be returned.
	 * @return Returns the GateSubPopulation for the given Gate.
	 */
	public GateSubPopulation getGateResult(Gate gate) {
		return gateResults.get(gate);
	}

	@Override public Iterator<GateSubPopulation> iterator() {
		return gateResults.values().iterator();
	}

	@Override public int size() {
		return gateResults.size();
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append(" -- # Events: ");
		builder.append(pop.size());
		builder.append("\n");
		if (hasErrors()) {
			builder.append("Errors:\n");
			for (AnalysisError error : errors) {
				builder.append(error);
				builder.append("\n");
			}
		}
		
		for (GateSubPopulation gateResult : gateResults.values()) {
			builder.append(gateResult.toString());
			builder.append("\n");
		}
		
		return builder.toString();
	}
}
