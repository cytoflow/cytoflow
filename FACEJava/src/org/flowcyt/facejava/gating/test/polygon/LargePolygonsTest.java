package org.flowcyt.facejava.gating.test.polygon;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

public class LargePolygonsTest {
	private static final String POLYGON_TEST_FILE = PolygonGateTest.POLYGON_TEST_FILE_DIRECTORY + "LargePolygons.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(POLYGON_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-10000_events_random.fcs");
		
		harness.addExpectedInsideEventCount("G10pts", 	1180);
		harness.addExpectedInsideEventCount("G100pts", 	3620);
		harness.addExpectedInsideEventCount("G250pts",	4559);
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
