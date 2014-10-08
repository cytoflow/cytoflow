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

public class BdTest2 {	
	private static OutputLayersTestHarness harness;
	
	private Map<PopulationStatisticType, Double> expectedGateResults;
	
	private Map<ParameterStatisticType, Double> expectedParameterResults;
		
	@BeforeClass
	public static void oneTimeSetUp() throws Exception {
		harness = new OutputLayersTestHarness();
		
		harness.setFcsFile(TestFileConstants.FCS_TEST_FILE_DIRECTORY + "c4");
		harness.setTransformationFile(TestFileConstants.TRANSFORMATIONS_TEST_FILE_DIRECTORY + "BDGatingTestTransformations2.xml");
		harness.setGatingFile(TestFileConstants.GATING_TEST_FILE_DIRECTORY + "BDGatingTest2.xml");
	}
	
	@Before
	public void setUp() {
		expectedGateResults = new HashMap<PopulationStatisticType, Double>();
		expectedParameterResults = new HashMap<ParameterStatisticType, Double>();
	}
	
	@Test public void testR1() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 2538.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 33.37);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 152.08);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 75.13);
		expectedParameterResults.put(ParameterStatisticType.CV, 72.63);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 149.89);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 28.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 139.49);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 110.46);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 47.32);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 9.71);
		expectedParameterResults.put(ParameterStatisticType.CV, 252.5);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 6.38);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 26.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 4.8260714794339155);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 119.48);
		BdTestHarness.testParameterStatistics(result, "FL2-H", expectedParameterResults);
	}
	
	@Test public void testR1WithFilterM1a() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1-filtered-M1a");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 568.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 7.47);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 4.35);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 3.86);
		expectedParameterResults.put(ParameterStatisticType.CV, 46.69);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 4.18);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 10.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 4.8260714794339155);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 2.03);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
	}
	
	@Test public void testR1WithFilterM2a() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1-filtered-M2a");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1970.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 25.9);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 194.67);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 176.86);
		expectedParameterResults.put(ParameterStatisticType.CV, 44.81);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 173.09);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 28.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 139.49);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 87.22);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
	}
	 
	@Test public void testR1WithFilterM2b() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1-filtered-M2b");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 397.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 5.22);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 270.05);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 234.4);
		expectedParameterResults.put(ParameterStatisticType.CV, 66.71);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 230.82);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 9.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 205.35);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 180.16);
		BdTestHarness.testParameterStatistics(result, "FL2-H", expectedParameterResults);
	}
    
	@Test public void testR1WithFilterQ1UL() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1-filtered-Q1.UL");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 389.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 5.12);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 4.15);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 3.65);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 271.82);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 241.06);
		BdTestHarness.testParameterStatistics(result, "FL2-H", expectedParameterResults);
	}
	
	@Test public void testR1WithFilterQ1UR() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1-filtered-Q1.UR");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 8.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 0.11);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 108.96);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 79.86);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 184.06);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 60.09);
		BdTestHarness.testParameterStatistics(result, "FL2-H", expectedParameterResults);
	}
   
	@Test public void testR1WithFilterQ1LL() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1-filtered-Q1.LL");
				
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 179.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 2.35);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 4.76);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 4.35);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 5.3);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 4.8);
		BdTestHarness.testParameterStatistics(result, "FL2-H", expectedParameterResults);
	}

	@Test public void testR1WithFilterQ1LR() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1-filtered-Q1.LR");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1962.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 25.8);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 195.02);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 177.44);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 6.08);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 5.43);
		BdTestHarness.testParameterStatistics(result, "FL2-H", expectedParameterResults);
	}
}
