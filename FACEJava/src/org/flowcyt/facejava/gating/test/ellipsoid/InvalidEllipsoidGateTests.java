package org.flowcyt.facejava.gating.test.ellipsoid;

import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Test;

/**
 * Tests invalid Ellipsoid Gates
 * 
 * @author echng
 */
public class InvalidEllipsoidGateTests {
	private static final String TEST_FILE_DIRECTORY = EllipsoidGateTest.ELLIPSOID_TEST_FILE_DIRECTORY;
	
	private static final String FIRST_FOCUS_NOT_ENOUGH_FILE = TEST_FILE_DIRECTORY + "FirstFocusNotEnoughCoordinates.xml";
	
	private static final String FIRST_FOCUS_TOO_MANY_FILE = TEST_FILE_DIRECTORY + "FirstFocusTooManyCoordinates.xml";
	
	private static final String LESS_THAN_TWO_DIMENSIONS_FILE = TEST_FILE_DIRECTORY + "LessThanTwoDimensions.xml";
	
	private static final String LESS_THAN_TWO_FOCI_FILE = TEST_FILE_DIRECTORY + "LessThanTwoFoci.xml";
	
	private static final String MORE_THAN_TWO_FOCI_FILE = TEST_FILE_DIRECTORY + "MoreThanTwoFoci.xml";
	
	private static final String NEGATIVE_DISTANCE_FILE = TEST_FILE_DIRECTORY + "NegativeDistance.xml";
	
	private static final String SECOND_FOCUS_NOT_ENOUGH_FILE = TEST_FILE_DIRECTORY + "SecondFocusNotEnoughCoordinates.xml";
		
	private static final String SECOND_FOCUS_TOO_MANY_FILE = TEST_FILE_DIRECTORY + "SecondFocusTooManyCoordinates.xml";
	
	@Test(expected=InvalidGateDescriptionException.class)
	public void testFirstFocusNotEnough() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(FIRST_FOCUS_NOT_ENOUGH_FILE );
		reader.read();
	}

	@Test(expected=InvalidGateDescriptionException.class)
	public void testFirstFocusTooMany() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(FIRST_FOCUS_TOO_MANY_FILE );
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testLessThanTwoDimensions() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(LESS_THAN_TWO_DIMENSIONS_FILE);
		reader.read();
	}

	@Test(expected=InvalidGatingMLFileException.class)
	public void testLessThanTwoFoci() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(LESS_THAN_TWO_FOCI_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testMoreThanTwoFoci() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(MORE_THAN_TWO_FOCI_FILE);
		reader.read();
	}

	@Test(expected=InvalidGatingMLFileException.class)
	public void testNegativeDistance() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NEGATIVE_DISTANCE_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGateDescriptionException.class)
	public void testSecondFocusNotEnough() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(SECOND_FOCUS_NOT_ENOUGH_FILE);
		reader.read();
	}

	@Test(expected=InvalidGateDescriptionException.class)
	public void testSecondFocusTooMany() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(SECOND_FOCUS_TOO_MANY_FILE);
		reader.read();
	}
}
