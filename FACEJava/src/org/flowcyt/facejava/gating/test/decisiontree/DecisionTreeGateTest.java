package org.flowcyt.facejava.gating.test.decisiontree;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests valid Decision Tree Gates.
 * 
 * @author echng
 */
public class DecisionTreeGateTest {
	public static final String DECISION_TREE_TEST_FILE_DIRECTORY = GateTestHarness.GATING_TEST_FILE_DIRECTORY + "decisiontree/";

	private static final String DECISION_TREE_TEST_FILE = DECISION_TREE_TEST_FILE_DIRECTORY + "simpleDecisionTrees.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(DECISION_TREE_TEST_FILE, GateTestHarness.FCS_DIRECTORY + "int-gating_test_file_4D.fcs");
		
		harness.addExpectedInsideEventCount("G1D-L",		0);
		harness.addExpectedInsideEventCount("G1D-G", 	1);
		harness.addExpectedInsideEventCount("G1D-E", 	1);
		harness.addExpectedInsideEventCount("G2D-LL",	1);
		harness.addExpectedInsideEventCount("G2D-LG", 	0);
		harness.addExpectedInsideEventCount("G2D-GL",	1);
		harness.addExpectedInsideEventCount("G2D-GG", 	0);
		harness.addExpectedInsideEventCount("G4D-LLLL",	1);
		harness.addExpectedInsideEventCount("G4D-LLLG", 	0);
		harness.addExpectedInsideEventCount("G4D-LLGL",	1);
		harness.addExpectedInsideEventCount("G4D-LLGG", 	0);
		harness.addExpectedInsideEventCount("G4D-LGLL",	1);
		harness.addExpectedInsideEventCount("G4D-LGLG", 	0);
		harness.addExpectedInsideEventCount("G4D-LGGL",	1);
		harness.addExpectedInsideEventCount("G4D-LGGG", 	0);
		harness.addExpectedInsideEventCount("G4D-GLLL",	1);
		harness.addExpectedInsideEventCount("G4D-GLLG", 	0);
		harness.addExpectedInsideEventCount("G4D-GLGL",	1);
		harness.addExpectedInsideEventCount("G4D-GLGG", 	0);
		harness.addExpectedInsideEventCount("G4D-GGLL",	1);
		harness.addExpectedInsideEventCount("G4D-GGLG", 	0);
		harness.addExpectedInsideEventCount("G4D-GGGL",	1);
		harness.addExpectedInsideEventCount("G4D-GGGG", 	0);
		
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}
}
