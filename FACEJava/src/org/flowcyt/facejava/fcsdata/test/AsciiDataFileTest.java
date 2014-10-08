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
public class AsciiDataFileTest {
	public static final String ASCII_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "ascii-4_events.fcs";
	
	private static DataFileTestHarness harness;
	
	@BeforeClass
    public static void oneTimeSetUp() throws Exception {
		harness = new DataFileTestHarness(ASCII_TEST_FILE, 1);
		
		harness.setExpectedDataSetCount(1);
		
		harness.addExpectedParameterName(1, "FSC");
		harness.addExpectedParameterName(2, "SSC");
		
		harness.setExpectedParameterCount(2);
		
		double[] data1 = {125, 150};
		harness.addExpectedEvent(new Event(data1));
		double[] data2 = {175, 150};
		harness.addExpectedEvent(new Event(data2));
		double[] data3 = {150, 125};
		harness.addExpectedEvent(new Event(data3));
		double[] data4 = {150, 175};
		harness.addExpectedEvent(new Event(data4));
		
		harness.setTestEvent(new Event(data4));
		
		harness.setExpectedEventCount(4);
	
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
