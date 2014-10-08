package org.flowcyt.facejava.fcsdata.test;

import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests that ASCII files get loaded correctly.
 * 
 * @author echng
 */
public class MissingParameterNameTest {
	public static final String ASCII_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "ascii-2_events_missing_parameter_names.fcs";
	
	private static DataFileTestHarness harness;
	
	@BeforeClass
    public static void oneTimeSetUp() throws Exception {
		harness = new DataFileTestHarness(ASCII_TEST_FILE, 1);
		
		harness.setExpectedDataSetCount(1);
		
		harness.addExpectedParameterName(1, "123");
		harness.addExpectedParameterName(3, "SSC");
		
		harness.setExpectedParameterCount(4);
		
		double[] data1 = {125, 150, 175, 150};
		harness.addExpectedEvent(new Event(data1));
		double[] data2 = {150, 125, 150, 175};
		harness.addExpectedEvent(new Event(data2));
		
		harness.setTestEvent(new Event(data2));
		
		harness.setExpectedEventCount(2);
	
		harness.setExpectedTestEventData(data2);
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
	
	@Test(expected=NoSuchParameterException.class)
	public void testUnreferencableParameter() throws Exception {
		harness.testUnreferencableParameterReference();
	}
}
