package org.flowcyt.facejava.gating.test.polygon;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests valid Polygon gates.
 * 
 * @author echng
 */
public class PolygonGateTest {
	public static final String POLYGON_TEST_FILE_DIRECTORY = GateTestHarness.GATING_TEST_FILE_DIRECTORY + "polygon/";

	private static final String POLYGON_TEST_FILE = POLYGON_TEST_FILE_DIRECTORY + "PolygonGates.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(POLYGON_TEST_FILE);
		
		harness.addExpectedInsideEventCount("RectangleInside", 					1);
		harness.addExpectedInsideEventCount("RectangleBoundary", 				1);
		harness.addExpectedInsideEventCount("RectangleOutside", 				0);
		harness.addExpectedInsideEventCount("SimpleConcaveInside", 				1);
		harness.addExpectedInsideEventCount("SimpleConcaveBoundary", 			1);
		harness.addExpectedInsideEventCount("SimpleConcaveOutside", 			0);
		harness.addExpectedInsideEventCount("ConcaveInside", 					1);
		harness.addExpectedInsideEventCount("ConcaveBoundary", 					1);
		harness.addExpectedInsideEventCount("ConcaveOutside", 					0);
		harness.addExpectedInsideEventCount("NonSimpleTopInside", 				1);
		harness.addExpectedInsideEventCount("NonSimpleBottomInside", 			1);
		harness.addExpectedInsideEventCount("NonSimpleLeftOutside", 			0);
		harness.addExpectedInsideEventCount("NonSimpleRightOutside", 			0);
		harness.addExpectedInsideEventCount("NonSimpleBoundaryCrossingPoint",	1);
		harness.addExpectedInsideEventCount("NonSimpleBoundaryForwardSlant", 	1);
		harness.addExpectedInsideEventCount("NonSimpleBoundaryBackSlant", 		1);		
		harness.addExpectedInsideEventCount("ComplicatedNonSimple1", 			0);		
		harness.addExpectedInsideEventCount("ComplicatedNonSimple2", 			0);		
		harness.addExpectedInsideEventCount("ComplicatedNonSimple3", 			1);		
		harness.addExpectedInsideEventCount("ComplicatedNonSimple4", 			1);
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
