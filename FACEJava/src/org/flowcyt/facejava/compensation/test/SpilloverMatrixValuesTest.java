package org.flowcyt.facejava.compensation.test;

import org.flowcyt.facejava.compensation.SpilloverMatrix;
import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.compensation.xmlio.CompensationMLFileReader;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.junit.Assert;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests that the expected values are returned from a spillover matrix for two given parameter
 * references.
 * 
 * @author echng
 */
public class SpilloverMatrixValuesTest {
	private static double EPSILON = 0.000005;
	
	private static final String SPILLOVER_MATRIX_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "SpilloverMatrixValueTest.xml";
	
	private static final String BASIC_TEST_MATRIX_ID = "BasicTestMatrix";
	
	private static final String MULTIPLE_VALUES_MATRIX_ID = "MultipleValuesSpecifiedMatrix";
	
	private static SpilloverMatrixSet coll;
	
	@BeforeClass public static void oneTimeSetup() throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader(SPILLOVER_MATRIX_TEST_FILE);
		coll = reader.read();		
	}
	
	public double getSpilloverValue(String matrixId, String firstParam, String secondParam) {
		SpilloverMatrix matrix = coll.get(matrixId);
		return matrix.getSpilloverValue(new ParameterReference(firstParam), new ParameterReference(secondParam));		
	}
	
	@Test public void testDifferentParametersBothNotSpecified() {
		Assert.assertEquals(0, getSpilloverValue(BASIC_TEST_MATRIX_ID, "NotSpecified1", "NotSpecified2"), EPSILON);
	}
	
	@Test public void testDifferentParametersFirstNotSpecified() {
		Assert.assertEquals(0, getSpilloverValue(BASIC_TEST_MATRIX_ID, "NotSpecified1", "Fluor"), EPSILON);
	}
	
	@Test public void testDifferentParametersSecondNotSpecified() {
		Assert.assertEquals(0, getSpilloverValue(BASIC_TEST_MATRIX_ID, "Cy5PE", "NotSpecified2"), EPSILON);
	}
	
	@Test public void testSameParameterSelfNotSpecified() {
		Assert.assertEquals(1, getSpilloverValue(BASIC_TEST_MATRIX_ID, "Cy5PE", "Cy5PE"), EPSILON);
	}
	
	@Test public void testSameParameterBothNotSpecified() {
		Assert.assertEquals(1, getSpilloverValue(BASIC_TEST_MATRIX_ID, "NotSpecified1", "NotSpecified1"), EPSILON);
	}
	
	@Test public void testDifferentParametersBothSpecified() {
		Assert.assertEquals(0.03457, getSpilloverValue(BASIC_TEST_MATRIX_ID, "Fluor", "Cy5PE"), EPSILON);
	}
	
	@Test public void testSameParameterBothSpecified() {
		Assert.assertEquals(0.9876, getSpilloverValue(BASIC_TEST_MATRIX_ID, "Fluor", "Fluor"), EPSILON);
	}
	
	@Test public void testNotSymmetric() {
		Assert.assertTrue(getSpilloverValue(BASIC_TEST_MATRIX_ID, "PhyEry", "Cy5PE") != 
			getSpilloverValue(BASIC_TEST_MATRIX_ID, "Cy5PE", "PhyEry"));
	}
	
	@Test public void testMultipleSpecifiedDifferentSpillover() {
		Assert.assertEquals(0.44444, getSpilloverValue(MULTIPLE_VALUES_MATRIX_ID, "Fluor", "PhyEry"), EPSILON);
	}
	
	@Test public void testMultipleSpecifiedSameSpillover() {
		Assert.assertEquals(0.66666, getSpilloverValue(MULTIPLE_VALUES_MATRIX_ID, "PhyEry", "Fluor"), EPSILON);
	}
	
	@Test public void testSameParameterMultipleSpecified() {
		Assert.assertEquals(0.88888, getSpilloverValue(MULTIPLE_VALUES_MATRIX_ID, "Cy5PE", "Cy5PE"), EPSILON);
	}	
}
