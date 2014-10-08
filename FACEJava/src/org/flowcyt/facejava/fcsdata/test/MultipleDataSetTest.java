package org.flowcyt.facejava.fcsdata.test;

import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests that we handle multiple data sets in one FCS file.
 * 
 * @author echng
 */
public class MultipleDataSetTest {
	public static final String MULTIPLE_DATA_SET_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "int-multiple_datasets.fcs";
	
	private static DataFileTestHarness harness;
	
	@BeforeClass
    public static void oneTimeSetUp() throws Exception {
		// Assume the first data set was loaded correctly (since it would've passed the
		// other FCS tests, so only check the second.
		harness = new DataFileTestHarness(MULTIPLE_DATA_SET_TEST_FILE, 2);
		
		harness.setExpectedDataSetCount(2);
		
		harness.addExpectedParameterName(1, "FSC");
		harness.addExpectedParameterName(2, "SSC");
		
		harness.setExpectedParameterCount(2);
		
		double[] data1 = {5,6};
		harness.addExpectedEvent(new Event(data1));
		double[] data2 = {7,8};
		harness.addExpectedEvent(new Event(data2));
		double[] data3 = {9,10};
		harness.addExpectedEvent(new Event(data3));
		double[] data4 = {11,12};
		harness.addExpectedEvent(new Event(data4));
		
		harness.setExpectedEventCount(4);
	
		harness.setTestEvent(new Event(data4));
		
		harness.setExpectedTestEventData(data4);
	}
	
	@Test public void testDataSetCount() {
		harness.testDataSetCount();
	}
	
	@Test public void testEventCount() {
		harness.testEventCount();
	}
	
	@Test public void testParameterCount() {
		harness.testParameterCount();
	}
	
	@Test public void testEventsLoaded() {
		harness.testEventsLoaded();
	}
	
	@Test public void testDataPointRetrievalByName() throws DataRetrievalException {
		harness.testDataPointRetrievalByName();
	}
	
	@Test(expected=NoSuchParameterException.class) 
	public void testBadParameterName() throws DataRetrievalException {
		harness.testBadParameterName();
	}
}
