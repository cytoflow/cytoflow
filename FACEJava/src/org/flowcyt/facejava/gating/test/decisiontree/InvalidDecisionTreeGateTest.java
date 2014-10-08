package org.flowcyt.facejava.gating.test.decisiontree;

import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Test;

/**
 * Test invalid Decision Tree Gates
 * 
 * @author echng
 */
public class InvalidDecisionTreeGateTest {
	
	private static final String TEST_FILE_DIRECTORY = DecisionTreeGateTest.DECISION_TREE_TEST_FILE_DIRECTORY;
	
	private static final String MISSING_LEAF_FILE = TEST_FILE_DIRECTORY + "MissingLeaf.xml";
	
	private static final String NO_BRANCHES_FILE = TEST_FILE_DIRECTORY + "NoBranches.xml";

	private static final String NO_GTE_BRANCH_FILE = TEST_FILE_DIRECTORY + "NoGTEBranch.xml";

	private static final String NO_INSIDE_FILE = TEST_FILE_DIRECTORY + "NoInside.xml";

	private static final String NO_LT_BRANCH_FILE = TEST_FILE_DIRECTORY + "NoLTBranch.xml";
	
	private static final String NO_ROOT_NODE_FILE = TEST_FILE_DIRECTORY + "NoRootNode.xml";
	
	private static final String NO_THRESHOLD_FILE = TEST_FILE_DIRECTORY + "NoThreshold.xml";

	private static final String SAME_BRANCH_AND_LEAF_TYPE_FILE = TEST_FILE_DIRECTORY + "SameBranchAndLeafType.xml";

	private static final String SAME_BRANCH_TYPE_FILE = TEST_FILE_DIRECTORY + "SameBranchType.xml";

	private static final String SAME_LEAF_TYPE_FILE = TEST_FILE_DIRECTORY + "SameLeafType.xml";
	
	private static final String TOO_MANY_ROOT_NODES_FILE = TEST_FILE_DIRECTORY + "TooManyRootNodes.xml";
	
	private static final String GTE_BEFORE_LT_FILE = TEST_FILE_DIRECTORY + "GTEBeforeLT.xml";
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testMissingLeaf() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(MISSING_LEAF_FILE);
		reader.read();
	}

	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoBranches() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_BRANCHES_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoGTEBranch() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_GTE_BRANCH_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoInside() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_INSIDE_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoLTBranch() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_LT_BRANCH_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoRootNode() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_ROOT_NODE_FILE);
		reader.read();
	}

	@Test(expected=InvalidGatingMLFileException.class)
	public void testNoThreshold() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(NO_THRESHOLD_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testSameBranchAndLeafType() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(SAME_BRANCH_AND_LEAF_TYPE_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testSameBranchType() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(SAME_BRANCH_TYPE_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testSameLeafType() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(SAME_LEAF_TYPE_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testTooManyRootNodes() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(TOO_MANY_ROOT_NODES_FILE);
		reader.read();
	}
	
	@Test(expected=InvalidGatingMLFileException.class)
	public void testGTEBeforeLT() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(GTE_BEFORE_LT_FILE);
		reader.read();
	}
}
