package org.flowcyt.facejava.transformation.runner;

import org.flowcyt.facejava.fcsdata.Parameter;
import org.flowcyt.facejava.transformation.TransformationCollection;
import org.flowcyt.facejava.transformation.xmlio.TransformationMLFileReader;

/**
 * Simple test class for reading a TransformationML file.
 * 
 * @author echng
 */
public class Runner {

	public static void main(String[] args) throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader("file:src/org/flowcyt/transformation/test/files/UniversalTransformations.xml");
		TransformationCollection coll = reader.read();
		
		for (Parameter param : coll)
			System.out.println(param);

	}

}
