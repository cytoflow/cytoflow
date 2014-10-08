package org.flowcyt.facejava.gating.test.polygon;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests complicated Polygon gates (i.e., many vertices).
 * 
 * @author echng
 */
public class ComplicatedPolygonGateTest {
	private static final String POLYGON_TEST_FILE = PolygonGateTest.POLYGON_TEST_FILE_DIRECTORY + "ComplicatedPolygons.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(POLYGON_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-15_scatter_events.fcs");
		
		harness.addExpectedInsideEventCount("G1i1", 	10);
		harness.addExpectedInsideEventCount("G1i2", 	10);
		harness.addExpectedInsideEventCount("G1i3", 	10);
		harness.addExpectedInsideEventCount("G1i4", 	10);
		harness.addExpectedInsideEventCount("G2i1", 	10);
		harness.addExpectedInsideEventCount("G2i2", 	10);
		harness.addExpectedInsideEventCount("G3i1", 	10);
		harness.addExpectedInsideEventCount("G3i2", 	10);
		harness.addExpectedInsideEventCount("G3i3", 	10);
		harness.addExpectedInsideEventCount("G3i4", 	10);
		harness.addExpectedInsideEventCount("G3i5", 	10);
		harness.addExpectedInsideEventCount("G3i6", 	10);
		harness.addExpectedInsideEventCount("G3i7", 	10);
		harness.addExpectedInsideEventCount("G4i1", 	8);
		harness.addExpectedInsideEventCount("G4i2", 	8);
		harness.addExpectedInsideEventCount("G4i3", 	8);
		harness.addExpectedInsideEventCount("G4i4", 	10);
		harness.addExpectedInsideEventCount("G5i1",		5);
		harness.addExpectedInsideEventCount("G5i2", 	5);
		harness.addExpectedInsideEventCount("G5i3", 	5);
		harness.addExpectedInsideEventCount("G5i4", 	5);
		harness.addExpectedInsideEventCount("G5i5", 	5);
		harness.addExpectedInsideEventCount("G6i4", 	7);
		harness.addExpectedInsideEventCount("G6i8", 	3);
		harness.addExpectedInsideEventCount("G6i16", 	4);
		harness.addExpectedInsideEventCount("G6i100", 	7);
		harness.addExpectedInsideEventCount("G6i101", 	6);
		harness.addExpectedInsideEventCount("G6i1000", 	7);
		harness.addExpectedInsideEventCount("G6i1024", 	4);
		harness.addExpectedInsideEventCount("G6i2347", 	3);
		harness.addExpectedInsideEventCount("G6i10000", 7);
		harness.addExpectedInsideEventCount("G7i1", 	8);
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
