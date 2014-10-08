package org.flowcyt.facejava.gating.test;

import java.util.HashMap;
import java.util.Map;

import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.gates.bool.BooleanGate;
import org.flowcyt.facejava.gating.gates.decisiontree.DecisionTreeGate;
import org.flowcyt.facejava.gating.gates.geometric.EllipsoidGate;
import org.flowcyt.facejava.gating.gates.geometric.PolygonGate;
import org.flowcyt.facejava.gating.gates.geometric.PolytopeGate;
import org.flowcyt.facejava.gating.gates.geometric.RectangleGate;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Assert;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Tests that Gates are loaded and created correctly.
 * 
 * @author echng
 */
public class GateCollectionTest {
	private static final String GATE_COLLECTION_TEST_FILE = GateTestHarness.GATING_TEST_FILE_DIRECTORY + "CombinedGates.xml";
	
	private static GateSet gateColl;
	
	private static int expectedGateCount;
	
	private static Map<String, Class<? extends Gate>> expectedGatesMap = new HashMap<String, Class<? extends Gate>>();
	
	@BeforeClass public static void oneTimeSetUp() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(GATE_COLLECTION_TEST_FILE);
		
		gateColl = reader.read();
		
		expectedGateCount = 91;

		expectedGatesMap.put("Lymphocytes", EllipsoidGate.class);
		expectedGatesMap.put("x2", EllipsoidGate.class);
		expectedGatesMap.put("ellipse", EllipsoidGate.class);
		expectedGatesMap.put("ellipsoid_3D", EllipsoidGate.class);
		expectedGatesMap.put("ellipsoid3D", EllipsoidGate.class);
		expectedGatesMap.put("ball3D", EllipsoidGate.class);
		expectedGatesMap.put("ellipse1", EllipsoidGate.class);
		expectedGatesMap.put("ellipse2", EllipsoidGate.class);
		expectedGatesMap.put("ellipse1.1", EllipsoidGate.class);
		
		expectedGatesMap.put("CD3_Positive", RectangleGate.class);
		expectedGatesMap.put("CD3", RectangleGate.class);
		expectedGatesMap.put("CD5", RectangleGate.class);
		expectedGatesMap.put("G1", RectangleGate.class);
		expectedGatesMap.put("G2", RectangleGate.class);
		expectedGatesMap.put("G3", RectangleGate.class);
		expectedGatesMap.put("G4", RectangleGate.class);
		expectedGatesMap.put("CD4", RectangleGate.class);
		expectedGatesMap.put("CD4_test", RectangleGate.class);
		expectedGatesMap.put("gate", RectangleGate.class);
		
		expectedGatesMap.put("PolyGate1", PolygonGate.class);
		expectedGatesMap.put("PolyGate2", PolygonGate.class);
		expectedGatesMap.put("Triangle", PolygonGate.class);
		
		expectedGatesMap.put("OneDPolytope", PolytopeGate.class);
		expectedGatesMap.put("PolyGate", PolytopeGate.class);
		expectedGatesMap.put("cube", PolytopeGate.class);
		
		expectedGatesMap.put("Polygon_as_a_Decision_Tree_1", DecisionTreeGate.class);
		expectedGatesMap.put("Polygon_as_a_Decision_Tree_2", DecisionTreeGate.class);
		expectedGatesMap.put("simple_DST", DecisionTreeGate.class);
		expectedGatesMap.put("Polygon_as_a_Decision_Tree", DecisionTreeGate.class);
		expectedGatesMap.put("AlternativeDST", DecisionTreeGate.class);
		expectedGatesMap.put("Polygon_as_a_Decision_Tree_from_Doc", DecisionTreeGate.class);
		expectedGatesMap.put("polygon_as_a_Decision_Tree_from_Doc2", DecisionTreeGate.class);
		expectedGatesMap.put("DST_with_Redundant_Node", DecisionTreeGate.class);
		
