package org.flowcyt.facejava.faceflow.application;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

import org.kohsuke.args4j.Argument;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.Option;

/**
 * <p>
 * CommandLineOptions is a class for use with the args4j library to parse and 
 * contain the command line arguments and options.
 * 
 * @author echng
 */
public class CommandLineOptions {
	/**
	 * The Usage string to print when errors are made.
	 */
	public static final String USAGE_STRING = "USAGE: java -jar faceflow.jar [options...] rdf_files...";
	
	/**
	 * args4j uses annotations to specify what should be parsed and how. See their
	 * documentation for more info.
	 */
	
	@Option(name="-f",usage="Specify an FCS File.\n* Required when no RDF files are specified.\n* Ignored when RDF files are specified.")
	private File fcsFile;
	
	@Option(name="-c",usage="Specify a Compensation-ML file to use on the FCS file.\n* Ignored when RDF files are specified.")
	private File compensationFile;
	
	@Option(name="-m",usage="Specify the id of the spilloverMatrix element to use in the\nCompensation-ML file. The matrix will be used on all data sets in\nthe FCS file.\n* Required when -c is used.\n* Ignored when RDF files are specified.")
	private String matrixId = null;
	
	@Option(name="-t",usage="Specify a Transformation-ML to use with the FCS file.\n* Ignored when RDF files are specified.")
	private File transformationFile;
	
	@Option(name="-g",usage="Specify a Gating-ML file to use on the FCS file.\n* Ignored when RDF files are specified.")
	private File gatingFile;
	
	@Option(name="-gate",usage="Specify the id of the gate to use in the Gating-ML file.\n* Optional. If not given, all gates in the file are used.\n* Ignored when -g is not given.")
	private String gateId = null;
	
	@Option(name="-d",usage="The resulting FCS files will be written to this directory.\n* Defaults to the current directory.")
	private File outputDirectory;
	
	@Option(name="-q",usage="Quiet Mode. Suppresses screen output.")
	private boolean quiet;
	
	@Option(name="-r",usage="Determine relations but do not output any FCS files.")
	private boolean testRun;
	
	@Option(name="-double",usage="If set, outputted FCS files will have double data.\n* Defaults to float data.")
	private boolean writeDoubles;
		
	@Argument
	private List<String> rdfFileList = new ArrayList<String>();
	
	/**
	 * Validates the options.
	 * 
	 * @return Returns true if the options are valid.
	 * @throws CmdLineException Thrown if the options/arguments don't meet the
	 * validation rules. The message string will contain the reason.
	 */
	public boolean validate() throws CmdLineException {
		if (rdfFileList.isEmpty() && fcsFile == null)
			throw new CmdLineException("-f is required if no RDF files are specified.");
		
		if (compensationFile != null && (matrixId == null || "".equals(matrixId)))
			throw new CmdLineException("-m is required if a Compensation-ML file is specified.");
		
		if (outputDirectory != null && !outputDirectory.canWrite())
			throw new CmdLineException("Cannot write to output directory given by -d option.");
		
		return true;
	}

	public File getCompensationFile() {
		return compensationFile;
	}

	public File getFcsFile() {
		return fcsFile;
	}

	public File getGatingFile() {
		return gatingFile;
	}

	public String getMatrixId() {
		return matrixId;
	}
	
	public String getGateId() {
		return gateId;
	}

	public File getOutputDirectory() {
		return outputDirectory;
	}

	public boolean isQuiet() {
		return quiet;
	}

	public List<String> getRdfFileList() {
		return rdfFileList;
	}

	public boolean isTestRun() {
		return testRun;
	}
	
	public boolean isWriteDoubles() {
		return writeDoubles;
	}

	public File getTransformationFile() {
		return transformationFile;
	}
}
