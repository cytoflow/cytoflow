package org.flowcyt.facejava.gating.test.polytope;

import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Test;

/**
 * Test invalid Polytope Gating XML files.
 * 
 * @author echng
 *
 */
public class InvalidPolytopeGateTest {
	private static final String TEST_FILE_DIRECTORY = PolytopeGateTest.POLYTOPE_TEST_FILE_DIRECTORY;
	
	private static final String NO_DIMENSIONS_FILE = TEST_FILE_DIRECTORY + "NoDimensions.xml";

	private static final String NO_COORDINATES_FILE = TEST_FILE_DIRECTORY + "NoCoordinates.xml";
	
	private static final String NO_POINTS_FILE = TEST_FILE_DIRECTORY + "NoPoints.xml";

	private static final String NOT_ENOUGH_COORDS_FILE = TEST_FILE_DIRECTORY + "NotEnoughCoordinates.xml";
	
	private static final String TOO_MANY_COORDS_FILE = TEST_FILE_DIRECTORY + "TooManyCoordinates.xml";
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoDimensions() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_DIMENSIONS_FILE );
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoCoordinates() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_COORDINATES_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoPoints() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_POINTS_FILE );
		reader.read();
	}
	
	@Test(expected=InvalidGateDescriptionException.class)
	public void testNotEnoughCoords() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NOT_ENOUGH_COORDS_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGateDescriptionException.class)
	public void testTooManyCoords() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(TOO_MANY_COORDS_FILE);
		reader.read();
	}
}
