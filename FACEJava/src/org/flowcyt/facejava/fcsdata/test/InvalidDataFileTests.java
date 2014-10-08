package org.flowcyt.facejava.fcsdata.test;

import java.io.IOException;

import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.fcsdata.exception.InvalidCFCSDataSetTypeException;
import org.flowcyt.facejava.fcsdata.exception.InvalidDataSetsException;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.junit.Assert;
import org.junit.Test;

import org.flowcyt.cfcs.CFCSError;

/**
 * Tests that invalid files are handled (by getting exceptions thrown. If we come across
 * other special cases for FCS files that we should be handling specifically, test them
 * here. We will assume that CFCS will correctly handle FCS files according to the spec,
 * so we only need to test things that we have code to handle specially.
 * 
 * @author echng
 */
public class InvalidDataFileTests {
	
	private static final String INVALID_CRC_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "invalid-no_crc.fcs";
	
	private static final String FILE_NOT_FOUND_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "thereisnosuchfile.fcs";
	
	private static final String INVALID_DATA_SET_TYPE_TEST_FILE  = DataFileTestHarness.TEST_FILE_DIRECTORY + "invalid-bad_data_set_type.fcs";
	
	private static final String DUPLICATE_PARAMETER_NAME_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "invalid-duplicate_parameter_name.fcs";	
	
	/**
	 * This is the one test to make sure that CFCS is reporting errors in an FCS file
	 * correctly. We will assume that since this one works all other errors are reported
	 * as well (in the same way, since it only has CFCSError).
	 */
	@Test(expected=CFCSError.class)
	public void testInvalidCrc() throws Exception {
		new CFCSInput().read(INVALID_CRC_TEST_FILE);
	}
	
	@Test(expected=IOException.class)
	public void testFileNotFound() throws Exception {
		new CFCSInput().read(FILE_NOT_FOUND_TEST_FILE);
	}
	
	@Test(expected=InvalidCFCSDataSetTypeException.class)
	public void testInvalidDataSetType() throws Exception {
		try {
			new CFCSInput().read(INVALID_DATA_SET_TYPE_TEST_FILE);
		} catch (InvalidDataSetsException ex) {
			Assert.assertEquals(ex.getReasons().size(), 1);
			Assert.assertTrue(ex.getReasons().containsKey(1));
			throw ex.getReasons().get(1);
		}
	}
	
	@Test(expected=DuplicateParameterReferenceException.class)
	public void testDuplicateParameterName() throws Exception {
		try {
			new CFCSInput().read(DUPLICATE_PARAMETER_NAME_TEST_FILE);
		} catch (InvalidDataSetsException ex) {
			Assert.assertEquals(ex.getReasons().size(), 1);
			Assert.assertTrue(ex.getReasons().containsKey(1));
			throw ex.getReasons().get(1);
		}
	}
	
}
