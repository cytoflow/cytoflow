package org.flowcyt.facejava.fcsdata.runner;

import java.io.File;
import java.net.URL;

import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.fcsdata.io.CFCSOutput;
import org.flowcyt.facejava.fcsdata.io.FcsInput;
import org.flowcyt.facejava.fcsdata.io.FcsOutput;

/**
 * A simple application which loads FCS files. Mainly used for testing.
 * 
 * @author echng
 */
public class Runner {

	public static void main(String[] args) {
		try {
			FcsInput adapter = new CFCSInput();
			FcsDataFile dataFile = adapter.read(new File("E:\\Bad FCS\\doubles.fcs"));
			for (Population pop : dataFile) {
				printPopulation(pop);
			}
			
			FcsOutput outadapter = new CFCSOutput();
			outadapter.write(new URL("file:test.fcs"), dataFile);
			
			FcsDataFile writtenPopColl = adapter.read("file:test.fcs");
			for (Population pop : writtenPopColl) {
				printPopulation(pop);
			}
		} catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	private static void printPopulation(Population pop) throws Exception {
		System.out.println(pop);

		int numToPrint = 10;
		if (pop.size() < numToPrint)
			numToPrint = pop.size();
		System.out.println("*** " + numToPrint + " events:\n");
		
		int i = 0;
		for (Event ev : pop) {
			System.out.println("Event " + i++ + ": " + ev);
			if (i == numToPrint)
				break;
		}
		
		System.out.println(pop.getStatistics());
	}
}
