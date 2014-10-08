package org.flowcyt.facejava.faceflow.test.bd;

import java.util.Map;

import org.flowcyt.facejava.faceflow.application.outputlayers.OutputLayer;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.statistics.PopulationParameterStatistics;
import org.flowcyt.facejava.fcsdata.statistics.PopulationStatistics;
import org.junit.Assert;

public class BdTestHarness {
	private static final double EPSILON = 0.01;
	
	enum ParameterStatisticType {
		MEAN,
		MEDIAN,
		MODE_VALUE,
		SMALLEST_MODE,
		CV,
		GEOMETRIC_MEAN,
		STANDARD_DEVIATION		
	}
	
	enum PopulationStatisticType {
		EVENT_COUNT,
		PERCENT_OF_PARENT
	}
	
	public static void testGatingStatistics(OutputLayer layer, Map<PopulationStatisticType, Double> expectedResults) throws Exception {
		PopulationStatistics stats = layer.getResultPopulation().getStatistics();
		for (Map.Entry<PopulationStatisticType, Double> entry : expectedResults.entrySet()) {
			Assert.assertEquals(entry.getValue(), getGateStatByType(stats, entry.getKey()), EPSILON);
		}
	}
	
	private static double getGateStatByType(PopulationStatistics stats, PopulationStatisticType statType) {
		double rv;
		switch (statType) {
			case EVENT_COUNT:
				rv =  stats.getN();
				break;
			case PERCENT_OF_PARENT:
				rv = stats.getPercentOfParent();
				break;
			default:
				throw new AssertionError("Invalid PopulationStatisticType");
		}
		return rv;
	}
	
	public static void testParameterStatistics(OutputLayer layer, String parameterReference, Map<ParameterStatisticType, Double> expectedResults) throws Exception {
		PopulationStatistics popStats = layer.getResultPopulation().getStatistics();
		PopulationParameterStatistics stats = popStats.getParameterStatistics(new ParameterReference(parameterReference));
		for (Map.Entry<ParameterStatisticType, Double> entry : expectedResults.entrySet()) {
			Assert.assertEquals(entry.getValue(), getParameterStatByType(stats, entry.getKey()), EPSILON);
		}
	}
	
	private static double getParameterStatByType(PopulationParameterStatistics stats, ParameterStatisticType statType) {
		double rv;
		switch (statType) {
			case MEAN:
				rv = stats.getMean();
				break;
			case MEDIAN:
				rv = stats.getMedian();
				break;
			case MODE_VALUE:
				rv = stats.getModeFrequency();
				break;
			case SMALLEST_MODE:
				rv = stats.getSmallestMode();
				break;
			case CV:
				rv = stats.getCoefficientOfVariation();
				break;
			case GEOMETRIC_MEAN:
				rv = stats.getGeometricMean();
				break;
			case STANDARD_DEVIATION:
				rv = stats.getUnbiasedStdDev();
				break;
			default:
				throw new AssertionError("Invalid ParameterStatisticType");
		}
		return rv;
	}
}
