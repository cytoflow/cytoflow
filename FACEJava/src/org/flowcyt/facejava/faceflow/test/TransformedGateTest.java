 package org.flowcyt.facejava.faceflow.test;

import org.flowcyt.facejava.faceflow.application.outputlayers.OutputLayer;
import org.junit.Assert;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests pre-defined transformations with actual gates. That is, that we gate
 * correctly when transformations are used in a gate. 
 * 
 * @author echng
 */
public class TransformedGateTest {
	private static final String TRANSFORMED_GATE_TRANSFORMATIONS_TEST_FILE = TestFileConstants.TRANSFORMATIONS_TEST_FILE_DIRECTORY + "TransformedGatesTransformations.xml";
	
	private static final String TRANSFORMED_GATE_FCS_TEST_FILE = TestFileConstants.FCS_TEST_FILE_DIRECTORY + "int-10000_events_random.fcs";
	
	private static final String TRANSFORMED_GATE_GATING_TEST_FILE = TestFileConstants.GATING_TEST_FILE_DIRECTORY + "TransformedGates.xml";
	
	private static OutputLayersTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new OutputLayersTestHarness();
		
		harness.setFcsFile(TRANSFORMED_GATE_FCS_TEST_FILE);
		harness.setTransformationFile(TRANSFORMED_GATE_TRANSFORMATIONS_TEST_FILE);
		harness.setGatingFile(TRANSFORMED_GATE_GATING_TEST_FILE);
	}
	
	@Test public void testMeanRectGate() throws Exception {
		OutputLayer result = harness.getFinalLayer(1, null, "MeanRectGate");
		Assert.assertEquals(96, result.getResultPopulation().size());
	}
}
