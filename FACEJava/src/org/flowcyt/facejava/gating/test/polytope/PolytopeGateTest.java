package org.flowcyt.facejava.gating.test.polytope;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests PolytopeGates with some basic cube Polytopes and in one dimension with some range
 * gates.
 * 
 * @author echng
 */
public class PolytopeGateTest {
	public static final String POLYTOPE_TEST_FILE_DIRECTORY = GateTestHarness.GATING_TEST_FILE_DIRECTORY + "polytope/";

	private static final String POLYTOPE_TEST_FILE = POLYTOPE_TEST_FILE_DIRECTORY + "PolytopeGates.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(POLYTOPE_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-gating_test_file_4D.fcs");
		
		harness.addExpectedInsideEventCount("OnePtLessThan", 					0);
		harness.addExpectedInsideEventCount("OnePtEqual", 						1);
		harness.addExpectedInsideEventCount("OnePtGreaterThan", 				0);
		harness.addExpectedInsideEventCount("TwoPtLessThan",					0);
		harness.addExpectedInsideEventCount("TwoPtRightBoundary", 				1);
		harness.addExpectedInsideEventCount("TwoPtWithin", 						1);
		harness.addExpectedInsideEventCount("TwoPtLeftBoundary", 				1);
		harness.addExpectedInsideEventCount("TwoPtGreaterThan", 				0);
		harness.addExpectedInsideEventCount("TwoPtLessThanWithRedundancy", 		0);
		harness.addExpectedInsideEventCount("TwoPtRightBoundaryWithRedundancy",	1);
		harness.addExpectedInsideEventCount("TwoPtWithinWithRedundancy", 		1);
		harness.addExpectedInsideEventCount("TwoPtLeftBoundaryWithRedundancy",	1);
		harness.addExpectedInsideEventCount("TwoPtGreaterThanWithRedundancy",	0);
		harness.addExpectedInsideEventCount("TriangleInside",					1);
		harness.addExpectedInsideEventCount("TriangleInsideWithRedundancy",		1);
		harness.addExpectedInsideEventCount("TriangleOutside",					0);
		harness.addExpectedInsideEventCount("TriangleOutsideWithRedundancy",	0);
		harness.addExpectedInsideEventCount("TriangleBoundary",					1);
		harness.addExpectedInsideEventCount("TriangleBoundaryWithRedundancy",	1);
		harness.addExpectedInsideEventCount("cube", 							0);
		harness.addExpectedInsideEventCount("cubeWithRedundancy",				0);
		harness.addExpectedInsideEventCount("cube2", 							1);
		harness.addExpectedInsideEventCount("cube2WithRedundancy",				1);
		harness.addExpectedInsideEventCount("cube3", 							0);
		harness.addExpectedInsideEventCount("cube3WithRedundancy",				0);
		harness.addExpectedInsideEventCount("cube4", 							1);
		harness.addExpectedInsideEventCount("cube4WithRedundancy",				1);
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
