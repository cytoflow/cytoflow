package org.flowcyt.facejava.compensation.runner;

import org.flowcyt.facejava.compensation.SpilloverMatrix;
import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.compensation.xmlio.CompensationMLFileReader;

/**
 * Simple class for testing loading Compensation files.
 * 
 * @author echng
 */
public class Runner {
	public static void main(String[] args) throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader("file:src/org/flowcyt/compensation/test/files/CompensationExample.xml");
		SpilloverMatrixSet coll = reader.read();
		
		for (SpilloverMatrix matrix : coll) {
			System.out.println(matrix);
		}
	}

}
