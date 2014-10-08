package org.flowcyt.facejava.faceflow.application.outputlayers;

import org.flowcyt.facejava.fcsdata.Population;

/**
 * <p>
 * OutputLayers are an implementation of the GoF Decorator pattern which represents
 * the (possible) output of the FACEFlow tool as a Population which can be written to
 * the FCS file. Each OutputLayer decorates the layer below by modifying the result
 * Population of the lower layer in some way, but without actually mutating the lower
 * layer in any way (i.e., the lower layer can still be used correctly as a parent
 * to some other layer).
 * 
 * @author echng
 */
public interface OutputLayer {
	
	/**
	 * @return Returns the OutputLayer that this OutputLayer decorates (i.e., 
	 * the layer below this layer). Returns null if the OutputLayer has no parent
	 * (i.e., it doesn't decorate anything).
	 */
	public OutputLayer getParentLayer();
	
	/**
	 * @return Returns the result Population for this OutputLayer.
	 */
	public Population getResultPopulation();
	
	/**
	 * @return Returns the base name for this layer which can be used as the file
	 * name for the new FCS file.
	 */
	public String getResultBaseName();
}
