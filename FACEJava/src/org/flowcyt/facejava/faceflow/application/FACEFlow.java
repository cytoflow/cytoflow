package org.flowcyt.facejava.faceflow.application;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.flowcyt.facejava.faceflow.application.outputlayers.OutputLayer;
import org.flowcyt.facejava.faceflow.exception.DuplicateRelationException;
import org.flowcyt.facejava.faceflow.loader.FileLoader;
import org.flowcyt.facejava.faceflow.loader.LocalFileLoader;
import org.flowcyt.facejava.faceflow.loader.URIFileLoader;
import org.flowcyt.facejava.faceflow.relations.CompensationRelation;
import org.flowcyt.facejava.faceflow.relations.DataSetRelations;
import org.flowcyt.facejava.faceflow.relations.GatingRelation;
import org.flowcyt.facejava.faceflow.relations.RelationsRepository;
import org.flowcyt.facejava.faceflow.relations.RelationsRepositoryIterator;
import org.flowcyt.facejava.faceflow.relations.SimpleRelationsRepository;
import org.flowcyt.facejava.faceflow.relations.TransformationRelation;
import org.flowcyt.facejava.faceflow.relations.rdf.RdfRelationsRepository;
import org.flowcyt.facejava.fcsdata.io.CFCSOutput;
import org.flowcyt.facejava.fcsdata.io.FcsOutput;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;

/**
 * <p>
 * The main application class for the FACEFlow application. It will parse
 * the command line and run the application accordingly.
 * 
 * <p>
 * The application can either be given an FCS file along with optionally
 * specifying a Compensation-ML, Gating-ML, and Transformation-ML file or one or more
 * RDF files.
 * 
 * <p>
 * If no RDF file is given, an FCS file must be specified. If an RDF file is given,
 * any FCS, Compensation-ML, Gating-ML, or Transformation-ML files will be ignored.
 * 
 * <p>
 * If given an RDF file, FACEFlow will process the relations as specified in the file. 
 * 
 * <p>
 * If given an FCS file, FACEFlow will associate any of the given *-ML files to
 * all of the data sets within the data file.
 * 
 * <p>
 * In either case, FACEFlow will output new FCS files where for each of the original
 * data sets will have had (if the relation exists) the compensation applied, the
 * transformations added (i.e., the transformed values will be in the new FCS file),
 * and a gate in the gating file applied (i.e., with 5 gates and 1 data set, there will
 * be 5 new FCS files -- one for each gate applied to the data set). If an
 * output directory is specified (-d), the new FCS files will be written there.
 * Otherwise, the current directory is used.
 * 
 * <p>
 * If -r is given, the correct relations will be determined, all specified files 
 * (including files specified within a RDF file) will be loaded. However, no new
 * FCS files will be written. This can be used to do a test run to find errors in
 * the specified relations or the specified files.
 * 
 * <p>
 * If quiet mode is given, no output will be written to stdout.
 * 
 * <p>
 * If -double is given, outputted FCS files will be written containing doubles (i.e.,
 * $DATATYPE is D). Defaults to writing floats (i.e., $DATATYPE is F).
 * 
 * @author echng
 */
public class FACEFlow {
	/**
	 * Used as a Section heading when reading FCS files.
	 */
	private static final String FCS_FILE_SECTION = "Loading FCS Files";
	
	/**
	 * Used as a Section heading when the correct relations are determined.
	 */
	private static final String RELATION_SECTION = "Processing relations";
	
	/**
	 * Used as a Section heading when writing the new FCS files.
	 */
	private static final String OUTPUT_SECTION = "Writing FCS result files";

	/**
	 * The default extension for FCS files.
	 */
	public static final String FCS_EXTENSION = ".fcs";
	
	/**
	 * main() function for FACEFlow. It'll parse and validate the command line 
	 * arguments before creating a new FACEFlow object to run the application.
	 * 
	 * @param args The Command Line arguments
	 */
	public static void main(String[] args) {
		CommandLineOptions options = new CommandLineOptions();
		CmdLineParser parser = new CmdLineParser(options);
		
		try {
			parser.parseArgument(args);
			if (options.validate()) {
				FACEFlow app = new FACEFlow(options);
				app.run();
			}			
		} catch (CmdLineException e) {
			System.err.println(CommandLineOptions.USAGE_STRING);
			System.err.print("ERROR: ");
			System.err.println(e.getMessage());
			System.err.println();
			parser.printUsage(System.err);
		}
	}
	
	/**
	 * The Logger class to use to log the progress of the applications.
	 */
	private Logger logger;
	
	/**
	 * Houses the arguments and options specified on the command line. 
	 */
	private CommandLineOptions options;
	
	/**
	 * Constructor. Creates a FACEFlow object which will run with the given options
	 * and arguments.
	 * 
	 * @param options The CommandLineOptions object which contains the options and
	 * arguments specified on the command line.
	 */
	public FACEFlow(CommandLineOptions options) {
		this.options = options;
		if (options.isQuiet())
			this.logger = new Logger(null);
		else
			this.logger = new Logger(System.out);
	}
	
	/**
	 * Runs the application according to the options given at start.
	 * See class comments.
	 */
	public void run() {
		FileLoader loader;
		if (options.getRdfFileList().isEmpty())
			loader = new LocalFileLoader();
		else
			loader = new URIFileLoader();
		
		
		for (RelationsRepository relRep : getRepositories()) {
			RelationsRepositoryIterator iterator = getRepositoryIterator(relRep, loader);
			LayerFactoryVisitor visitor = processRelations(iterator, loader);
			
			// Print out errors
			if (iterator.hasErrors()) {
				for (Map.Entry<String, Exception> entry : iterator.getErrors().entrySet()) {
					logger.logFileError(entry.getKey(), entry.getValue());
				}
			}
			
			outputResults(visitor);
		}
	}
	
