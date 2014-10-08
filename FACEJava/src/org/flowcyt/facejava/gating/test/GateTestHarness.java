package org.flowcyt.facejava.gating.test;

import java.util.HashMap;
import java.util.Map;

import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.fcsdata.io.FcsInput;
import org.flowcyt.facejava.gating.analysis.Analyzer;
import org.flowcyt.facejava.gating.analysis.PopulationAnalysisResult;
import org.flowcyt.facejava.gating.analysis.PopulationCollectionAnalysisResult;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.gates.GateSubPopulation;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Assert;

/**
 * The main class for Gate testing. It should only be used for testing valid gating
 * files, where we want to check if the correct number of events are inside the gate.
 * Error checks should be done in another class.
 * 
 * Consumers should set the correct values for the expected inside event count for 
 * each of the gates (by id). Then, use each of the test* methods in their own 
 * corresponding methods (annotated with @Test) 
 * 
 * Note: Gating XML files should denote their expected results in the comments for
 * clarity and also for which FCS file the expected results are for.
 * 
 * @author echng
 */
public class GateTestHarness {

	/**
	 * The root directory for all gating test files. (It has the trailing slash).
	 */
	public static final String GATING_TEST_FILE_DIRECTORY = "file:src/org/flowcyt/facejava/gating/test/files/";
	
	/**
	 * The base directory for the FCS files that are used during testing.
	 */
	public static final String FCS_DIRECTORY = "file:src/org/flowcyt/facejava/gating/test/files/fcs/";
	
	/**
	 * The default FCS file to use when testing. It contains one event at (100, 200) with 
	 * parameters (FS, SS).
	 */
	public static final String DEFAULT_GATING_TEST_FCS_FILE = FCS_DIRECTORY + "int-gating_test_file.fcs";	
	
	protected PopulationAnalysisResult result;
	
	protected GateSet gateColl;
	
	private Map<String, Integer> expectedInsideEventCount = new HashMap<String, Integer>();
	
	/**
	 * Constructor. Anslysis will be done using the gates in the given file and on the default 
	 * gating test fcs file.
	 * 
	 * @param gateFileURI The URI to the gating file to use in analysis.
	 * @throws Exception Since only valid  files are being tested, any exception is bad.
	 */
	public GateTestHarness(String gateFileURI) throws Exception {
		this(gateFileURI, DEFAULT_GATING_TEST_FCS_FILE);
	}
	
	/**
	 * Constructor. Runs the analysis using the given gating XML file and FCS file.
	 * 
	 * @param gateFileURI The URI to the gating file to use in analysis.
	 * @param fcsFileURI The URI to the FCS file to be analyzed.
	 * @throws Exception Since only valid  files are being tested, any exception is bad.
	 */
	public GateTestHarness(String gateFileURI, String fcsFileURI) throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(gateFileURI);
		gateColl = reader.read();
		
		FcsInput fcsAdapter = new CFCSInput();
		FcsDataFile fcsFile = fcsAdapter.read(fcsFileURI);
		
		Analyzer analyzer = new Analyzer(gateColl);
		
		PopulationCollectionAnalysisResult popCollResult = analyzer.analyze(fcsFile);
		
		// There better be one result since we should be analyzing at least one data set.
		result = popCollResult.getPopulationResults().get(0);
	}
	
	public void addExpectedInsideEventCount(String gateId, int expectedInsideCount) {
		expectedInsideEventCount.put(gateId, expectedInsideCount);
	}
	
	/**
	 * Makes sure that no errors occured during analysis (since we're testing valid
	 * files).
	 */
	public void testNoErrors() {
		Assert.assertFalse(result.hasErrors());
	}
	
	public void testInsideEventCountsCorrect() {
		for (Map.Entry<String, Integer> entry : expectedInsideEventCount.entrySet()) {
			Gate gate = gateColl.get(entry.getKey());
			GateSubPopulation gateResult = result.getGateResult(gate);
			boolean isEqual = gateResult.size() == entry.getValue();
			if (!isEqual) {
				System.out.println("Gate \"" + entry.getKey() + "\"; # Expected Inside: " + entry.getValue() + "; # Found Inside: " + gateResult.size());
			}
			Assert.assertTrue(isEqual);
		}
	}
	
	/**
	 * Prints the results of the analysis.
	 */
	public void printResults() {
		for (Map.Entry<String, Integer> entry : expectedInsideEventCount.entrySet()) {
			Gate gate = gateColl.get(entry.getKey());
			GateSubPopulation gateResult = result.getGateResult(gate);
			System.out.println("Gate \"" + entry.getKey() + "\";\t # Expected Inside: " + entry.getValue() + ";\t # Found Inside: " + gateResult.size());
		}
	}
	
}
