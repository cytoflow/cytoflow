package org.flowcyt.facejava.transformation.test;

import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests pre-defined transformations. These tests simply test that the transformation
 * is performed correctly on given dummy events. 
 * 
 * @author echng
 */
public class SimpleTransformationTests {
	
	private static final String TRANSFORMATIONS_TEST_FILE = TransformationTestHarness.TRANSFORMATION_TEST_FILE_DIRECTORY + "SimpleTransformations.xml";
	
	private static final String EVENT_0_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "int-0_20_test_file.fcs";
	
	private static final String EVENT_1_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "int-1_20_test_file.fcs";
	
	private static final String EVENT_10_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "int-10_20_test_file.fcs";
	
	private static final String EVENT_1500_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "int-1500_20_test_file.fcs";
	
	private static final String EVENT_650_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "int-650_20_test_file.fcs";
	
	private static final String EVENT__5_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "double-0.5_20_test_file.fcs";
	
	private static final String EVENT_4_5_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "double-(-4.5)_20_test_file.fcs";
	
	private static final String EVENT_649_5_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "double-649.5_20_test_file.fcs";
	
	private static final String EVENT_649_7900106_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "double-649.7900106_20_test_file.fcs";
	
	private static TransformationTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new TransformationTestHarness(TRANSFORMATIONS_TEST_FILE);
	}
	
	@Test public void testLinear() throws Exception {
		// 3 * 10 + 5 = 35
		harness.testTransformation("Linear", EVENT_10_20_FCS_FILE, 35);
	}
	
	@Test public void testLn() throws Exception {
		// ln(10) * 1000 / 3 = 767.52836433134856133933048489479
		// We'll stop at 10 places after decimal.
		harness.testTransformation("Ln", EVENT_10_20_FCS_FILE, 767.5283643313);
	}
	
	@Test public void testLnLTOne() throws Exception {
		// < 1 then = 0.
		harness.testTransformation("Ln", EVENT__5_20_FCS_FILE, 0);
	}
	
	@Test public void testLnEqualOne() throws Exception {
		// ln(1) * 1000 / 3 = 0.
		harness.testTransformation("Ln", EVENT_1_20_FCS_FILE, 0);
	}
	
	@Test public void testLog() throws Exception {
		// log10(10) * 2000 / 5 = 400.
		harness.testTransformation("Log", EVENT_10_20_FCS_FILE, 400);
	}
	
	@Test public void testLogLTOne() throws Exception {
		// < 1 then = 0.
		harness.testTransformation("Log", EVENT__5_20_FCS_FILE, 0);
	}
	
	@Test public void testLogEqualOne() throws Exception {
		// log10(1) * 2000 / 5 = 0.
		harness.testTransformation("Log", EVENT_1_20_FCS_FILE, 0);
	}
	
	@Test public void testLog17() throws Exception {
		// log17(10) * 400 / 3 = 108.3615346.
		harness.testTransformation("Log17", EVENT_10_20_FCS_FILE, 108.3615346);
	}
	
	@Test public void testLog17LTOne() throws Exception {
		// < 1 then = 0.
		harness.testTransformation("Log17", EVENT__5_20_FCS_FILE, 0);
	}
	
	@Test public void testLog17EqualOne() throws Exception {
		// log17(1) * 400 / 3 = 0.
		harness.testTransformation("Log17", EVENT_1_20_FCS_FILE, 0);
	}
	
	@Test public void testQuadratic() throws Exception {
		// 3 * 10^2 + 2 * 10 + 1 = 341
		harness.testTransformation("Quadratic", EVENT_10_20_FCS_FILE, 321);
	}
	
	@Test public void testBiexponential() throws Exception {
		// root((0.5 * e^(1 * y) - 1.5 * e^(-2 * y) + 2.5) - 10) = 2.708937121
		harness.testTransformation("Biexponential", EVENT_10_20_FCS_FILE, 2.708937121);
	}
		
	@Test public void testSplitScaleBelowThreshold() throws Exception {
		// 10 < t = 649.7900106 => 0.049246678 * 10 + 32 = 32.49246678
		harness.testTransformation("SplitScale", EVENT_10_20_FCS_FILE, 32.49246678);
	}
	
	@Test public void testSplitScaleCloseBelowThreshold() throws Exception {
		// 649.5 < t = 649.7900106 => 0.049246678 * 649.5 + 32 = 63.98571794
		harness.testTransformation("SplitScale", EVENT_649_5_20_FCS_FILE, 63.98571794);
	}
	
	@Test public void testSplitScaleEqualThreshold() throws Exception {
		// 649.7900106 = t =>  0.049246678 * 649.7900106 + 32 = 64
		harness.testTransformation("SplitScale", EVENT_649_7900106_20_FCS_FILE, 64);
	}
	
	@Test public void testSplitScaleCloseAboveThreshold() throws Exception {
		// 650 > t = 649.7900106 => log(.011371452 * 650) * 192 / 2.605766891 = 64.01033961
		harness.testTransformation("SplitScale", EVENT_650_20_FCS_FILE, 64.01033961);
	}
	
	@Test public void testSplitScaleAboveThreshold() throws Exception {
		// 1500 > t = 649.7900106 => log(.011371452 * 1500) * 192 / 2.605766891 = 90.77027638
		harness.testTransformation("SplitScale", EVENT_1500_20_FCS_FILE, 90.77027638);
	}
	
	@Test public void testHyperlogRootLTZero() throws Exception {
		// root((-10^(-y * 3 /1000) + 35 * 3 / 1000 * y - 1) - (-4.5)) = -39.8399952
		harness.testTransformation("Hyperlog", EVENT_4_5_20_FCS_FILE, -39.8399952);
	}
	
	@Test public void testHyperlogRootEqualZero() throws Exception {
		// root((10^(y * 3 /1000) + 35 * 3 / 1000 * y - 1) - 0) = 0
		harness.testTransformation("Hyperlog", EVENT_0_20_FCS_FILE, 0);
	}
	
	@Test public void testHyperlogRootGTZero() throws Exception {
		// root((10^(y * 3 /1000) + 35 * 3 / 1000 * y - 1) - 10) = 87.34948401
		harness.testTransformation("Hyperlog", EVENT_10_20_FCS_FILE, 87.34948401);
	}
	
	@Test public void testLogicleRootLTW() throws Exception {
		// root(-(10000 * e^-(10.36 - .48655813) * (e^(.48655813 - y) - (1.5^2) * e^(-(.48655813 - y)/1.5) + 1.5^2 - 1) - (-4.5)) = -1.5983752
		harness.testTransformation("Logicle", EVENT_4_5_20_FCS_FILE, -1.5983752);
	}
	
	@Test public void testLogicleRootEqualW() throws Exception {
		// root((10000 * e^-(10.36 - .48655813) * (e^(y - .48655813) - (1.5^2) * e^(-(y - .48655813)/1.5) + 1.5^2 - 1) - 0) = 0.48655813
		harness.testTransformation("Logicle", EVENT_0_20_FCS_FILE, .48655813);
	}
	
	@Test public void testLogicleRootGTW() throws Exception {
		// root((10000 * e^-(10.36 - .48655813) * (e^(y - .48655813) - (1.5^2) * e^(-(y - .48655813)/1.5) + 1.5^2 - 1) - 10) = 3.403242878
		harness.testTransformation("Logicle", EVENT_10_20_FCS_FILE, 3.403242878);
	}
	
}
