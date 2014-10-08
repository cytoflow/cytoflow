package org.flowcyt.facejava.gating.test.polytope;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Test Polytopes on data with many events and on gates with many points.
 * 
 * @author echng
 *
 */
public class LargePolytopeGateTest {
	private static final String POLYTOPE_TEST_FILE = PolytopeGateTest.POLYTOPE_TEST_FILE_DIRECTORY + "LargePolytopeGates.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(POLYTOPE_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-10000_events_random.fcs");
		
		harness.addExpectedInsideEventCount("G1D10ptsV1", 	9123);
		harness.addExpectedInsideEventCount("G2D10ptsV1", 	2731);
		harness.addExpectedInsideEventCount("G2D100ptsV1", 	8964);
		harness.addExpectedInsideEventCount("G10ptsV1", 	8);
		harness.addExpectedInsideEventCount("G10ptsV2",		26);
		harness.addExpectedInsideEventCount("G100ptsV1", 	1306);
		harness.addExpectedInsideEventCount("G100ptsV2",	1408);
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
