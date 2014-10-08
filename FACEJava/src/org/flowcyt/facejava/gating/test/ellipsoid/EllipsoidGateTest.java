package org.flowcyt.facejava.gating.test.ellipsoid;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests valid Ellipsoid Gates
 * 
 * @author echng
 */
public class EllipsoidGateTest {
	public static final String ELLIPSOID_TEST_FILE_DIRECTORY = GateTestHarness.GATING_TEST_FILE_DIRECTORY + "ellipsoid/";
	
	private static final String ELLIPSOID_GATE_TEST_FILE = ELLIPSOID_TEST_FILE_DIRECTORY + "SimpleEllipsoids.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(ELLIPSOID_GATE_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-gating_test_file_4D.fcs");
		
		harness.addExpectedInsideEventCount("WithinDistanceLimit", 			1);
		harness.addExpectedInsideEventCount("WithinDistanceLimitSmall", 	1);
		harness.addExpectedInsideEventCount("EqualDistanceLimit",	 		1);
		harness.addExpectedInsideEventCount("OutsideDistanceLimitSmall", 	0);
		harness.addExpectedInsideEventCount("OutsideDistanceLimit", 		0);
		harness.addExpectedInsideEventCount("CloserFoci", 					1);
		harness.addExpectedInsideEventCount("CloserFociSmall", 				1);
		harness.addExpectedInsideEventCount("FartherFociSmall", 			0);
		harness.addExpectedInsideEventCount("FartherFoci", 					0);
		harness.addExpectedInsideEventCount("WithinDistanceLimit4D", 		1);
		harness.addExpectedInsideEventCount("WithinDistanceLimit4DSmall", 	1);
		harness.addExpectedInsideEventCount("EqualDistanceLimit4D", 		1);
		harness.addExpectedInsideEventCount("OutsideDistanceLimit4DSmall", 	0);
		harness.addExpectedInsideEventCount("OutsideDistanceLimit4D",		0);
		harness.addExpectedInsideEventCount("CloserFoci4D", 				1);
		harness.addExpectedInsideEventCount("CloserFociSmall4D", 			1);
		harness.addExpectedInsideEventCount("FartherFociSmall4D", 			0);
		harness.addExpectedInsideEventCount("FartherFoci4D", 				0);
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
