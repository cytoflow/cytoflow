package org.flowcyt.facejava.gating.runner;

import java.io.File;
import java.util.Arrays;
import java.util.List;

import javax.xml.bind.ValidationEvent;

import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;

/**
 * Simple class to test gate loading.
 * 
 * @author echng
 */
public class Runner {
	public static void main(String[] args) throws Exception {
		List<File> sampleFiles = Arrays.asList(
				new File("src/org/flowcyt/gating/test/files/bool/InvalidGateReference.xml")
		);
			
		for (File file : sampleFiles) {
			GatingMLFileReader reader = new GatingMLFileReader(file);
			try{
				GateSet gc = reader.read();
				
				System.out.println("*** " + file + " ***");
				System.out.println("Number of Gates = " + gc.size());
				
				for (Gate gate : gc) {
					System.out.println(gate);
				}
				
				System.out.println();
			} catch (InvalidGatingMLFileException e) {
				e.printStackTrace();
				ValidationEvent[] problems =  reader.getValidationEvents();
				for (int i = 0; i < problems.length; ++i) {
					System.out.println(problems[i]);
				}				
			}
		}		
	}
}
