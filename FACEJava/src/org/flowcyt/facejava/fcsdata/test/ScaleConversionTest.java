package org.flowcyt.facejava.fcsdata.test;

import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;
import org.junit.BeforeClass;
import org.junit.Test;

public class ScaleConversionTest {
	public static final String SCALE_CONVERSION_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "int-scale_conversion.fcs";

	private static DataFileTestHarness harness;
	
	@BeforeClass
    public static void oneTimeSetUp() throws Exception {
		harness = new DataFileTestHarness(SCALE_CONVERSION_TEST_FILE, 1);
		
		harness.setExpectedDataSetCount(1);
		
		harness.addExpectedParameterName(1, "FS");
		harness.addExpectedParameterName(2, "LOG");
		
		harness.setExpectedParameterCount(2);	
		
		double[] data1 = {25.6, 10};
		harness.addExpectedEvent(new Event(data1));
		double[] data2 = {51.2, 100};
		harness.addExpectedEvent(new Event(data2));
		double[] data3 = {76.8, 1000};
		harness.addExpectedEvent(new Event(data3));
		
		harness.setExpectedEventCount(3);
		
		harness.setTestEvent(new Event(data3));		
		
		harness.setExpectedTestEventData(data3);
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
