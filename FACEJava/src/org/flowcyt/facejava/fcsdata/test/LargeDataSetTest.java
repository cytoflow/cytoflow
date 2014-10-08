package org.flowcyt.facejava.fcsdata.test;

import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests the loading of a large data set (11 MB FCS file).
 * 
 * NOTE: From empirical tests, CFCS uses ~170 MB to load its data, then we use ~80 M to load
 * our version of the data (stuff in cfcsadapter), so at peak memory usage (before the
 * CFCS* objects get garbage-collected) we need around ~250 M. Thus, the VM max heap size 
 * must be increased to around 256 MB (at least). Use -Xmx256M to do so. *  
 * 
 * @author echng
 */
public class LargeDataSetTest {
	public static final String LARGE_DATA_SET_TEST_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "int-large_dataset.fcs";
	
	private static DataFileTestHarness harness;
	
	@BeforeClass
    public static void oneTimeSetUp() throws Exception {
		harness = new DataFileTestHarness(LARGE_DATA_SET_TEST_FILE, 1);
		
		harness.setExpectedDataSetCount(1);
		
		harness.addExpectedParameterName(1, "FSC-H");
		harness.addExpectedParameterName(2, "SSC-H");
		harness.addExpectedParameterName(3, "FL1-H");
		harness.addExpectedParameterName(4, "FL2-H");
		harness.addExpectedParameterName(5, "FL3-H");
		harness.addExpectedParameterName(6, "FL3-A");
		harness.addExpectedParameterName(7, "FL4-H");
		
		// Don't bother checking for any events. Covered by Integer test
		
		harness.setExpectedParameterCount(7);
		
		harness.setExpectedEventCount(809850);
	
		double[] testData = {1, 2, 3, 4, 5, 6, 7};
		harness.setTestEvent(new Event(testData));
		harness.setExpectedTestEventData(testData);
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
