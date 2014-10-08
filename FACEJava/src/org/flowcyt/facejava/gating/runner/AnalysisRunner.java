package org.flowcyt.facejava.gating.runner;

import java.io.FileOutputStream;
import java.io.PrintStream;

import javax.xml.bind.ValidationEvent;

import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.fcsdata.io.FcsInput;
import org.flowcyt.facejava.gating.analysis.Analyzer;
import org.flowcyt.facejava.gating.analysis.PopulationCollectionAnalysisResult;
import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;

/** 
 * Simple class to test analysis.
 * 
 * @author echng
 */
public class AnalysisRunner {
	
	public static void main(String[] args) throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader("file:src/org/flowcyt/gating/test/files/bd/GatingTest4.xml");
		try {
			GateSet gateColl = reader.read();
			
			FcsInput adapter = new CFCSInput();
			FcsDataFile fcsFile = adapter.read("file:src/org/flowcyt/gating/test/files/fcs/bd/c4");
			
			Analyzer analyzer = new Analyzer(gateColl);
			
			PopulationCollectionAnalysisResult result = analyzer.analyze(fcsFile);
			
			FileOutputStream out = new FileOutputStream("analyzer-results.txt");
			PrintStream p = new PrintStream(out);
			System.out.println(result);
			p.println(result);
		} catch (InvalidGatingMLFileException e) {
			ValidationEvent[] problems =  reader.getValidationEvents();
			for (int i = 0; i < problems.length; ++i) {
				System.out.println(problems[i]);
			}
			e.printStackTrace();
		}
	}
	
}
