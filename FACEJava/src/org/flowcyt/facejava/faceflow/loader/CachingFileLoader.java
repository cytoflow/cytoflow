package org.flowcyt.facejava.faceflow.loader;

import java.util.HashMap;
import java.util.Map;

import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.faceflow.exception.FileLoaderException;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.io.FcsInput;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.transformation.TransformationCollection;

/**
 * <p>
 * CachingFileLoader is an abstract class which will cache the results of successfully
 * loading the different types of files (GateSet, TransformationCollection,
 * etc.) based on their location. The loading methods maintain the cache, while it is
 * left to the subclasses to actually do the loading of the files (so that different
 * location string types can be handled) through the perform*Load abstract methods.
 * 
 * @author echng
 */
public abstract class CachingFileLoader implements FileLoader {
	/**
	 * Caches the GateCllections by mapping it from the location string.
	 */
	private Map<String, GateSet> gatingCache;
	
	/**
	 * Caches the TransformationCllections by mapping it from the location string.
	 */
	private Map<String, TransformationCollection> transformationCache;
	
	/**
	 * Caches the SpilloverMatrixCllections by mapping it from the location string.
	 */
	private Map<String, SpilloverMatrixSet> compensationCache;
	
	/**
	 * Caches the FcsDataFiles by mapping it from the location string.
	 */
	private Map<String, FcsDataFile> fcsCache;
	
	/**
	 * The FcsInput object to use to load FCS files
	 */
	protected FcsInput fcsIn;
	
	/**
	 * Constructor.
	 */
	public CachingFileLoader() {
		gatingCache = new HashMap<String, GateSet>();
		transformationCache = new HashMap<String, TransformationCollection>();
		compensationCache = new HashMap<String, SpilloverMatrixSet>();
		fcsCache = new HashMap<String, FcsDataFile>();
	}

	/**
	 * The results of a successful load are cached so that future calls with the
	 * same location string will return the cached SpilloverMatrixSet
	 * from the previous load.
	 */
	public SpilloverMatrixSet loadCompensationFile(String location) throws FileLoaderException {
		SpilloverMatrixSet rv;
		if (compensationCache.containsKey(location)) {
			rv = compensationCache.get(location);
		} else {
			rv = performCompensationLoad(location);			
			compensationCache.put(location, rv);
		}
		return rv;
	}

	/**
	 * The results of a successful load are cached so that future calls with the
	 * same location string will return the cached GateSet
	 * from the previous load.
	 */
	public GateSet loadGatingFile(String location) throws FileLoaderException {
		GateSet rv;
		if (gatingCache.containsKey(location)) {
			rv = gatingCache.get(location);
		} else {
			rv = performGatingLoad(location);
			gatingCache.put(location, rv);
		}
		return rv;
	}

	/**
	 * The results of a successful load are cached so that future calls with the
	 * same location string will return the cached TransformationCollection
	 * from the previous load.
	 */
	public TransformationCollection loadTransformationFile(String location) throws FileLoaderException {
		TransformationCollection rv;
		if (transformationCache.containsKey(location)) {
			rv = transformationCache.get(location);
		} else {
			rv = performTransformationLoad(location);
			transformationCache.put(location, rv);
		}
		return rv;
	}

	public void setFcsInput(FcsInput in) {
		this.fcsIn = in;		
	}
	
	/**
	 * The results of a successful load are cached so that future calls with the
	 * same location string will return the cached FcsDatFile from the previous load.
	 */
	public FcsDataFile loadFcsFile(String location) throws FileLoaderException {
		FcsDataFile rv;
		if (fcsCache.containsKey(location)) {
			rv = fcsCache.get(location);
		} else {
			rv = performFcsLoad(location);
			fcsCache.put(location, rv);
		}
		return rv;
	}
	
	/**
	 * Performs the actual loading of a Gating-ML file at the given Location.
	 * 
	 * @param location The location of the file as a string.
	 * @return Returns a GateSet that has the Gates that are in the File 
	 * @throws FileLoaderException Thrown if there was an error loading the file.
	 * Use getLinkedException() to get the actual cause.
	 */
	protected abstract GateSet performGatingLoad(String location) throws FileLoaderException;
	
	/**
	 * Performs the actual loading of a Transformation-ML file at the given location.
	 * 
	 * @param location The location of the file as a string.
	 * @return Returns a TransformationCollection that has the Transformations that
	 * are in the File.
	 * @throws FileLoaderException Thrown if there was an error loading the file.
	 * Use getLinkedException() to get the actual cause.
	 */
	protected abstract TransformationCollection performTransformationLoad(String location) throws FileLoaderException;
	
	/**
	 * Performs the actual loading of a Copmensation-ML file at the given Location.
	 * 
	 * @param location The location of the file as a string.
	 * @return Returns the SpilloverMatrixSet that has the SpilloverMatrices
	 * that are in the file.
	 * @throws FileLoaderException Thrown if there was an error loading the file.
	 * Use getLinkedException() to get the actual cause.
	 */
	protected abstract SpilloverMatrixSet performCompensationLoad(String location) throws FileLoaderException;
	
	/**
	 * Performs the actual loading of an FCS file at the given location.
	 * 
	 * @param location The location of the file as a string.
	 * @return Returns the FcsDataFile that has the FcsDataSets that are in the file.
	 * @throws FileLoaderException Thrown if there was an error loading the file.
	 * Use getLinkedException() to get the actual cause.
	 */
	protected abstract FcsDataFile performFcsLoad(String location) throws FileLoaderException;
	
}
