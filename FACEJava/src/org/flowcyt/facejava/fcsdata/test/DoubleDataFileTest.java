package org.flowcyt.facejava.fcsdata.test;

import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests that double files get loaded correctly.
 * 
 * @author echng
 */
public class DoubleDataFileTest {
	public static final String DOUBLE_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "double-5_events.fcs";
	
		
	private static DataFileTestHarness harness;
		
	@BeforeClass
    public static void oneTimeSetUp() throws Exception {
		harness = new DataFileTestHarness(DOUBLE_TEST_FILE, 1);
		
		harness.setExpectedDataSetCount(1);
		
		harness.addExpectedParameterName(1, "AS");
		harness.addExpectedParameterName(2, "BS");
		harness.addExpectedParameterName(3, "CS");
		harness.addExpectedParameterName(4, "DS");
		
		harness.setExpectedParameterCount(4);
		
		double[] data1 = {100, 200, 300, 400};
		harness.addExpectedEvent(new Event(data1));
		double[] data2 = {550.5, 670.3, 730.7, 890.1};
		harness.addExpectedEvent(new Event(data2));
		double[] data3 = {123.456789, 345.678912, 678.912345, 912.345678};
		harness.addExpectedEvent(new Event(data3));
		double[] data4 = {326.8498654313, 269.8765432135, 468.7973216549, 843.1549265195};
		harness.addExpectedEvent(new Event(data4));
		double[] data5 = {0.8213456498421, 0.0003463842624, 0.0000006422416, 0.0000000000042};
		harness.addExpectedEvent(new Event(data5));
		
		harness.setTestEvent(new Event(data4));
		
		harness.setExpectedEventCount(5);
	
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
		harness.testEventsLoadedWithEpsilon();
	}
	
	@Test public void testDataPointRetrievalByName() throws DataRetrievalException {
		harness.testDataPointRetrievalByName();
	}
	
	@Test(expected=NoSuchParameterException.class) 
	public void testBadParameterName() throws DataRetrievalException {
		harness.testBadParameterName();
	}
}
