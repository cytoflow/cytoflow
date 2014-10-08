package org.flowcyt.facejava.fcsdata.test;

import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Test that integer files get loaded correctly.
 * 
 * @author echng
 */
public class IntegerDataFileTest {
	public static final String INTEGER_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "int-15_events.fcs";
	
	private static DataFileTestHarness harness;
	
	@BeforeClass
    public static void oneTimeSetUp() throws Exception {
		harness = new DataFileTestHarness(INTEGER_TEST_FILE, 1);
		
		harness.setExpectedDataSetCount(1);
		
		harness.addExpectedParameterName(1, "FCS");
		harness.addExpectedParameterName(2, "SSC");
		
		harness.setExpectedParameterCount(2);	
		
		double[] data1 = {400, 300};
		harness.addExpectedEvent(new Event(data1));
		double[] data2 = {600, 300};
		harness.addExpectedEvent(new Event(data2));
		double[] data3 = {300, 600};
		harness.addExpectedEvent(new Event(data3));
		double[] data4 = {500, 200};
		harness.addExpectedEvent(new Event(data4));
		double[] data5 = {600, 800};
		harness.addExpectedEvent(new Event(data5));
		double[] data6 = {500, 500};
		harness.addExpectedEvent(new Event(data6));
		double[] data7 = {800, 600};
		harness.addExpectedEvent(new Event(data7));
		double[] data8 = {200, 400};
		harness.addExpectedEvent(new Event(data8));
		double[] data9 = {300, 100};
		harness.addExpectedEvent(new Event(data9));
		double[] data10 = {800, 200};
		harness.addExpectedEvent(new Event(data10));
		double[] data11 = {900, 400};
		harness.addExpectedEvent(new Event(data11));
		double[] data12 = {400, 800};
		harness.addExpectedEvent(new Event(data12));
		double[] data13 = {200, 900};
		harness.addExpectedEvent(new Event(data13));
		double[] data14 = {600, 700};
		harness.addExpectedEvent(new Event(data14));
		double[] data15 = {400, 500};
		harness.addExpectedEvent(new Event(data15));
		
		harness.setTestEvent(new Event(data15));		
		
		harness.setExpectedEventCount(15);
	
		harness.setExpectedTestEventData(data15);
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
