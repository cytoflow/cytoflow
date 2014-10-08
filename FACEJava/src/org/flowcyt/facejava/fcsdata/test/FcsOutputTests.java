package org.flowcyt.facejava.fcsdata.test;

import org.junit.Test;

public class FcsOutputTests {
	@Test public void testAsciiFile() throws Exception{
		FcsOutputTestHarness harness = new FcsOutputTestHarness(AsciiDataFileTest.ASCII_TEST_FILE);
		harness.runTestSequence(false);
		harness.runTestSequence(true);
	}
	
	@Test public void testDoubleFile() throws Exception{
		FcsOutputTestHarness harness = new FcsOutputTestHarness(DoubleDataFileTest.DOUBLE_TEST_FILE);
		harness.runTestSequence(false);
		harness.runTestSequence(true);
	}
	
	@Test public void testIntegerFile() throws Exception{
		FcsOutputTestHarness harness = new FcsOutputTestHarness(IntegerDataFileTest.INTEGER_TEST_FILE);
		harness.runTestSequence(false);
		harness.runTestSequence(true);
	}
	
	/* Not enough RAM to run test
	@Test public void testLargeDataSetFile() throws Exception{
		FcsOutputTestHarness harness = new FcsOutputTestHarness(LargeDataSetTest.LARGE_DATA_SET_TEST_FILE);
		harness.runTestSequence();
	} */
	
	@Test public void testMediumDataSetFile() throws Exception{
		FcsOutputTestHarness harness = new FcsOutputTestHarness(DataFileTestHarness.TEST_FILE_DIRECTORY + "int-10000_events_random.fcs");
		harness.runTestSequence(false);
		harness.runTestSequence(true);
	}
	
	@Test public void testMultipleDataSetFile() throws Exception{
		FcsOutputTestHarness harness = new FcsOutputTestHarness(MultipleDataSetTest.MULTIPLE_DATA_SET_TEST_FILE);
		harness.runTestSequence(false);
		harness.runTestSequence(true);
	}
	
	@Test public void testScaleConversionFile() throws Exception{
		FcsOutputTestHarness harness = new FcsOutputTestHarness(ScaleConversionTest.SCALE_CONVERSION_TEST_FILE);
		harness.runTestSequence(false);
		harness.runTestSequence(true);
	}
}
