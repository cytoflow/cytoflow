package org.flowcyt.facejava.gating.test;

import java.io.IOException;

import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Test;

/**
 * Tests that Invalid Gating files are found and reported (only invalid Gate elements
 * are tested). These only test errors that are general to the gating file and not
 * errors specific to a gate type.
 * 
 * @author echng
 */
public class InvalidGateFileTests {
	private static final String TEST_FILE_DIRECTORY = GateTestHarness.GATING_TEST_FILE_DIRECTORY;
	
	private static final String DUPLICATE_GATE_IDS_GATING_FILE = TEST_FILE_DIRECTORY + "DuplicateGateId.xml";
	
	private static final String ZERO_GATES_GATING_FILE = TEST_FILE_DIRECTORY + "ZeroGates.xml";
	
	private static final String MISSING_GATE_ID_GATING_FILE = TEST_FILE_DIRECTORY + "MissingGateId.xml";
	
	private static final String INVALID_STRUCTURE_GATING_FILE = TEST_FILE_DIRECTORY + "InvalidStructure.xml";
	
	private static final String NO_SUCH_GATING_FILE = TEST_FILE_DIRECTORY + "IAmAGatingFileThatDoesNotExist.xml";
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testDuplicateGateIds() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(DUPLICATE_GATE_IDS_GATING_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testZeroGates() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(ZERO_GATES_GATING_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testMissingGateId() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(MISSING_GATE_ID_GATING_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testInvalidStructure() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(INVALID_STRUCTURE_GATING_FILE);
		reader.read();
	}
	
	@Test(expected=IOException.class)
	public void testFileNotFound() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_SUCH_GATING_FILE);
		reader.read();
	}
}
