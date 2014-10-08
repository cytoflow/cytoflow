package org.flowcyt.facejava.gating.test.bool;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

public class LargeBooleanGateTest {
	private static final String BOOLEAN_TEST_FILE = BooleanGateTest.BOOLEAN_TEST_FILE_DIRECTORY + "LargeBooleanGates.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(BOOLEAN_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-10000_events_random.fcs");
		
		harness.addExpectedInsideEventCount("Rect1", 	1836);
		harness.addExpectedInsideEventCount("Rect2", 	803);
		harness.addExpectedInsideEventCount("Rect3", 	107);
		harness.addExpectedInsideEventCount("Rect4", 	29);
		harness.addExpectedInsideEventCount("Rect5", 	30);
		harness.addExpectedInsideEventCount("Rect6", 	4);
		harness.addExpectedInsideEventCount("Rect7", 	4182);
		harness.addExpectedInsideEventCount("Rect8", 	626);
		harness.addExpectedInsideEventCount("Rect9", 	1016);
		harness.addExpectedInsideEventCount("Rect10", 	6346);
		harness.addExpectedInsideEventCount("Bool1", 	9248);	
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
