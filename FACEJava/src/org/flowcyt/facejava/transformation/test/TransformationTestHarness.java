package org.flowcyt.facejava.transformation.test;

import java.util.Collections;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.transformation.TransformationCollection;
import org.flowcyt.facejava.transformation.xmlio.TransformationMLFileReader;
import org.junit.Assert;

/**
 * A simple class to test arbitrary (but valid) transformations. 
 *  
 * @author echng
 */
public class TransformationTestHarness {

	public static final String TRANSFORMATION_TEST_FILE_DIRECTORY = "file:src/org/flowcyt/facejava/transformation/test/files/";
		
	public static final String FCS_FILE_DIR = "file:src/org/flowcyt/facejava/transformation/test/files/fcs/";
	
	private static final double EPSILON = 0.00000005;
	
	private TransformationCollection coll;
	
	public TransformationTestHarness(String xmlFileURI) throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(xmlFileURI);
		this.coll = reader.read();
	}
	
	public void testTransformation(String name, String fcsFileURI, double expected) throws Exception {
		testTransformation(name, fcsFileURI, expected, EPSILON);
	}
	
	public void testTransformation(String name, String fcsFileURI, double expected, double epsilon) throws Exception {
		CFCSInput fcsReader = new CFCSInput();
		FcsDataFile fcsFile = fcsReader.read(fcsFileURI);
		FcsDataSet ds = fcsFile.getByDataSetNumber(1);
		
		DataRetriever retriever = new DataRetriever(ds.getRetriever(), Collections.singletonList(coll));
		
		double data = retriever.getScale(new ParameterReference(name), ds.get(0));
		Assert.assertEquals(expected, data, epsilon);
	}
}
