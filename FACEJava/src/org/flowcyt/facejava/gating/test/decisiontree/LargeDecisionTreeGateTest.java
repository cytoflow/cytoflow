package org.flowcyt.facejava.gating.test.decisiontree;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

public class LargeDecisionTreeGateTest {
	private static final String DTREE_TEST_FILE = DecisionTreeGateTest.DECISION_TREE_TEST_FILE_DIRECTORY + "LargeDecisionTrees.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(DTREE_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-10000_events_random.fcs");
		
		harness.addExpectedInsideEventCount("dtree1", 	7136);
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
