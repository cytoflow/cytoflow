package org.flowcyt.facejava.gating.test.rectangle;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests RectangleGates with many events. 
 * 
 * @author echng
 */
public class LargeRectangleGateTest {

	private static final String LARGE_RECTANGLE_GATE_TEST_FILE = RectangleGateTest.RECTANGLE_TEST_FILE_DIRECTORY + "LargeRectangleTest.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(LARGE_RECTANGLE_GATE_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-homogenous_matrix.fcs");
		
		harness.addExpectedInsideEventCount("Gate01", 300);
		harness.addExpectedInsideEventCount("Gate02", 250);
		harness.addExpectedInsideEventCount("Gate03", 550);
		harness.addExpectedInsideEventCount("Gate04", 500);
		harness.addExpectedInsideEventCount("Gate05", 150);
		harness.addExpectedInsideEventCount("Gate06", 50);
		harness.addExpectedInsideEventCount("Gate07", 100);
		harness.addExpectedInsideEventCount("Gate08", 0);
		harness.addExpectedInsideEventCount("Gate11", 975);
		harness.addExpectedInsideEventCount("Gate12", 950);
		harness.addExpectedInsideEventCount("Gate13", 800);
		harness.addExpectedInsideEventCount("Gate14", 775);
		harness.addExpectedInsideEventCount("Gate15", 125);
		harness.addExpectedInsideEventCount("Gate16", 100);
		harness.addExpectedInsideEventCount("Gate17", 25);
		harness.addExpectedInsideEventCount("Gate18", 0);
		harness.addExpectedInsideEventCount("Gate21", 18);
		harness.addExpectedInsideEventCount("Gate22", 10);
		harness.addExpectedInsideEventCount("Gate23", 240);
		harness.addExpectedInsideEventCount("Gate24", 228);
		harness.addExpectedInsideEventCount("Gate25", 228);
		harness.addExpectedInsideEventCount("Gate26", 228);
		harness.addExpectedInsideEventCount("Gate27", 160);
		harness.addExpectedInsideEventCount("Gate28", 133);
		harness.addExpectedInsideEventCount("Gate29", 128);
		harness.addExpectedInsideEventCount("Gate30", 105);
		harness.addExpectedInsideEventCount("Gate31", 231);
		harness.addExpectedInsideEventCount("Gate32", 200);
		harness.addExpectedInsideEventCount("Gate33", 110);
		harness.addExpectedInsideEventCount("Gate34", 90);
		harness.addExpectedInsideEventCount("Gate35", 88);
		harness.addExpectedInsideEventCount("Gate36", 70);
		harness.addExpectedInsideEventCount("Gate37", 88);
		harness.addExpectedInsideEventCount("Gate38", 88);
		harness.addExpectedInsideEventCount("Gate39", 88);
		harness.addExpectedInsideEventCount("Gate40", 88);
		harness.addExpectedInsideEventCount("Gate41", 88);
		harness.addExpectedInsideEventCount("Gate42", 88);
		harness.addExpectedInsideEventCount("Gate43", 560);
		harness.addExpectedInsideEventCount("Gate44", 525);
		harness.addExpectedInsideEventCount("Gate45", 150);
		harness.addExpectedInsideEventCount("Gate46", 135);
		harness.addExpectedInsideEventCount("Gatep1", 550);
		harness.addExpectedInsideEventCount("Gatep2", 550);
		harness.addExpectedInsideEventCount("Gatep3", 550);
		harness.addExpectedInsideEventCount("Gatep4", 500);
		harness.addExpectedInsideEventCount("Gatep5", 500);
		harness.addExpectedInsideEventCount("Gatep6", 500);
		harness.addExpectedInsideEventCount("Gatep7", 500);	
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
