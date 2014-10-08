package org.flowcyt.facejava.faceflow.test.bd;

import java.util.HashMap;
import java.util.Map;

import org.flowcyt.facejava.faceflow.application.outputlayers.OutputLayer;
import org.flowcyt.facejava.faceflow.test.OutputLayersTestHarness;
import org.flowcyt.facejava.faceflow.test.TestFileConstants;
import org.flowcyt.facejava.faceflow.test.bd.BdTestHarness.ParameterStatisticType;
import org.flowcyt.facejava.faceflow.test.bd.BdTestHarness.PopulationStatisticType;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

public class BdTest4 {
private static OutputLayersTestHarness harness;
	
	private Map<PopulationStatisticType, Double> expectedGateResults;
	
	private Map<ParameterStatisticType, Double> expectedParameterResults;
		
	@BeforeClass
	public static void oneTimeSetUp() throws Exception {
		harness = new OutputLayersTestHarness();
		
		harness.setFcsFile(TestFileConstants.FCS_TEST_FILE_DIRECTORY + "120403pep48hrp04253.H09");
		harness.setTransformationFile(TestFileConstants.TRANSFORMATIONS_TEST_FILE_DIRECTORY + "BDGatingTestTransformations4.xml");
		harness.setGatingFile(TestFileConstants.GATING_TEST_FILE_DIRECTORY + "BDGatingTest4.xml");
	}
	
	@Before
	public void setUp() {
		expectedGateResults = new HashMap<PopulationStatisticType, Double>();
		expectedParameterResults = new HashMap<ParameterStatisticType, Double>();
	}
	
	@Test public void testR1() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 4806.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 20.56);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 462.50);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 409.07);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 519.65);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 485.43);
		BdTestHarness.testParameterStatistics(result, "SSC-H", expectedParameterResults);
	}
   
	@Test public void testR3() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R3");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 0.00);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 6731.70);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 6731.70);
		BdTestHarness.testParameterStatistics(result, "FL3-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 181.0);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 181.0);
		BdTestHarness.testParameterStatistics(result, "FL4-H", expectedParameterResults);
	}
	
	@Test public void testR4() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R4");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 8.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 0.03);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 92.38);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 80.41);
		BdTestHarness.testParameterStatistics(result, "FL4-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 434.62);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 422.11);
		BdTestHarness.testParameterStatistics(result, "Time", expectedParameterResults);
	}
}
