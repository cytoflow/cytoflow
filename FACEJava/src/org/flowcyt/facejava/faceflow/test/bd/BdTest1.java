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

public class BdTest1 {	
	private static OutputLayersTestHarness harness;
	
	private Map<PopulationStatisticType, Double> expectedGateResults;
	
	private Map<ParameterStatisticType, Double> expectedParameterResults;
		
	@BeforeClass
	public static void oneTimeSetUp() throws Exception {
		harness = new OutputLayersTestHarness();
		
		harness.setFcsFile(TestFileConstants.FCS_TEST_FILE_DIRECTORY + "MPM.1.Sort.Bcells.DG0062100.023");
		harness.setTransformationFile(TestFileConstants.TRANSFORMATIONS_TEST_FILE_DIRECTORY + "BDGatingTestTransformations1.xml");
		harness.setGatingFile(TestFileConstants.GATING_TEST_FILE_DIRECTORY + "BDGatingTest1.xml");
	}
	
	@Before
	public void setUp() {
		expectedGateResults = new HashMap<PopulationStatisticType, Double>();
		expectedParameterResults = new HashMap<ParameterStatisticType, Double>();
	}
	
	@Test public void testR1() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1234.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 9.31);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 322.48);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 317.51);
		expectedParameterResults.put(ParameterStatisticType.CV, 18.32);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 315.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 18.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 284.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 59.07);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testR2() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R2");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1379.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 10.41);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 323.55);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 319.51);
		expectedParameterResults.put(ParameterStatisticType.CV, 16.21);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 316.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 20.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 284.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 52.43);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testR3() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R3");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 915.0);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
	}
	
	@Test public void testG4() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G4");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1133.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 8.55);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 322.07);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 318.53);
		expectedParameterResults.put(ParameterStatisticType.CV, 15.14);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 316.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 15.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 281.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 48.76);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}

	@Test public void testG5() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G5");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1184.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 8.94);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 320.88);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 317.35);
		expectedParameterResults.put(ParameterStatisticType.CV, 15.15);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 315.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 18.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 284.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 48.62);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testG6() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G6");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 85.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 0.64);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 295.44);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 293.19);
		expectedParameterResults.put(ParameterStatisticType.CV, 12.62);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 291.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 5.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 284.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 37.29);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testG7() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G7");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 54.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 0.41);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 290.65);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 287.92);
		expectedParameterResults.put(ParameterStatisticType.CV, 13.86);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 284.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 5.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 284.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 40.28);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testG8() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G8");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 12334.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 93.09);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 592.41);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 538.78);
		expectedParameterResults.put(ParameterStatisticType.CV, 41.71);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 560.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 1442.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 1023.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 247.11);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testG9() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G9");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1180.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 8.91);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 323.93);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 318.94);
		expectedParameterResults.put(ParameterStatisticType.CV, 18.34);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 316.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 15.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 281.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 59.39);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testG10() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G10");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1294.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 9.77);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 325.40);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 321.32);
		expectedParameterResults.put(ParameterStatisticType.CV, 16.22);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 318.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 15.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 281.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 52.76);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testG11() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G11");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1133.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 8.55);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 322.07);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 318.53);
		expectedParameterResults.put(ParameterStatisticType.CV, 15.14);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 316.0);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 15.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 281.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 48.76);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testG4WithFilterM1() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G4-filtered-M1");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1010.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 7.62);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 8.33);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 5.51);
		expectedParameterResults.put(ParameterStatisticType.CV, 97.14);
		expectedParameterResults.put(ParameterStatisticType.MEDIAN, 5.19);
		expectedParameterResults.put(ParameterStatisticType.MODE_VALUE, 29.0);
		expectedParameterResults.put(ParameterStatisticType.SMALLEST_MODE, 1.0);
		expectedParameterResults.put(ParameterStatisticType.STANDARD_DEVIATION, 8.09);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
	}
	
	@Test public void testG4WithFilterQ1UL() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G4-filtered-Q1.UL");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 23.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 0.17);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 11.14);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 8.6);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 662.44);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 501.46);
		BdTestHarness.testParameterStatistics(result, "FL2-H", expectedParameterResults);
	}
	
	@Test public void testG4WithFilterQ1UR() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "G4-filtered-Q1.UR");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 27.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 0.2);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 67.39);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 62.54);
		BdTestHarness.testParameterStatistics(result, "FL1-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 536.15);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 497.46);
		BdTestHarness.testParameterStatistics(result, "FL2-H", expectedParameterResults);
	}
}
