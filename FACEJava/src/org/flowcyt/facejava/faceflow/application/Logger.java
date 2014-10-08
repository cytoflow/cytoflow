package org.flowcyt.facejava.faceflow.application;

import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;

import org.flowcyt.facejava.faceflow.relations.DataSetRelations;
import org.flowcyt.facejava.gating.gates.Gate;

/**
 * <p>
 * Logger is used to log the events that happen as FACEFlow runs. It prints
 * info about the events to the OutputStream given at construction. If null is given
 * no output is generated.
 * 
 * @author echng
 */
public class Logger {
	/**
	 * The following are some String constants which appear regularly in the output.
	 */
	
	public static final String SECTION_MARKER = "* ";
	
	public static final String ERROR_MARKER = "!!! ";
	
	public static final String DATA_SET_MARKER = "- ";
	
	public static final String RELATION_MARKER = "-- ";
	
	public static final String BEGIN_DESCRIPTION = "Start: ";
	
	public static final String END_DESCRIPTION = "Finished: ";
	
	public static final String ERROR_DESCRIPTION = "Error: ";
	
	public static final String SKIP_DESCRIPTION = "Skipped: ";
	
	public static final String PREVIOUS_ERROR_DESCRIPTION = "Previously found error loading ";
	
	public static final String ELLIPSIS = "...";
	
	public static final String SKIP_DATA_SET_MESSAGE = "Skipping Data Set. ";
	
	public static final String SKIP_GATE_MESSAGE = "Skipping Gate ";
	
	public static final String DATA_SET_SUCCESS = "Completed";
	
	public static final String DATA_SET_ERROR = "Skipped";
	
	/**
	 * The Stream to print to.
	 */
	public PrintStream out;
	
	/**
	 * Constructor.
	 * 
	 * @param outStream The OutputStream to print to. If null, no output will
	 * be generated.
	 */
	public Logger(OutputStream outStream) {
		if (outStream == null)
			this.out = new PrintStream(new NullOutputStream());
		else
			this.out = new PrintStream(outStream);
	}
	
	public void logSectionStart(String sectionName) {
		out.println(SECTION_MARKER + BEGIN_DESCRIPTION + sectionName + ELLIPSIS);
	}
	
	public void logSectionEnd(String sectionName) {
		out.println(SECTION_MARKER + END_DESCRIPTION  + sectionName + ELLIPSIS);
	}
	

	public void logSectionSkip(String sectionName, String reason) {
		out.println(SECTION_MARKER + SKIP_DESCRIPTION + sectionName + ". " + reason);
	}
	
	public void logFileError(String location, Exception e) {
		out.println(ERROR_MARKER + "Error loading " + location + ": " + e.getMessage());
	}
	
	public void logDataSetStart(DataSetRelations relations) {
		out.println(DATA_SET_MARKER + BEGIN_DESCRIPTION + "Data Set #" + relations.getDataSet().getDataSetNumber() + " in " + relations.getDataFileLocation());
	}
	
	public void logDataSetEnd(DataSetRelations relations, boolean successful) {
		out.println(DATA_SET_MARKER + END_DESCRIPTION + (successful ? DATA_SET_SUCCESS : DATA_SET_ERROR) + " Data Set #" + relations.getDataSet().getDataSetNumber() + " in " + relations.getDataFileLocation());
	}
	
	public void logRelationError(Exception e) {
		out.println(ERROR_MARKER + SKIP_DATA_SET_MESSAGE + ERROR_DESCRIPTION + e.getMessage());
		e.printStackTrace();
	}
	
	public void logGateError(Gate g, Exception e) {
		out.println(ERROR_MARKER + SKIP_GATE_MESSAGE + g.getId() + ". " + ERROR_DESCRIPTION  + " -- " + e.getMessage());
	}
	
	public void logNoGateError(String gateId) {
		out.println(ERROR_MARKER + "No gate element with id \"" + gateId + "\" found. " + SKIP_DATA_SET_MESSAGE);
	}
	
	public void logCompensationError(String matrixId) {
		out.println(ERROR_MARKER + "No spilloverMatrix element with id \"" + matrixId + "\" found. " + SKIP_DATA_SET_MESSAGE);
	}
	
	public void logNoMatrixError() {
		out.println(ERROR_MARKER + "No spilloverMatrix id given. Cannot perform compensation." + SKIP_DATA_SET_MESSAGE);
	}
	
	public void logPreviousRelationError(String relationName, String location) {
		out.println(ERROR_MARKER  + SKIP_DATA_SET_MESSAGE + PREVIOUS_ERROR_DESCRIPTION + relationName + " file: " + location);
	}
	
	public void logLoadedRelation(String relationName, String location) {
		out.println(RELATION_MARKER + "Loading related " + relationName + " file: " + location);
	}
	
	public void logIgnoredRelation(String relationName, String location) {
		out.println(RELATION_MARKER + "Ignoring " + relationName + " relation -- " + location);
	}
	
	public void logDefaultRelation(String className) {
		out.println(RELATION_MARKER + "Found " + className + " relation which cannot be processed because it is not known.");
	}
	
	public void logWritingDataSet(File f) {
		out.println(DATA_SET_MARKER + "Writing result to " + f.getPath());		
	}
	
	public void logWritingDataSetError(Exception e) {
		out.println(ERROR_MARKER + "Output " + ERROR_DESCRIPTION + e.getMessage());
	}
	
	/**
	 * A class which does not generate any output (i.e., much like > /dev/null).
	 * 
	 * @author echng
	 */
	public static class NullOutputStream extends OutputStream {
		@Override
		public void write(int b) throws IOException {
			// Do nothing.
		}
	}
}
