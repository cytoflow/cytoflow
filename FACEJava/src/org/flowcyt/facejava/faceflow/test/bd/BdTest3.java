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

public class BdTest3 {
	private static OutputLayersTestHarness harness;
	
	private Map<PopulationStatisticType, Double> expectedGateResults;
	
	private Map<ParameterStatisticType, Double> expectedParameterResults;
		
	@BeforeClass
	public static void oneTimeSetUp() throws Exception {
		harness = new OutputLayersTestHarness();
		
		harness.setFcsFile(TestFileConstants.FCS_TEST_FILE_DIRECTORY + "120403pep48hrp04253.H09");
		harness.setTransformationFile(TestFileConstants.TRANSFORMATIONS_TEST_FILE_DIRECTORY + "BDGatingTestTransformations3.xml");
		harness.setGatingFile(TestFileConstants.GATING_TEST_FILE_DIRECTORY + "BDGatingTest3.xml");
	}
	
	@Before
	public void setUp() {
		expectedGateResults = new HashMap<PopulationStatisticType, Double>();
		expectedParameterResults = new HashMap<ParameterStatisticType, Double>();
	}
	
	@Test public void testR1() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R1");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 17459.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 74.71);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 199.86);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 0.0);
		BdTestHarness.testParameterStatistics(result, "SSC-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 11.04);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 7.39);
		BdTestHarness.testParameterStatistics(result, "FL3-H", expectedParameterResults);
	}
	
	@Test public void testR2() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R2");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 579.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 2.48);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 940.25);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 938.24);
		BdTestHarness.testParameterStatistics(result, "SSC-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 360.13);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 354.56);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
	
	@Test public void testR3() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R3");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 5408.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 23.14);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 216.34);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 167.22);
		BdTestHarness.testParameterStatistics(result, "SSC-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 439.59);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 434.71);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
	}
     
	@Test public void testR3FilteredWithR4() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R3-filtered-R4");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 253.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 1.08);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 388.98);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 385.78);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 1313.93);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 1205.88);
		BdTestHarness.testParameterStatistics(result, "FL3-H", expectedParameterResults);
	}
     
	@Test public void testR5() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R5");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 2214.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 9.47);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 327.06);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 313.33);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 657.30);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 644.74);
		BdTestHarness.testParameterStatistics(result, "SSC-H", expectedParameterResults);
	}
     
	@Test public void testR6() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R6");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 1795.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 7.68);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 445.16);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 418.28);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 679.05);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 676.53);
		BdTestHarness.testParameterStatistics(result, "SSC-H", expectedParameterResults);
	}
     
	@Test public void testR7() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R7");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 19.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 0.08);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 645.47);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 645.31);
		BdTestHarness.testParameterStatistics(result, "FSC-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 839.05);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 838.94);
		BdTestHarness.testParameterStatistics(result, "SSC-H", expectedParameterResults);
	}
     
	@Test public void testR11() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "R11");
		
		expectedGateResults.put(PopulationStatisticType.EVENT_COUNT, 2463.0);
		expectedGateResults.put(PopulationStatisticType.PERCENT_OF_PARENT, 10.54);
		BdTestHarness.testGatingStatistics(result, expectedGateResults);
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 32.51);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 26.51);
		BdTestHarness.testParameterStatistics(result, "FL2-H", expectedParameterResults);
		
		expectedParameterResults.clear();
		
		expectedParameterResults.put(ParameterStatisticType.MEAN, 355.42);
		expectedParameterResults.put(ParameterStatisticType.GEOMETRIC_MEAN, 263.07);
		BdTestHarness.testParameterStatistics(result, "SSC-H", expectedParameterResults);
	}
}
