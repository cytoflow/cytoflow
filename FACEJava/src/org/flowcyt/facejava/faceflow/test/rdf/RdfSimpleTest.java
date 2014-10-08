package org.flowcyt.facejava.faceflow.test.rdf;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.flowcyt.facejava.faceflow.test.TestFileConstants;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

public class RdfSimpleTest {
	
	private static RdfProcessingTestHarness harness;
	
	private static List<ParameterReference> basicRefs;
	
	private static List<ParameterReference> withTransformationRefs;
	
	private Set<double[]> expectedEventValues;
	
	@BeforeClass
	public static void oneTimeSetUp() throws Exception {
		harness = new RdfProcessingTestHarness(TestFileConstants.RDF_TEST_FILE_DIRECTORY + "SimpleTest.rdf");
		
		basicRefs = new ArrayList<ParameterReference>();
		basicRefs.add(new ParameterReference("AS"));
		basicRefs.add(new ParameterReference("BS"));
		
		withTransformationRefs = new ArrayList<ParameterReference>(basicRefs);
		withTransformationRefs.add(new ParameterReference("DoubleBS"));
	}
	
	@Before
	public void setUp() {
		expectedEventValues = new HashSet<double[]>();
	}
	
	@Test public void testNoRelations() throws Exception{
		expectedEventValues.add(new double[] {10, 20});
		expectedEventValues.add(new double[] {30, 40});
		
		harness.testExpectedValues("int-2_ds_2_events_2_parameters-1-DS1", basicRefs, expectedEventValues);
	}
	
	@Test public void testG() throws Exception {
		expectedEventValues.add(new double[] {70, 80});
		
		harness.testExpectedValues("int-2_ds_2_events_2_parameters-1-DS2-GASGate", basicRefs, expectedEventValues);
		
		expectedEventValues.clear();
		expectedEventValues.add(new double[] {50, 60});
		
		harness.testExpectedValues("int-2_ds_2_events_2_parameters-1-DS2-GNotASGate", basicRefs, expectedEventValues);
	}
	
	@Test public void testT() throws Exception {
		expectedEventValues.add(new double[] {90, 100, 200});
		expectedEventValues.add(new double[] {110, 120, 240});
		
		harness.testExpectedValues("int-2_ds_2_events_2_parameters-2-DS1", withTransformationRefs, expectedEventValues);
	}
	
	@Test public void testTG() throws Exception {
		expectedEventValues.add(new double[] {150, 160, 320});
		
		harness.testExpectedValues("int-2_ds_2_events_2_parameters-2-DS2-GDoubleBSGate", withTransformationRefs, expectedEventValues);
		
		expectedEventValues.clear();
		expectedEventValues.add(new double[] {130, 140, 280});
		
		harness.testExpectedValues("int-2_ds_2_events_2_parameters-2-DS2-GNotDoubleBSGate", withTransformationRefs, expectedEventValues);
	}
	
	@Test public void testC() throws Exception {
		expectedEventValues.add(new double[] {152.7638190955, 172.3618090452});
		expectedEventValues.add(new double[] {170.8542713568, 191.4572864322});
		
		harness.testExpectedValues("int-4_ds_2_events_2_parameters-DS1-CASBSMatrix", basicRefs, expectedEventValues);
	}
	
	@Test public void testCT() throws Exception {
		expectedEventValues.add(new double[] {188.9447236181, 210.5527638191, 421.1055276382});
		expectedEventValues.add(new double[] {207.0351758794, 229.648241206, 459.296482412});
		
		harness.testExpectedValues("int-4_ds_2_events_2_parameters-DS2-CASBSMatrix", withTransformationRefs, expectedEventValues);
	}
	
	@Test public void testCG() throws Exception {
		expectedEventValues.add(new double[] {243.216080402,  267.8391959799});
		
		harness.testExpectedValues("int-4_ds_2_events_2_parameters-DS3-CASBSMatrix-GASGate", basicRefs, expectedEventValues);
		
		expectedEventValues.clear();
		expectedEventValues.add(new double[] {225.1256281407, 248.743718593});
		
		harness.testExpectedValues("int-4_ds_2_events_2_parameters-DS3-CASBSMatrix-GNotASGate", basicRefs, expectedEventValues);
	}
	
	@Test public void testCTG() throws Exception {
		expectedEventValues.add(new double[] {279.3969849246, 306.0301507538, 612.0603015076});
		
		harness.testExpectedValues("int-4_ds_2_events_2_parameters-DS4-CASBSMatrix-GDoubleBSGate", withTransformationRefs, expectedEventValues);
		
		expectedEventValues.clear();
		expectedEventValues.add(new double[] {261.3065326633, 286.9346733668, 573.8693467336});
		
		harness.testExpectedValues("int-4_ds_2_events_2_parameters-DS4-CASBSMatrix-GNotDoubleBSGate", withTransformationRefs, expectedEventValues);
	}	
}
