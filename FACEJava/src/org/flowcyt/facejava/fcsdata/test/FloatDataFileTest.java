package org.flowcyt.facejava.fcsdata.test;

import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests that float files get loaded correctly.
 * 
 * @author echng
 */
public class FloatDataFileTest {
	public static final String FLOAT_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "float-1_event.fcs";
	
		
	private static DataFileTestHarness harness;
		
	@BeforeClass
    public static void oneTimeSetUp() throws Exception {
		harness = new DataFileTestHarness(FLOAT_TEST_FILE, 1);
		
		harness.setExpectedDataSetCount(1);
		
		harness.addExpectedParameterName(1, "Time");
		harness.addExpectedParameterName(2, "FSC-A");
		harness.addExpectedParameterName(3, "FSC-H");
		harness.addExpectedParameterName(4, "SSC-A");
		harness.addExpectedParameterName(5, "SSC-H");
		harness.addExpectedParameterName(6, "SSC-W");
		harness.addExpectedParameterName(7, "FITC-A");
		harness.addExpectedParameterName(8, "PE-A");
		harness.addExpectedParameterName(9, "FL4 PI-A");
		harness.addExpectedParameterName(10, "FL6 APC-A");
		
		harness.setExpectedParameterCount(10);
		
		double[] data1 = {18.45, 3283.87, 1476.89, 3294.86, 2945.63, 29978.93, 1248.62, 64958.82, 56594.05, 233.97};
		harness.addExpectedEvent(new Event(data1));
		
		harness.setTestEvent(new Event(data1));
		
		harness.setExpectedEventCount(1);
	
		harness.setExpectedTestEventData(data1);
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
