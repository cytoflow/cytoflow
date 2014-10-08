package org.flowcyt.facejava.fcsdata.test;

import java.util.Iterator;
import java.util.ListIterator;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;
import org.flowcyt.facejava.fcsdata.impl.FcsParameter;
import org.flowcyt.facejava.fcsdata.impl.FcsParameterList;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.fcsdata.io.CFCSOutput;
import org.flowcyt.facejava.fcsdata.io.FcsInput;
import org.flowcyt.facejava.fcsdata.io.FcsOutput;
import org.junit.Assert;

public class FcsOutputTestHarness {
	private static final String DEFAULT_OUTPUT_TEST_FILE = "file:test.fcs";
	
	private String inputFileURI;
	
	private String outputFileURI;
	
	public FcsOutputTestHarness(String inputFileURI) throws Exception {
		this(inputFileURI, DEFAULT_OUTPUT_TEST_FILE);
	}
	
	public FcsOutputTestHarness(String inputFileURI, String outputFileURI) throws Exception {
		this.inputFileURI = inputFileURI;
		this.outputFileURI = outputFileURI;
	}
	
	public void runTestSequence(boolean writeDoubles) throws Exception {
		FcsDataFile inputFile = readFile(inputFileURI);
		
		writeFile(outputFileURI, inputFile, writeDoubles);
		
		FcsDataFile writtenFile = readFile(outputFileURI);
		
		Assert.assertEquals(inputFile.size(), writtenFile.size());
		
		Iterator<FcsDataSet> originalPopsIter = inputFile.iterator();
		Iterator<FcsDataSet> writtenPopsIter = writtenFile.iterator();
		
		while (originalPopsIter.hasNext()) {
			testDataSets(originalPopsIter.next(), writtenPopsIter.next());
		}
	}
	
	private FcsDataFile readFile(String uri) throws Exception {
		FcsInput inAdapter = new CFCSInput();
		return inAdapter.read(uri);
	}
	
	private void writeFile(String uri, FcsDataFile file, boolean writeDoubles) throws Exception {
		FcsOutput outAdapter = new CFCSOutput(writeDoubles);
		outAdapter.write(uri, file);
	}
	
	public void testDataSets(FcsDataSet expected, FcsDataSet actual) throws Exception {
		Assert.assertEquals(expected.getDataSetNumber(), actual.getDataSetNumber());
		Assert.assertEquals(expected.getParameterCount(), actual.getParameterCount());
		Assert.assertEquals(expected.size(), actual.size());
		
		testParameters(expected, actual);
		testEvents(expected, actual);
	}
	
	public void testParameters(FcsDataSet expected, FcsDataSet actual) throws Exception {
		ListIterator<FcsParameter> expectedIter = expected.getParameters().listIterator();
		ListIterator<FcsParameter> actualIter = actual.getParameters().listIterator();
		
		while (expectedIter.hasNext()) {
			FcsParameter expectedParam = expectedIter.next();
			FcsParameter actualParam = actualIter.next();
			
			testParameter(expectedParam, actualParam);
		}
		
		DataRetriever expectedRetriever = expected.getRetriever();
		DataRetriever actualRetriever = actual.getRetriever();
		
		FcsParameterList expectedParameters = expected.getParameters(); 
		FcsParameterList actualParameters = actual.getParameters(); 
		
		Assert.assertEquals(expectedParameters.getParameterReferences().size(), actualParameters.getParameterReferences().size());
		
		Iterator<ParameterReference> expectedReferencesIter = expectedParameters.getParameterReferences().iterator();
		Set<ParameterReference> actualReferences = actualParameters.getParameterReferences();
		
		// References are equal if they both have the same string value.
		while (expectedReferencesIter.hasNext()) {
			ParameterReference expectedRef = expectedReferencesIter.next();
			Assert.assertTrue(actualReferences.contains(expectedRef));
			testParameter((FcsParameter)expectedRetriever.resolveReference(expectedRef),
					(FcsParameter)actualRetriever.resolveReference(expectedRef));
		}
	}
	
	public void testParameter(FcsParameter expected, FcsParameter actual) {
		Assert.assertEquals(expected.getReference(), actual.getReference());
		Assert.assertEquals(expected.getParameterNumber(), actual.getParameterNumber());
	}
	
	public void testEvents(FcsDataSet expected, FcsDataSet actual) throws Exception {
		Iterator<Event> expectedIter = expected.iterator();
		Iterator<Event> actualIter = actual.iterator();
		
		DataRetriever expectedRetriever = expected.getRetriever();
		DataRetriever actualRetriever = actual.getRetriever();
		
		while (expectedIter.hasNext()) {
			Event expectedEvent = expectedIter.next();
			Event actualEvent = actualIter.next();
		
			// Parameter Order and Event Order should be maintained.
			Assert.assertTrue(expectedEvent.hasSameData(actualEvent, DataFileTestHarness.EPSILON));
			
			int i = 0;
			for (FcsParameter expectedParam : expected.getParameters()) {
				FcsParameter actualParam = actual.getParameters().get(i++);
				
				Assert.assertEquals(expectedRetriever.getScale(expectedParam, expectedEvent),
						actualRetriever.getScale(actualParam, actualEvent), 
						DataFileTestHarness.EPSILON);
			}
		}
	}
}
