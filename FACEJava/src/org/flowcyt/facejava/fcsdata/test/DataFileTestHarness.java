package org.flowcyt.facejava.fcsdata.test;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.CircularParameterDependencyException;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.fcsdata.exception.InvalidDataSetsException;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.junit.Assert;

/**
 * The main class for FCS Tests. We want to run the same test on all the different
 * data types we support so we've put them in here. FCS tests should create a new harness
 * and use these methods (when they make sense). If any new tests apply to all data types
 * add them here. It should only be used when testing valid FCS files. Error checks should
 * be done in another class. 
 * 
 * Consumers should set the correct values for all the expected values in their
 * @BeforeClass method so that all the tests will run correctly. (It can be set in the
 * @Before method but then the same data will be reloaded for each test. Since the 
 * data doesn't change between tests, we only need to load it once). Then, the test*
 * methods can be called from the consumer in their own methods (annotated with @Test). 
 * 
 * @author echng
 */
public class DataFileTestHarness {
	public static final double EPSILON = 0.005;
	
	public static final String TEST_FILE_DIRECTORY = "file:src/org/flowcyt/facejava/fcsdata/test/files/";

	/**
	 * The following member variables should be filled by consumers before any tests are
	 * run.
	 */
	private FcsDataFile dataFile;
	
	/**
	 * Pick one data set from the test file to perform the tests on. 
	 */
	private FcsDataSet testDataSet;
	
	private DataRetriever retriever;
	
	private int expectedDataSetCount;
	
	/**
	 * Map the parameter number (from 1) to its short name. If a parameter doesn't
	 * have a short name, don't put it in the map.
	 */
	private Map<Integer, String> expectedParameterNames = new HashMap<Integer, String>();
	
	private int expectedParameterCount;
	
	/**
	 * Put events that you want to check were loaded correctly into here.
	 */
	private List<Event> expectedEvents = new ArrayList<Event>();
	
	private int expectedEventCount;
	
	/**
	 * The next two are used to check that DataRetriever is working correctly (i.e.,
	 * getting Parameters from the DataSet correctly). testEvent should contain 
	 * expectedTestEventData.
	 */
	private Event testEvent;
	
	private double[] expectedTestEventData;
	
	/**
	 * Constructor.
	 * @param fcsFilePath The path to the FCS data file to use.
	 * @param datasetNumber The data set number (starts from 0) of the data set in the
	 * given file to use when doing the tests.
	 * @throws IOException
	 * @throws InvalidCFCSDataSetTypeException
	 * @throws CFCSDataSizeError
	 * @throws DuplicateParameterReferenceException 
	 * @throws InvalidDataSetsException 
	 * @throws CircularParameterDependencyException 
	 */
	public DataFileTestHarness(String fcsFileURI, int datasetNumber) throws Exception {
		dataFile = new CFCSInput().read(fcsFileURI);
		
		testDataSet = dataFile.getByDataSetNumber(datasetNumber);
		
		retriever = testDataSet.getRetriever();
	}
	
	public void setExpectedDataSetCount(int expectedDataSetCount) {
		this.expectedDataSetCount = expectedDataSetCount;
	}

	public void setExpectedEventCount(int expectedEventCount) {
		this.expectedEventCount = expectedEventCount;
	}

	public void addExpectedEvent(Event expectedEvent) {
		this.expectedEvents.add(expectedEvent);
	}

	public void setExpectedParameterCount(int expectedParameterCount) {
		this.expectedParameterCount = expectedParameterCount;
	}

	public void addExpectedParameterName(int paramNumber, String expectedParameterName) {
		this.expectedParameterNames.put(paramNumber, expectedParameterName);
	}

	public void setExpectedTestEventData(double[] expectedTestEventData) {
		this.expectedTestEventData = expectedTestEventData;
	}

	public void setTestEvent(Event testEvent) {
		this.testEvent = testEvent;
	}

	public void testDataSetCount() {
		Assert.assertEquals(dataFile.size(), expectedDataSetCount);
	}
	
	public void testEventCount() {
		Assert.assertEquals(testDataSet.size(), expectedEventCount);
	}
	
	public void testParameterCount() {
		Assert.assertEquals(testDataSet.getParameterCount(), expectedParameterCount);
	}
	
	public void testEventsLoaded() {
		for (Event expectedEvent : expectedEvents) {
			boolean found = false;
			for (Event dataEvent : testDataSet) {
				if (expectedEvent.hasSameData(dataEvent)) {
					found = true;
					break;
				}
			}
			Assert.assertTrue(found);
		}
	}
	
	public void testEventsLoadedWithEpsilon() {
		for (Event expectedEvent : expectedEvents) {
			boolean found = false;
			for (Event dataEvent : testDataSet) {
				if (expectedEvent.hasSameData(dataEvent, EPSILON)) {
					found = true;
					break;
				}
			}
			Assert.assertTrue(found);
		}
	}
	
	public FcsDataSet getTestDataSet() {
		return testDataSet;
	}
	
	public void testDataPointRetrievalByName() throws DataRetrievalException {
		for (Map.Entry<Integer, String> entry : expectedParameterNames.entrySet()) {
			Assert.assertEquals(
					retriever.getScale(new ParameterReference(entry.getValue()), testEvent),
					expectedTestEventData[entry.getKey() - 1]);
		}
	}
	
	public void testBadParameterName() throws DataRetrievalException {
		retriever.getScale(new ParameterReference("I Am Not A Real Parameter Name"), testEvent);
	}
	
	public void testUnreferencableParameterReference() throws DataRetrievalException {
		retriever.getScale(ParameterReference.UNREFERENCABLE, testEvent);
	}
}
