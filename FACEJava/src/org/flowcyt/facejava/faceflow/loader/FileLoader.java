package org.flowcyt.facejava.faceflow.loader;

import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.faceflow.exception.FileLoaderException;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.io.FcsInput;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.transformation.TransformationCollection;

/**
 * <p>
 * Used to load all the different types of files that are supported. FileLoaders are
 * given the locations as Strings which may describe the location in one of many ways
 * (e.g., file paths, URIs, etc.). Implementations of FileLoader must make clear
 * which types of location Strings they can load.
 * 
 * <p>
 * FileLoaderExceptions are thrown which wrap the Exceptions that are thrown by the
 * classes that perform the actual loading. This is because of checked exceptions, where 
 * if one  of the file readers throws a new Exception type, the interface here and in all
 * subtypes must be changed if it were not for the FileLoaderException wrapper.
 * 
 * @author echng
 */
public interface FileLoader {
	
	/**
	 * Loads a Gating-ML file at the given Location.
	 * 
	 * @param location The location of the file as a string.
	 * @return Returns a GateSet that has the Gates that are in the File 
	 * @throws FileLoaderException Thrown if there was an error loading the file.
	 * Use getLinkedException() to get the actual cause.
	 */
	public GateSet loadGatingFile(String location) throws FileLoaderException;
	
	/**
	 * Loads a Transformation-ML file at the given location.
	 * 
	 * @param location The location of the file as a string.
	 * @return Returns a TransformationCollection that has the Transformations that
	 * are in the File.
	 * @throws FileLoaderException Thrown if there was an error loading the file.
	 * Use getLinkedException() to get the actual cause.
	 */
	public TransformationCollection loadTransformationFile(String location) throws FileLoaderException;
	
	/**
	 * Loads a Copmensation-ML file at the given Location.
	 * 
	 * @param location The location of the file as a string.
	 * @return Returns the SpilloverMatrixSet that has the SpilloverMatrices
	 * that are in the file.
	 * @throws FileLoaderException Thrown if there was an error loading the file.
	 * Use getLinkedException() to get the actual cause.
	 */
	public SpilloverMatrixSet loadCompensationFile(String location) throws FileLoaderException;
	
	/**
	 * Sets the FcsInput object to use when loading FCS Files.
	 * @param in The FcsInput object to use to load FCS files.
	 */
	public void setFcsInput(FcsInput in);
	
	/**
	 * Loads an FCS file at the given location.
	 * 
	 * @param location The location of the file as a string.
	 * @return Returns the FcsDataFile that has the FcsDataSets that are in the file.
	 * @throws FileLoaderException Thrown if there was an error loading the file.
	 * Use getLinkedException() to get the actual cause.
	 */
	public FcsDataFile loadFcsFile(String location) throws FileLoaderException;
}
