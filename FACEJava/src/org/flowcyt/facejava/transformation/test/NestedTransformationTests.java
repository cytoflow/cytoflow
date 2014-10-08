package org.flowcyt.facejava.transformation.test;

import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests nested transformations. From SimpleTransformationTests we know that transformations
 * are caluculated correctly, so now we test that transformations on transformations are
 * ok too.
 * 
 * @author echng
 */
public class NestedTransformationTests {
	
	private static final String TRANSFORMATIONS_TEST_FILE = TransformationTestHarness.TRANSFORMATION_TEST_FILE_DIRECTORY + "NestedTransformations.xml";
	
	private static final String EVENT_10_20_FCS_FILE = TransformationTestHarness.FCS_FILE_DIR + "int-10_20_test_file.fcs";

	private static final double RELAXED_EPSILON = 0.000005;
	
	private static TransformationTestHarness harness;
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		harness = new TransformationTestHarness(TRANSFORMATIONS_TEST_FILE);
	}
	
	@Test public void test2deep() throws Exception {
		// a: root((0.5 * e^(1 * y) - 1.5 * e^(-2 * y) + 2.5) - 10) = 2.708937121
		// b: 3 * 2.708937121 + 5 = 13.126811363
		harness.testTransformation("b-2deep", EVENT_10_20_FCS_FILE, 13.126811363);
	}
	
	@Test public void test4deep() throws Exception {
		// a: root((10^(y * 3 /1000) + 35 * 3 / 1000 * y - 1) - 10) = 87.34948401
		// b: 87.34948401 < t = 649.7900106 => 0.049246678 * 87.34948401 + 32 = 36.30167191250661878
		// c: ln(36.30167191250661878) * 1000 / 3 = 1197.2879328019778620131511418328
		// d: log10(1197.2879328019778620131511418328) * 2000 / 5 = 1231.2794421474116452230074312062
		harness.testTransformation("d-4deep", EVENT_10_20_FCS_FILE, 1231.27944, RELAXED_EPSILON);
	}
	
	@Test public void test8deep() throws Exception {
		// a: root((10000 * e^-(10.36 - .48655813) * (e^(y - .48655813) - (1.5^2) * e^(-(y - .48655813)/1.5) + 1.5^2 - 1) - 10) = 3.403242878
		// b: 3 * 3.403242878^2 + 2 * 3.403242878 + 1 = 42.552672015973168652
		// c: ln(42.552672015973168652) * 1000 / 3 = 1250.2475500442931939961448715176
		// d: log10(1250.2475500442931939961448715176) * 2000 / 5 = 1238.7984048749129442552219116953
		// e: 3 * 1238.7984048749129442552219116953 + 5 = 3721.395214624738832765665735086
		// f: 3721.395214624738832765665735086 > t = 649.7900106 => log(.011371452 * 3721.395214624738832765665735086) * 192 / 2.605766891 = 119.84654913154187084339340661727
		// g: 0.25 * 119.84654913154187084339340661727 ^ 2 + 12.3 * 119.84654913154187084339340661727 + 6.33
		// h: log7(5071.2413890027349004917644638532) * 500 / 3 = 730.70699253149303018441107495513
		harness.testTransformation("h-8deep", EVENT_10_20_FCS_FILE, 730.70699, RELAXED_EPSILON);
	}
}
