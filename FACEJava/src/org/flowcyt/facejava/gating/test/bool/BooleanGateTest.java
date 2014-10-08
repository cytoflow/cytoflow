package org.flowcyt.facejava.gating.test.bool;

import org.flowcyt.facejava.gating.test.GateTestHarness;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests valid Boolean Gates
 * 
 * @author echng
 */
public class BooleanGateTest {
	public static final String BOOLEAN_TEST_FILE_DIRECTORY = GateTestHarness.GATING_TEST_FILE_DIRECTORY + "bool/";
	
	private static final String BOOLEAN_TEST_FILE = BOOLEAN_TEST_FILE_DIRECTORY + "SimpleBooleanGates.xml";
	
	private static GateTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new GateTestHarness(BOOLEAN_TEST_FILE);
		
		harness.addExpectedInsideEventCount("AndTwoArg0In", 				0);
		harness.addExpectedInsideEventCount("AndTwoArg1In", 				0);
		harness.addExpectedInsideEventCount("AndTwoArgAllIn", 				1);
		harness.addExpectedInsideEventCount("AndManyArgs0In", 				0);
		harness.addExpectedInsideEventCount("AndManyArgs1In", 				0);
		harness.addExpectedInsideEventCount("AndManyArgsSomeIn", 			0);
		harness.addExpectedInsideEventCount("AndManyArgsAllIn", 			1);
		harness.addExpectedInsideEventCount("OrTwoArg0In", 					0);
		harness.addExpectedInsideEventCount("OrTwoArg1In", 					1);
		harness.addExpectedInsideEventCount("OrTwoArgAllIn", 				1);
		harness.addExpectedInsideEventCount("OrManyArgs0In", 				0);
		harness.addExpectedInsideEventCount("OrManyArgs1In", 				1);
		harness.addExpectedInsideEventCount("OrManyArgsSomeIn", 			1);
		harness.addExpectedInsideEventCount("OrManyArgsAllIn", 				1);
		harness.addExpectedInsideEventCount("NotEventInReferencedGate", 	0);
		harness.addExpectedInsideEventCount("NotEventNotInReferencedGate",	1);
		harness.addExpectedInsideEventCount("AndMixedTwoArg1In", 			0);
		harness.addExpectedInsideEventCount("AndAllDefinedTwoArgAllIn", 	1);
		harness.addExpectedInsideEventCount("OrMixedTwoArg1In", 			1);
		harness.addExpectedInsideEventCount("OrAllDefinedTwoArg0In", 		0);
		harness.addExpectedInsideEventCount("NotEventNotInDefinedGate", 	1);
		harness.addExpectedInsideEventCount("XorBothIn", 					0);
		harness.addExpectedInsideEventCount("XorBothOut", 					0);
		harness.addExpectedInsideEventCount("XorOneIn", 					1);
		harness.addExpectedInsideEventCount("XorOtherIn", 					1);
	}
	
	@Test public void testNoErrors() {
		harness.testNoErrors();
	}
	
	@Test public void testInsideEventCountsCorrect() {
		harness.testInsideEventCountsCorrect();
	}

}
