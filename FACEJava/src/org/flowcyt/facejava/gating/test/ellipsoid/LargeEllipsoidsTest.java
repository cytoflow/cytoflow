package org.flowcyt.facejava.gating.test.ellipsoid;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

public class LargeEllipsoidsTest {
private static final String ELLIPSOID_GATE_TEST_FILE = EllipsoidGateTest.ELLIPSOID_TEST_FILE_DIRECTORY + "LargeEllipsoids.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(ELLIPSOID_GATE_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-10000_events_random.fcs");
		
		harness.addExpectedInsideEventCount("ellipse", 			4612);
		harness.addExpectedInsideEventCount("ellipsoid", 		7921);
		harness.addExpectedInsideEventCount("hyper-ellipsoid",	422);
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
