package org.flowcyt.facejava.gating.analysis;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

import org.flowcyt.facejava.fcsdata.Population;

/**
 * <p>
 * This class contains the analysis results of appliying the gates in a GateSet to all the
 * Populations in a PopulationCollection.
 * 
 * @author echng
 */
public class PopulationCollectionAnalysisResult {
	
	/**
	 * The Collection of Populations that was analysed and that this result is for.
	 */
	private Collection<? extends Population> popColl;
	
	/**
	 * A PopulationAnalysisResult for each of the Populations in the analyzed collection. THe
	 * results will be in the order corresponding to their order in popColl.getPopulations().
	 */
	private List<PopulationAnalysisResult> populationResults;
	
	/**
	 * Constructor. Protected so that it is only created by Analyzer. Consumers only
	 * need to read the info from the result returned by Analyzer.
	 * 
	 * @param popColl The Collection of Populations that was analyzed.
	 */
	protected PopulationCollectionAnalysisResult(Collection<? extends Population> popColl) {
		this.popColl = popColl;
		populationResults = new ArrayList<PopulationAnalysisResult>();
	}
	
	/**
	 * <p>
	 * Adds a result for one of the Populations in the analyzed collection. This method is
	 * protected since it should only be used by Analyzer at analysis time. Consumers only need to
	 * read the results from this object.
	 * 
	 * <p>
	 * The results should be added corresponding to their order in the Population Collection
	 * (as they were returned by the Collection's iterator.)
	 * 
	 * @param dsResult The PopulationAnalysisResult to add.
	 */
	protected void addPopulationResult(PopulationAnalysisResult dsResult) {
		populationResults.add(dsResult);
	}
	
	/**
	 * @return Returns the Collection of Populations that was analyzed.
	 */
	public Collection<? extends Population> getPopulationCollection() {
		return popColl;
	}
	
	/**
	 * @return Returns a list containing all the PopulationAnalysisResults for the Populations in
	 * the analyzed Collection of Populations. (They are in the same order as
	 * they were returned by the Collection's iterator.)
	 */
	public List<PopulationAnalysisResult> getPopulationResults() {
		return Collections.unmodifiableList(populationResults);
	}
	
	/**
	 * @return Returns true if there were any errors during analysis of this file. This method
	 * performs a "deep" check where all PopulationAnalysisResults for the Populations in the
	 * collection are also queried for errors. The actual error objects can be retrieved from
	 * the PopulationAnalysisResult for which it occured
	 */
	public boolean hasErrors() {
		for (PopulationAnalysisResult dsResult : populationResults) {
			if (dsResult.hasErrors())
				return true;
		}
		return false;
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("\n");
		for (PopulationAnalysisResult dsResult : populationResults) {
			builder.append(dsResult.toString());
			builder.append("\n");
		}
		return builder.toString();
	}
}
