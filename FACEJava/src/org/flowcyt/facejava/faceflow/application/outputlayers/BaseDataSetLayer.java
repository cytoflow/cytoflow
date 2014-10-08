package org.flowcyt.facejava.faceflow.application.outputlayers;

import java.io.File;

import org.flowcyt.facejava.faceflow.application.FACEFlow;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;

/**
 * <p>
 * This is the normal base layer, one that should be created for each data set read in from
 * a data file. The result population is the FcsDataSet itself (with no changes). It
 * has no parent layer.
 * 
 * @author echng
 */
public class BaseDataSetLayer extends AbstractOutputLayer {

	/**
	 * The base data set contained by the layer.
	 */
	private FcsDataSet dataSet;
	
	/**
	 * Constructor.
	 * 
	 * @param ds The data set to use as the base,
	 * @param location
	 */
	public BaseDataSetLayer(FcsDataSet ds, String location) {
		super(null);
		this.dataSet = ds;
		this.appendToResultBaseName(makeBaseName(location) + "-DS" + ds.getDataSetNumber());
	}
	
	/**
	 * Given a path to the data file containing the , (naively) derives a suitable
	 * base name. Any .fcs suffix (case-insensitive) is stripped and the portion
	 * of the path before (and including) the last '/' or if there is no '/', 
	 * the system-dependent path separator is also stripped. The portion of the path
	 * left is returned. 
	 * 
	 * @param location The path to use to get a base name.
	 * @return Returns the base name as obtained above. 
	 */
	private String makeBaseName(String location) {
		// XXX: There's probably a better, portable way to do this.
		String path = location;
		
		// In case it's a URI (or Unix-style path)
		int lastSlashPos = path.lastIndexOf('/');
		
		// Fall back to assuming it's a file system path
		if (lastSlashPos == -1) {
			lastSlashPos = path.lastIndexOf(File.separatorChar);
		}
		boolean hasFcsSuffix = path.toUpperCase().endsWith(FACEFlow.FCS_EXTENSION.toUpperCase());
		
		String baseName = path;
		if (hasFcsSuffix)
			baseName = path.substring(lastSlashPos+1, path.length() - FACEFlow.FCS_EXTENSION.length());
		else
			baseName = path.substring(lastSlashPos+1);
		return baseName;
	}
	
	/**
	 * @return Returns the FcsDataSet.
	 */
	public FcsDataSet getResultPopulation() {
		return dataSet;
	}
	
}
