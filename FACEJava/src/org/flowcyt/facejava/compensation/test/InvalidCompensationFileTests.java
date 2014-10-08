package org.flowcyt.facejava.compensation.test;

import org.flowcyt.facejava.compensation.CompensatedDataSet;
import org.flowcyt.facejava.compensation.SpilloverMatrix;
import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.compensation.exception.InvalidCompensationMLFileException;
import org.flowcyt.facejava.compensation.exception.InvalidCompensationMatrixException;
import org.flowcyt.facejava.compensation.xmlio.CompensationMLFileReader;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.junit.Assert;
import org.junit.Test;

/**
 * Tests invalid files.
 * 
 * @author echng
 */
public class InvalidCompensationFileTests {
	private static final String COEFF_LT_0_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "CoefficientLT0.xml";
	
	private static final String COEFF_EQUAL_0_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "CoefficientEqual0.xml";

	private static final String COEFF_GT_1_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "CoefficientGT1.xml";

	private static final String COEFF_EQUAL_1_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "CoefficientEqual1.xml";
	
	private static final String DUPLICATE_IDS_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "DuplicateIds.xml";

	private static final String NO_COEFFICIENT_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "NoCoefficient.xml";

	private static final String NO_ID_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "NoId.xml";

	private static final String NO_MATRIX_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "NoMatrix.xml";

	private static final String NO_PARAMETER_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "NoParameter.xml";

	private static final String NO_SPILLOVER_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "NoSpillover.xml";
	
	private static final String NO_VALUE_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "NoValue.xml";
	
	private static final String SINGULAR_MATRIX_TEST_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "SingularMatrix.xml";
	
	public SpilloverMatrixSet runReader(String fileURI) throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader(fileURI);
		return reader.read();
	}
	
	@Test public void testCoeffEqual0() throws Exception {
		Assert.assertNotNull(runReader(COEFF_EQUAL_0_TEST_FILE));
	}
	
	@Test public void testCoeffEqual1() throws Exception {
		Assert.assertNotNull(runReader(COEFF_EQUAL_1_TEST_FILE));
	}
	
	@Test(expected=InvalidCompensationMLFileException.class)
	public void testCoeffLT0() throws Exception {
		runReader(COEFF_LT_0_TEST_FILE);
	}
	
	@Test(expected=InvalidCompensationMLFileException.class)
	public void testCoeffGT1() throws Exception {
		runReader(COEFF_GT_1_TEST_FILE);
	}
	
	@Test(expected=InvalidCompensationMLFileException.class)
	public void testDuplicateIds() throws Exception {
		runReader(DUPLICATE_IDS_TEST_FILE);
	}
	
	@Test(expected=InvalidCompensationMLFileException.class)
	public void testNoCoefficient() throws Exception {
		runReader(NO_COEFFICIENT_TEST_FILE);
	}
	
	@Test(expected=InvalidCompensationMLFileException.class)
	public void testNoId() throws Exception {
		runReader(NO_ID_TEST_FILE);
	}
	
	@Test(expected=InvalidCompensationMLFileException.class)
	public void testNoMatrix() throws Exception {
		runReader(NO_MATRIX_TEST_FILE);
	}
	
	@Test(expected=InvalidCompensationMLFileException.class)
	public void testNoParameter() throws Exception {
		runReader(NO_PARAMETER_TEST_FILE);
	}
	
	@Test(expected=InvalidCompensationMLFileException.class)
	public void testNoSpillover() throws Exception {
		runReader(NO_SPILLOVER_TEST_FILE);
	}
	
	@Test(expected=InvalidCompensationMLFileException.class)
	public void testNoValue() throws Exception {
		runReader(NO_VALUE_TEST_FILE);
	}
	
	@Test(expected=InvalidCompensationMatrixException.class)
	public void testSingularMatrix() throws Exception {
		SpilloverMatrixSet coll = runReader(SINGULAR_MATRIX_TEST_FILE);
		SpilloverMatrix matrix = coll.get("Singular");
		
		CFCSInput adapter = new CFCSInput();
		FcsDataFile dataFile = adapter.read(CompensatorTestHarness.FCS_TEST_FILE_DIRECTORY + "int-10_events_8_parameters.fcs");
		
		new CompensatedDataSet(dataFile.getByDataSetNumber(1), matrix); 
	}
}
