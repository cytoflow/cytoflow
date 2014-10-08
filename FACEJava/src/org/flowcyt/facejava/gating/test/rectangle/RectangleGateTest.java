package org.flowcyt.facejava.gating.test.rectangle;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Basic RectangleGate test. Tests all cases that an event can be in the range [min, max)
 * for a single dimension, then checks that it handles multiple dimensions correctly.
 * 
 * @author echng
 */
public class RectangleGateTest {

	public static final String RECTANGLE_TEST_FILE_DIRECTORY = GateTestHarness.GATING_TEST_FILE_DIRECTORY + "rectangle/";
	
	private static final String RECTANGLE_TEST_FILE = RECTANGLE_TEST_FILE_DIRECTORY + "SimpleRectangles.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(RECTANGLE_TEST_FILE);
		
		harness.addExpectedInsideEventCount("LessThanMin", 					0);
		harness.addExpectedInsideEventCount("EqualToMin", 					1);
		harness.addExpectedInsideEventCount("GreaterThanMin", 				1);
		harness.addExpectedInsideEventCount("LessThanMax",					1);
		harness.addExpectedInsideEventCount("EqualToMax", 					0);
		harness.addExpectedInsideEventCount("GreaterThanMax", 				0);
		harness.addExpectedInsideEventCount("BetweenMinAndMax", 			1);
		harness.addExpectedInsideEventCount("EqualToMinAndLessThanMax", 	1);
		harness.addExpectedInsideEventCount("GreaterThanMinAndEqualToMax", 	0);
		harness.addExpectedInsideEventCount("EqualToMinAndMax", 			0);
		harness.addExpectedInsideEventCount("GreaterThanMinAndMax", 		0);
		harness.addExpectedInsideEventCount("LessThanMinAndMax", 			0);
		harness.addExpectedInsideEventCount("MinGreaterThanMax", 			0);
		harness.addExpectedInsideEventCount("InNoDimensions", 				0);
		harness.addExpectedInsideEventCount("InOneDimensions", 				0);
		harness.addExpectedInsideEventCount("InAllDimensions", 				1);
				
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
