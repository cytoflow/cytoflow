package org.flowcyt.facejava.compensation.test;

import java.util.HashSet;
import java.util.Set;

import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Runs test for copmensation when only one parameter is to be compensated. See the comments of
 * the CompensationML test file for the expected results. 
 * 
 * @author echng
 */
public class OneParameterCompensatorTests {
	private static final String MATRIX_FILE_URI = CompensatorTestHarness.TEST_FILE_DIRECTORY + "OneParameterCompensation.xml";
	
	private static CompensatorTestHarness harness;
	
	private Set<String> expectedReferences;
	
	@BeforeClass public static void oneTimeSetup() throws Exception {
		harness = new CompensatorTestHarness(MATRIX_FILE_URI);
	}
	
	@Before public void setUp() {
		expectedReferences = new HashSet<String>();
	}
	
	@Test public void testSSubD() throws Exception {
		expectedReferences.add("AS");
		
		double[][] expectedEventsData = {
			{10.0, 20.0},
			{30.0, 40.0},
			{50.0, 60.0},
			{70.0, 80.0},
			{90.0, 100.0},
			{110.0, 120.0},
			{130.0, 140.0},
			{150.0, 160.0},
			{170.0, 180.0},
			{190.0, 200.0}
		};
		
		harness.runTestSequence("S-Sub-D", 
				CompensatorTestHarness.FCS_TEST_FILE_DIRECTORY + "int-10_events_2_parameters.fcs", 
				expectedEventsData,
				expectedReferences);
	}
	
	@Test public void testDIntS() throws Exception {
		expectedReferences.add("BS");
		
		double[][] expectedEventsData = {
			{10.0, 20.2634245187437},
			{30.0, 40.5268490374873},
			{50.0, 60.790273556231},
			{70.0, 81.0536980749747},
			{90.0, 101.317122593718},
			{110.0, 121.580547112462},
			{130.0, 141.843971631206},
			{150.0, 162.107396149949},
			{170.0, 182.370820668693},
			{190.0, 202.634245187437}
		};
		
		harness.runTestSequence("D-Int-S", 
				CompensatorTestHarness.FCS_TEST_FILE_DIRECTORY + "int-10_events_2_parameters.fcs", 
				expectedEventsData,
				expectedReferences);
	}
}
