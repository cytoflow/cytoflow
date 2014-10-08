package org.flowcyt.facejava.gating.test.bool;

import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Test;

/**
 * Tests invalid Boolean Gates.
 * 
 * @author echng
 */
public class InvalidBooleanGateTests {
	private static final String TEST_FILE_DIRECTORY = BooleanGateTest.BOOLEAN_TEST_FILE_DIRECTORY;
	
	private static final String AND_NOT_ENOUGH_FILE = TEST_FILE_DIRECTORY + "AndNotEnoughOperands.xml";
	
	private static final String DEPENDENCY_LOOP_FILE = TEST_FILE_DIRECTORY + "DependencyLoop.xml";
	
	private static final String INVALID_GATE_DEFINITION_SCHEMA_FILE = TEST_FILE_DIRECTORY + "InvalidGateDefinitionSchema.xml";
	
	private static final String INVALID_GATE_DEFINITION_SPEC_FILE = TEST_FILE_DIRECTORY + "InvalidGateDefinitionSpec.xml";
	
	private static final String INvALID_GATE_REFERENCE_FILE = TEST_FILE_DIRECTORY + "InvalidGateReference.xml";
	
	private static final String LARGE_DEPENDENCY_CYCLE_FILE = TEST_FILE_DIRECTORY + "LargeDependencyCycle.xml";
	
	private static final String MEDIUM_DEPENDENCY_CYCLE_FILE = TEST_FILE_DIRECTORY + "MediumDependencyCycle.xml";
	
	private static final String NESTED_GATE_DUPLICATE_ID_FILE = TEST_FILE_DIRECTORY + "NestedGateDuplicateId.xml";
	
	private static final String NOT_ENOUGH_OPERATORS_FILE = TEST_FILE_DIRECTORY + "NotEnoughOperators.xml";
	
	private static final String NOT_NOT_ENOUGH_FILE = TEST_FILE_DIRECTORY + "NotNotEnoughOperands.xml";
	
	private static final String NOT_TOO_MANY_FILE = TEST_FILE_DIRECTORY + "NotTooManyOperands.xml";
	
	private static final String OR_NOT_ENOUGH_FILE = TEST_FILE_DIRECTORY + "OrNotEnoughOperands.xml";
	
	private static final String SMALL_DEPENDENCY_CYCLE_FILE = TEST_FILE_DIRECTORY + "SmallDependencyCycle.xml";
	
	private static final String TOO_MANY_OPERATORS_FILE = TEST_FILE_DIRECTORY + "TooManyOperators.xml";
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testAndNotEnough() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(AND_NOT_ENOUGH_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGateDescriptionException.class)
	public void testDependencyLoop() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(DEPENDENCY_LOOP_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testInvalidGateDescriotionSchema() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(INVALID_GATE_DEFINITION_SCHEMA_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGateDescriptionException.class)
	public void testInvalidGateDescriptionSpec() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(INVALID_GATE_DEFINITION_SPEC_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testInvalidGateReference() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(INvALID_GATE_REFERENCE_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGateDescriptionException.class)
	public void testLargeDependencyCycle() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(LARGE_DEPENDENCY_CYCLE_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGateDescriptionException.class)
	public void testMediumDependencyCycle() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(MEDIUM_DEPENDENCY_CYCLE_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNestedGateDuplicateId() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NESTED_GATE_DUPLICATE_ID_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNotEnoughOperators() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NOT_ENOUGH_OPERATORS_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNotNotEnoughOperands() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NOT_NOT_ENOUGH_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNotTooManyOperands() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NOT_TOO_MANY_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testOrNotEnoughOperands() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(OR_NOT_ENOUGH_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGateDescriptionException.class)
	public void testSmallDependencyCycle() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(SMALL_DEPENDENCY_CYCLE_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testTooManyOperators() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(TOO_MANY_OPERATORS_FILE);
		reader.read();
	}
}
