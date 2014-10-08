package org.flowcyt.facejava.transformation.test;

import org.flowcyt.facejava.transformation.exception.InvalidTransformationMLFileException;
import org.flowcyt.facejava.transformation.xmlio.TransformationMLFileReader;
import org.junit.Test;

/**
 * Test invalid universal transformations
 * 
 * @author echng
 */
public class InvalidUniversalTransformations {
	private static final String TEST_FILE_DIRECTORY = TransformationTestHarness.TRANSFORMATION_TEST_FILE_DIRECTORY;
	
	private static final String MULTIPLE_MATH_TEST_FILE = TEST_FILE_DIRECTORY + "MultipleMathElements.xml";

	private static final String NO_MATH_TEST_FILE = TEST_FILE_DIRECTORY + "NoMathElements.xml";
	
	private static final String UNKNOWN_MATHML_ELEMENT_TEST_FILE = TEST_FILE_DIRECTORY + "UnknownMathMLElement.xml";
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testMultipleMath() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(MULTIPLE_MATH_TEST_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testNoMath() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(NO_MATH_TEST_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testUnknownMathMLElement() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(UNKNOWN_MATHML_ELEMENT_TEST_FILE);
		reader.read();
	}
}
