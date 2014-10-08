package org.flowcyt.facejava.compensation.test;

import java.util.HashSet;
import java.util.Set;

import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Runs test for copmensation when only two parameters are to be compensated. See the comments of
 * the CompensationML test file for the expected results. 
 * 
 * @author echng
 */
public class TwoParameterCompensatorTests {
	private static final String MATRIX_FILE_URI = CompensatorTestHarness.TEST_FILE_DIRECTORY + "TwoParameterCompensation.xml";
	
	private static CompensatorTestHarness harness;
	
	private Set<String> expectedReferences;
	
	@BeforeClass public static void oneTimeSetup() throws Exception {
		harness = new CompensatorTestHarness(MATRIX_FILE_URI);
	}
	
	@Before public void setUp() {
		expectedReferences = new HashSet<String>();
	}
	
	@Test public void testParametersEqual() throws Exception {
		expectedReferences.add("AS");
		expectedReferences.add("BS");
		
		double[][] expectedEventsData = {
			{7.4034902168165, 19.7778952934955},
			{25.3833950290851, 39.2384981491274},
			{43.3632998413538, 58.6991010047594},
			{61.3432046536224, 78.1597038603913},
			{79.3231094658911, 97.6203067160233},
			{97.3030142781597, 117.080909571655},
			{115.282919090428, 136.541512427287},
			{133.262823902697, 156.002115282919},
			{151.242728714966, 175.462718138551},
			{169.222633527234, 194.923320994183}
		};
		
		harness.runTestSequence("Equal", 
				CompensatorTestHarness.FCS_TEST_FILE_DIRECTORY + "int-10_events_2_parameters.fcs", 
				expectedEventsData,
				expectedReferences);
	}
	
	@Test public void testSSubD() throws Exception {
		expectedReferences.add("AS");
		expectedReferences.add("BS");
		
		double[][] expectedEventsData = {
			{10.752688172043, 17.5268817204301, 30.0, 40.0},
			{53.763440860215, 47.6344086021505, 70.0, 80.0},
			{96.7741935483871, 77.741935483871, 110.0, 120.0},
			{139.784946236559, 107.849462365591, 150.0, 160.0},
			{182.795698924731, 137.956989247312, 190.0, 200.0},
			{225.806451612903, 168.064516129032, 230.0, 240.0},
			{268.817204301075, 198.172043010753, 270.0, 280.0},
			{311.827956989247, 228.279569892473, 310.0, 320.0},
			{354.838709677419, 258.387096774194, 350.0, 360.0},
			{397.849462365591, 288.494623655914, 390.0, 400.0}
		};
		
		harness.runTestSequence("S-Sub-D", 
				CompensatorTestHarness.FCS_TEST_FILE_DIRECTORY + "int-10_events_4_parameters.fcs", 
				expectedEventsData,
				expectedReferences);
	}
	
	@Test public void testDSubS() throws Exception {
		expectedReferences.add("AS");
		expectedReferences.add("BS");
		
		double[][] expectedEventsData = {
			{6.71591312366876, 19.9023506231819},
			{23.4558764035642, 39.6589515570922},
			{40.1958396834597, 59.4155524910025},
			{56.9358029633551, 79.1721534249128},
			{73.6757662432506, 98.9287543588231},
			{90.415729523146, 118.685355292733},
			{107.155692803042, 138.441956226644},
			{123.895656082937, 158.198557160554},
			{140.635619362832, 177.955158094464},
			{157.375582642728, 197.711759028375}
		};
		
		harness.runTestSequence("D-Sub-S", 
				CompensatorTestHarness.FCS_TEST_FILE_DIRECTORY + "int-10_events_2_parameters.fcs", 
				expectedEventsData,
				expectedReferences);
	}
	
	@Test public void testDIntS() throws Exception {
		expectedReferences.add("BS");
		expectedReferences.add("DS");
		
		double[][] expectedEventsData = {
			{10.0, -7.81060871781485, 30.0, 40.9642196462142},
			{50.0, 6.20832062422176, 70.0, 79.2335828189398},
			{90.0, 20.2272499662584, 110.0, 117.502945991665},
			{130.0, 34.246179308295, 150.0, 155.772309164391},
			{170.0, 48.2651086503316, 190.0, 194.041672337117},
			{210.0, 62.2840379923682, 230.0, 232.311035509842},
			{250.0, 76.3029673344047, 270.0, 270.580398682568},
			{290.0, 90.3218966764414, 310.0, 308.849761855293},
			{330.0, 104.340826018478, 350.0, 347.119125028019},
			{370.0, 118.359755360515, 390.0, 385.388488200744}
		};
		
		harness.runTestSequence("D-Int-S", 
				CompensatorTestHarness.FCS_TEST_FILE_DIRECTORY + "int-10_events_4_parameters.fcs", 
				expectedEventsData,
				expectedReferences);
	}
	
	@Test public void testNoParams() throws Exception {
		// No params should be compensated
		
		double[][] expectedEventsData = {
			{10.0, 20.0, 30.0, 40.0},
			{50.0, 60.0, 70.0, 80.0},
			{90.0, 100.0, 110.0, 120.0},
			{130.0, 140.0, 150.0, 160.0},
			{170.0, 180.0, 190.0, 200.0},
			{210.0, 220.0, 230.0, 240.0},
			{250.0, 260.0, 270.0, 280.0},
			{290.0, 300.0, 310.0, 320.0},
			{290.0, 300.0, 310.0, 320.0},
			{370.0, 380.0, 390.0, 400.0}
		};
		
		harness.runTestSequence("NoParams", 
				CompensatorTestHarness.FCS_TEST_FILE_DIRECTORY + "int-10_events_4_parameters.fcs", 
				expectedEventsData,
				expectedReferences);
	}
}
