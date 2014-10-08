package org.flowcyt.facejava.gating.test.polygon;

import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Test;

/**
 * Tests invalid Polygon gates.
 * 
 * @author echng
 */
public class InvalidPolygonGateTests {
	private static final String TEST_FILE_DIRECTORY = PolygonGateTest.POLYGON_TEST_FILE_DIRECTORY;
	
	private static final String LESS_THAN_THREE_VERTICES_FILE = TEST_FILE_DIRECTORY + "LessThanThreeVertices.xml";
	
	private static final String LESS_THAN_TWO_DIMENSIONS_FILE = TEST_FILE_DIRECTORY + "LessThanTwoDimensions.xml";

	private static final String MORE_THAN_TWO_DIMENSIONS_FILE = TEST_FILE_DIRECTORY + "MoreThanTwoDimensions.xml";

	private static final String VERTEX_NOT_ENOUGH_COORDS_FILE = TEST_FILE_DIRECTORY + "VertexHasLessThanTwoCoordinates.xml";

	private static final String VERTEX_TOO_MANY_COORDS_FILE = TEST_FILE_DIRECTORY + "VertexHasMoreThanTwoCoordinates.xml";
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testLessThanThreeVertices() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(LESS_THAN_THREE_VERTICES_FILE);
		reader.read();
	}

	@Test(expected=InvalidGatingMLFileException.class)
	public void testLessThanTwoDimensions() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(LESS_THAN_TWO_DIMENSIONS_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testMoreThanTwoDimensions() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(MORE_THAN_TWO_DIMENSIONS_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testVertexNotEnoughCoords() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(VERTEX_NOT_ENOUGH_COORDS_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testVertexTooManyCoords() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(VERTEX_TOO_MANY_COORDS_FILE);
		reader.read();
	}
}
