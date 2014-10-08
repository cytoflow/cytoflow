package org.flowcyt.facejava.transformation.test;

import java.util.Collections;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.exception.CircularParameterDependencyException;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.transformation.TransformationCollection;
import org.flowcyt.facejava.transformation.exception.InvalidTransformationMLFileException;
import org.flowcyt.facejava.transformation.xmlio.TransformationMLFileReader;
import org.junit.Test;

/**
 * Tests invalid transformations.
 * 
 * @author echng
 */
public class InvalidTransformationTests {
	private static final String TEST_FILE_DIRECTORY = TransformationTestHarness.TRANSFORMATION_TEST_FILE_DIRECTORY;
	
	private static final String NO_NAME_TEST_FILE = TEST_FILE_DIRECTORY + "NoName.xml";

	private static final String NO_PREDEFINED_UNIVERSAL_TEST_FILE = TEST_FILE_DIRECTORY + "NoPredefinedOrUniversal.xml";
	
	private static final String ONE_PREDEFINED_ONE_UNIVERSAL_TEST_FILE = TEST_FILE_DIRECTORY + "OnePredefinedOneUniversal.xml";
	
	private static final String TWO_PREDEFINED_TEST_FILE = TEST_FILE_DIRECTORY + "TwoPredefined.xml";
	
	private static final String TWO_IN_PREDEFINED_TEST_FILE = TEST_FILE_DIRECTORY + "TwoTransformationsInPredefined.xml";
	
	private static final String TWO_UNIVERSAL_TEST_FILE = TEST_FILE_DIRECTORY + "TwoUniversal.xml";
	
	private static final String ZERO_IN_PREDEFINED_TEST_FILE = TEST_FILE_DIRECTORY + "ZeroTransformationsInPredefined.xml";

	private static final String DEPENDENCY_LOOP_TEST_FILE = TEST_FILE_DIRECTORY + "DependencyLoop.xml";
	
	private static final String SMALL_DEPENDENCY_CYCLE_TEST_FILE = TEST_FILE_DIRECTORY + "SmallDependencyCycle.xml";
	
	private static final String MEDIUM_DEPENDENCY_CYCLE_TEST_FILE = TEST_FILE_DIRECTORY + "MediumDependencyCycle.xml";
	
	private static final String LARGE_DEPENDENCY_CYCLE_TEST_FILE = TEST_FILE_DIRECTORY + "LargeDependencyCycle.xml";

	private static final String DUPLICATE_NAME_WITH_FCS_PARAMETER_TEST_FILE = TEST_FILE_DIRECTORY + "DuplicateNameWithFcsParameter.xml";
	
	private static final String DUPLICATE_TRANSFORMATION_NAME_TEST_FILE = TEST_FILE_DIRECTORY + "DuplicateTransformationName.xml";
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testNoName() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(NO_NAME_TEST_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testNoPredefinedUniversal() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(NO_PREDEFINED_UNIVERSAL_TEST_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testOnePredefinedOneUniversal() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(ONE_PREDEFINED_ONE_UNIVERSAL_TEST_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testTwoPredefined() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(TWO_PREDEFINED_TEST_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testTwoInPredefined() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(TWO_IN_PREDEFINED_TEST_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testTwoUniversal() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(TWO_UNIVERSAL_TEST_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidTransformationMLFileException.class)
	public void testZeroInPredefined() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(ZERO_IN_PREDEFINED_TEST_FILE);
		reader.read();
	}
	
	private DataRetriever loadFileAndMakeRetriever(String xmlFileURI) throws Exception {
		return loadFileAndMakeRetriever(xmlFileURI, TransformationTestHarness.FCS_FILE_DIR + "int-10_20_test_file.fcs");
	}
	
	private DataRetriever loadFileAndMakeRetriever(String xmlFileURI, String fcsFileURI) throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(xmlFileURI);
		TransformationCollection coll = reader.read();
		
		CFCSInput fcsReader = new CFCSInput();
		FcsDataFile fcsFile = fcsReader.read(fcsFileURI);
		FcsDataSet ds = fcsFile.getByDataSetNumber(1);
		
		return new DataRetriever(ds.getRetriever(), Collections.singletonList(coll));
	}
	
	@Test(expected=CircularParameterDependencyException.class)
	public void testDependencyLoop() throws Exception {
		loadFileAndMakeRetriever(DEPENDENCY_LOOP_TEST_FILE, TransformationTestHarness.FCS_FILE_DIR + "float-1_event.fcs");
	}
	
	@Test(expected=CircularParameterDependencyException.class)
	public void testSmallDependencyCycle() throws Exception {
		loadFileAndMakeRetriever(SMALL_DEPENDENCY_CYCLE_TEST_FILE,TransformationTestHarness.FCS_FILE_DIR + "float-1_event.fcs");
	}
	
	@Test(expected=CircularParameterDependencyException.class)
	public void testMediumDependencyCycle() throws Exception {
		loadFileAndMakeRetriever(MEDIUM_DEPENDENCY_CYCLE_TEST_FILE, TransformationTestHarness.FCS_FILE_DIR + "float-1_event.fcs");
	}
	
	@Test(expected=CircularParameterDependencyException.class)
	public void testLargeDependencyCycle() throws Exception {
		loadFileAndMakeRetriever(LARGE_DEPENDENCY_CYCLE_TEST_FILE, TransformationTestHarness.FCS_FILE_DIR + "float-1_event.fcs");
	}
	
	@Test(expected=DuplicateParameterReferenceException.class)
	public void testDuplicateTransformationName() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(DUPLICATE_TRANSFORMATION_NAME_TEST_FILE);
		reader.read();
	}
	
	@Test(expected=DuplicateParameterReferenceException.class)
	public void testDuplicateNameWithFcsParameter() throws Exception {
		loadFileAndMakeRetriever(DUPLICATE_NAME_WITH_FCS_PARAMETER_TEST_FILE);
	}
	
}
