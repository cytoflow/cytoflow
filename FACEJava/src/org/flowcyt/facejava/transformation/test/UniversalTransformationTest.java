package org.flowcyt.facejava.transformation.test;

import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests universal transformations. At least, what can be handled by MathJ.
 * 
 * @author echng
 */
public class UniversalTransformationTest {
	private static final String TRANSFORMATIONS_TEST_FILE = TransformationTestHarness.TRANSFORMATION_TEST_FILE_DIRECTORY + "UniversalTransformations.xml";
	
	private static final String EVENT_10_4_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "int-10_4_test_file.fcs";
	
	private static TransformationTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new TransformationTestHarness(TRANSFORMATIONS_TEST_FILE);
	}
	
	@Test public void testSum() throws Exception {
		harness.testTransformation("PiApprox", EVENT_10_4_FCS_FILE, 3.141592653589793);
	}
	
	@Test public void testRoot() throws Exception {
		harness.testTransformation("squareroot FS", EVENT_10_4_FCS_FILE, Math.sqrt(10));
	}
	
	@Test(expected=DataRetrievalException.class)
	public void testNotImplemented() throws Exception {
		harness.testTransformation("MathML log FS", EVENT_10_4_FCS_FILE, 3.1415926354);
	}
	
	@Test public void testPowerFactorial() throws Exception {
		harness.testTransformation("FS squared/fact SS", EVENT_10_4_FCS_FILE, Math.pow(10, 2)/24);
	}
	
	@Test public void testRootAsPower() throws Exception {
		harness.testTransformation("fourthroot SS", EVENT_10_4_FCS_FILE, Math.sqrt(2));
	}
	
	
	@Test public void testArithmetic() throws Exception {
		harness.testTransformation("arithmetic", EVENT_10_4_FCS_FILE, 4.8);
	}
	
	@Test public void testMultipleApplies() throws Exception {
		harness.testTransformation("multiple apply", EVENT_10_4_FCS_FILE, 100.0);
	}
}
