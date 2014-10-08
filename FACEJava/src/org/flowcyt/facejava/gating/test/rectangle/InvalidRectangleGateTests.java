package org.flowcyt.facejava.gating.test.rectangle;

import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Test;

/**
 * Test that invalid RectangleGates are recognized properly.
 * 
 * @author echng
 */
public class InvalidRectangleGateTests {
	
	private static final String TEST_FILE_DIRECTORY = RectangleGateTest.RECTANGLE_TEST_FILE_DIRECTORY;
	
	private static final String NO_MIN_MAX_FILE = TEST_FILE_DIRECTORY + "InvalidMinMax.xml";
	
	private static final String NO_DIMENSIONS_FILE = TEST_FILE_DIRECTORY + "NoDimensions.xml";
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoDimensions() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_DIMENSIONS_FILE );
		reader.read();
	}

	@Test(expected=InvalidGateDescriptionException.class)
	public void testNoMinMax() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_MIN_MAX_FILE );
		reader.read();
	}
}
