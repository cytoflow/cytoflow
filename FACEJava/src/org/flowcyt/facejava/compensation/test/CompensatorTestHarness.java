package org.flowcyt.facejava.compensation.test;

import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.flowcyt.facejava.compensation.CompensatedDataSet;
import org.flowcyt.facejava.compensation.SpilloverMatrix;
import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.compensation.xmlio.CompensationMLFileReader;
import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Parameter;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;
import org.flowcyt.facejava.fcsdata.impl.FcsParameter;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.fcsdata.io.FcsInput;
import org.junit.Assert;

/**
 * The harness runs a generic sequence of tests that compensate and uncompensate a data set. Each
 * harness is specific to one CompensationML file.
 * 
 * It checks that:
 *  - the correct parameters are detected to be part of the compensation matrix
 *  - calling compensate() will result in the given expected events
 *  - calling compensate() on an already compensated data set will have no effect
 *  - calling uncompensate() will result in the original events before compensation
 *  - calling uncompensate() on an already uncompensated data set will have no effect  
 * 
 * These test assume that correct values are retrieved from a SpilloverMatrix.
 * 
 * @author echng
 */
public class CompensatorTestHarness {
	public static final String TEST_FILE_DIRECTORY = "file:src/org/flowcyt/facejava/compensation/test/files/";
	
	public static final String FCS_TEST_FILE_DIRECTORY = "file:src/org/flowcyt/facejava/compensation/test/files/fcs/";
	
	public static final double EPSILON = 0.000000000005;
	
	private SpilloverMatrixSet matrixColl;
	
	/**
	 * Constructor.
	 * @param matrixFileURI The CompensationML file to load
	 * @throws Exception Thrown if there was some error
	 */
	public CompensatorTestHarness(String matrixFileURI) throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader(matrixFileURI);
		matrixColl = reader.read();
	}
	
	/**
	 * 
	 * @param matrixId The id of the matrix to test.
	 * @param fcsFileURI The URI string for the FCS file to use in the test. The first data 
	 * set in the file will be used for the tests.
	 * @param expectedEventsData A 2D array of the expected event data after compensation. 
	 * Each row is one event.  
	 * @param expectedCompensatedParameterReferences A set containing the references that are
	 * expected to be used to create the matrix.
	 * @throws Exception Thrown if there was some error.
	 */
	public void runTestSequence(String matrixId, String fcsFileURI, double[][] expectedEventsData, Set<String> expectedCompensatedParameterReferences) throws Exception {
		SpilloverMatrix matrix = matrixColl.get(matrixId);
		
		FcsDataSet ds = getFirstDataSet(fcsFileURI);
		CompensatedDataSet compds = new CompensatedDataSet(ds, matrix);
		
		testCompensatedParameters(compds, expectedCompensatedParameterReferences);
				
		Collection<Event> expectedEvents = makeEventSet(expectedEventsData);
		containsAllExpectedEvents(compds, expectedEvents);
	}
	
	private FcsDataSet getFirstDataSet(String fcsFileURI) throws Exception {
		FcsInput adapter = new CFCSInput();
		FcsDataFile dataFile = adapter.read(fcsFileURI);
		return dataFile.getByDataSetNumber(1);
	}
	
	private Set<Event> makeEventSet(double[][] eventsData) {
		Set<Event> rv = new HashSet<Event>();
		
		for (int i = 0; i < eventsData.length; ++i) {
			rv.add(new Event(eventsData[i]));
		}
		
		return rv;
	}
	
	private void testCompensatedParameters(CompensatedDataSet compds, Set<String> expectedReferences) throws Exception {
		DataRetriever retriever = compds.getRetriever();
		List<FcsParameter> compensatedParameters = compds.getCompensatedParameters();
		
		for (String expectedReference : expectedReferences) {
			Assert.assertTrue(compensatedParameters.contains(retriever.resolveReference(new ParameterReference(expectedReference))));
		}
		
		Assert.assertEquals(expectedReferences.size(), compds.getCompensatedParameterCount());
	}
	
	private void containsAllExpectedEvents(CompensatedDataSet compds, Collection<Event> expectedEvents) throws Exception {
		DataRetriever retriever = compds.getRetriever();
		
		for (Event expected : expectedEvents) {
			boolean found = false;
			for (Event dataEvent : compds) {
				if (expected.hasSameData(dataEvent, EPSILON)) {
					found = true;
					
					for (Parameter param : retriever.getAllParameters()) {
						Assert.assertEquals(retriever.getScale(param, expected), retriever.getScale(param, dataEvent), EPSILON);
					}
					
					break;
				}
			}
			if (!found)
				System.out.println(expected);
			Assert.assertTrue(found);
		}
		Assert.assertEquals(expectedEvents.size(), compds.size());
	}
}