	/**
	 * @return Returns a list of the RelationsRepositories to be processed. It
	 * uses the RDF files given as arguments or if there are none, the FCS and *-ML
	 * files given as options (as a single RelationsRepository). If multiple RDF
	 * files are given then there are multiple repositories.
	 */
	private List<RelationsRepository> getRepositories() {
		List<RelationsRepository> rv = new ArrayList<RelationsRepository>();
		
		if (options.getRdfFileList().isEmpty()) {
			rv.add(buildRelationsRepository());
		} else {
			for (String rdfFile : options.getRdfFileList()) {
				try {
					rv.add(new RdfRelationsRepository(rdfFile));
				} catch (IOException e) {
					logger.logFileError(rdfFile, e);
				}
			}
		}
		return rv;
		
	}
	
	/**
	 * Builds a SimpleRelationsRepository which contains only the FCS file specified
	 * with -f and any of the *-ML files specified related to all data sets within
	 * the FCS file.
	 * 
	 * @return Returns the built SimpleRelationsRepository
	 */
	private SimpleRelationsRepository buildRelationsRepository() {
		SimpleRelationsRepository rv = new SimpleRelationsRepository();
		
		try {
			if (options.getCompensationFile() != null)
				rv.addRelation(options.getFcsFile().getPath(), new CompensationRelation(options.getCompensationFile().getPath(), options.getMatrixId()));
		
			if (options.getTransformationFile() != null)
				rv.addRelation(options.getFcsFile().getPath(), new TransformationRelation(options.getTransformationFile().getPath()));
			
			if (options.getGatingFile() != null)
				rv.addRelation(options.getFcsFile().getPath(), new GatingRelation(options.getGatingFile().getPath(), options.getGateId()));
		} catch (DuplicateRelationException e) {
			throw new AssertionError("No duplicate relations can occur since we're manually building the repository.");
		}
				
		return rv;
	}
	
	/**
	 * Creates a RelationsRepositoryIterator given the RelationsRepository and
	 * the FileLoader to use to load the FCS files.
	 * 
	 * @param relRep The RelationsRepository the iterator is for.
	 * @param loader The FileLoader to use to load the FCS files in the
	 * RelationsRepository
	 * @return Returns the new iterator for the repository 
	 */
	private RelationsRepositoryIterator getRepositoryIterator(RelationsRepository relRep, FileLoader loader) {
		logger.logSectionStart(FCS_FILE_SECTION);
		
		RelationsRepositoryIterator iterator = new RelationsRepositoryIterator(relRep, loader);
		
		logger.logSectionEnd(FCS_FILE_SECTION);
		
		return iterator;
	}
	
	/**
	 * Given a RelationsRepositoryIterator and a FileLoader to use to load related
	 * *-ML files, a LayerFactoryVisitor will be created and used to process
	 * the DataSetRelations in the iterator.
	 * 
	 * @param iterator The RelationsRepositoryIterator to iterate through.
	 * @param loader The FileLoader to use to load related files.
	 * @return Returns the LayerFactoryVisitor that was used to visit the
	 * DataSetRelations in the iterator. The visitor will contain all the result
	 * layers.
	 */
	private LayerFactoryVisitor processRelations(RelationsRepositoryIterator iterator, FileLoader loader) {
		logger.logSectionStart(RELATION_SECTION);
		
		LayerFactoryVisitor visitor = new LayerFactoryVisitor(logger, loader);
		while (iterator.hasNext()) {
			DataSetRelations relations = iterator.next();
			relations.accept(visitor);
		}
		
		logger.logSectionEnd(RELATION_SECTION);
		
		return visitor;
	}
	
	/**
	 * Outputs the result layers in the visitor after processing relations to new
	 * FCS files.
	 * 
	 * @param visitor The visitor that was used to process the relations and that
	 * contains the result layers.
	 */
	private void outputResults(LayerFactoryVisitor visitor) {
		if (options.isTestRun()) {
			logger.logSectionSkip(OUTPUT_SECTION, "-r specified");
			return;
		}
			
		
		logger.logSectionStart(OUTPUT_SECTION);
		
		FcsOutput out = new CFCSOutput(options.isWriteDoubles());
		
		for (OutputLayer result : visitor.getFinalLayers()) {
			File outFile = makeOutputFile(options.getOutputDirectory(), result.getResultBaseName());
			logger.logWritingDataSet(outFile);
			try {
				out.write(outFile, result.getResultPopulation());
			} catch (Exception e) {
				logger.logWritingDataSetError(e);
			}
		}
		
		logger.logSectionEnd(OUTPUT_SECTION);
	}
	
	/**
	 * Makes a file name for the output file that does not yet exist.
	 * 
	 * @param directory The directory to place the file
	 * @param fileBaseName the base name of the file from the layer
	 * @return Returns a File which does not exist in the correct name format.
	 */
	private File makeOutputFile(File directory, String fileBaseName) {
		File rv = new File(directory, fileBaseName + FCS_EXTENSION);
		
		if (rv.exists()) {
			int i = 1;
			while (rv.exists()) {
				rv = new File(directory, fileBaseName + "(" + i + ")" + FCS_EXTENSION);
				++i;
			}			
		}
		
		return rv;
	}

}