		expectedGatesMap.put("FS-", BooleanGate.class);
		expectedGatesMap.put("GG1", BooleanGate.class);
		expectedGatesMap.put("GG2", BooleanGate.class);
		expectedGatesMap.put("GG4", BooleanGate.class);
		expectedGatesMap.put("g1", BooleanGate.class);
		expectedGatesMap.put("g2", BooleanGate.class);
		expectedGatesMap.put("x1", BooleanGate.class);
		expectedGatesMap.put("g3", BooleanGate.class);
		expectedGatesMap.put("xx2", BooleanGate.class);
		expectedGatesMap.put("x3", BooleanGate.class);
		expectedGatesMap.put("g4", BooleanGate.class);
		expectedGatesMap.put("x4", BooleanGate.class);
		expectedGatesMap.put("BoolSample_1", BooleanGate.class);
		expectedGatesMap.put("BoolSample2", BooleanGate.class);
		expectedGatesMap.put("x5", BooleanGate.class);
		expectedGatesMap.put("BoolSample_2", BooleanGate.class);
		expectedGatesMap.put("Bool_Sample_2", BooleanGate.class);
		expectedGatesMap.put("Bool_Sample_3", BooleanGate.class);
		expectedGatesMap.put("x8", BooleanGate.class);
		expectedGatesMap.put("BoolSample1", BooleanGate.class);
		expectedGatesMap.put("BoolSample3", BooleanGate.class);
		expectedGatesMap.put("BoolSample3a", BooleanGate.class);
		expectedGatesMap.put("FSC-H-minus", BooleanGate.class);
		expectedGatesMap.put("G1x", BooleanGate.class);
		expectedGatesMap.put("G2x", BooleanGate.class);
		expectedGatesMap.put("G4x", BooleanGate.class);
		expectedGatesMap.put("G1y", BooleanGate.class);
		expectedGatesMap.put("G2y", BooleanGate.class);
		expectedGatesMap.put("just_random_1", BooleanGate.class);
		expectedGatesMap.put("G3y", BooleanGate.class);
		expectedGatesMap.put("just_random_2", BooleanGate.class);
		expectedGatesMap.put("just_random_3", BooleanGate.class);
		expectedGatesMap.put("G4y", BooleanGate.class);
		expectedGatesMap.put("just_random_4", BooleanGate.class);
		
		// Referenced by boolean gates
		expectedGatesMap.put("Lymphocytes_1", EllipsoidGate.class);
		expectedGatesMap.put("x7", EllipsoidGate.class);
		expectedGatesMap.put("x9", EllipsoidGate.class);
		expectedGatesMap.put("x21", EllipsoidGate.class);
		expectedGatesMap.put("xb3", EllipsoidGate.class);
		
		expectedGatesMap.put("PolyGate11", PolytopeGate.class);
		
		expectedGatesMap.put("FS-P", RectangleGate.class);
		expectedGatesMap.put("SS-P", RectangleGate.class);
		expectedGatesMap.put("SS-", RectangleGate.class);
		expectedGatesMap.put("FS1-P", RectangleGate.class);
		expectedGatesMap.put("SS1-P", RectangleGate.class);
		expectedGatesMap.put("GG3", RectangleGate.class);
		expectedGatesMap.put("RectGate11", RectangleGate.class);
		expectedGatesMap.put("Lymphocytes33", RectangleGate.class);
		expectedGatesMap.put("x6", RectangleGate.class);
		expectedGatesMap.put("x11", RectangleGate.class);
		expectedGatesMap.put("FSC-H-plus", RectangleGate.class);
		expectedGatesMap.put("G3x", RectangleGate.class);
		expectedGatesMap.put("SSC-H-plus", RectangleGate.class);
		expectedGatesMap.put("SSC-H-minus", RectangleGate.class);
		expectedGatesMap.put("FSC-H-pluss", RectangleGate.class);
		expectedGatesMap.put("SSC-H-pluss", RectangleGate.class);
	}
	
	@Test public void testAllGatesLoaded() {
		Assert.assertEquals(gateColl.size(), expectedGateCount);
	}
	
	@Test public void testGateRetrieval() {
		for (String gateId : expectedGatesMap.keySet()) {
			Gate gate = gateColl.get(gateId);
			Assert.assertEquals(gateId, gate.getId());
		}
	}
	
	/**
	 * Make sure the GateFactory is creating the right types of gates. (It should
	 * since they have different constructor signatures...)
	 *
	 */
	@Test public void testGateCreation() {
		for (Map.Entry<String, Class<? extends Gate>> entry : expectedGatesMap.entrySet()) {
			Gate gate = gateColl.get(entry.getKey());
			Assert.assertEquals(entry.getValue(), gate.getClass());
		}
	}
}
