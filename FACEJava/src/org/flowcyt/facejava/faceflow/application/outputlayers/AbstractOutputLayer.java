package org.flowcyt.facejava.faceflow.application.outputlayers;

/**
 * <p>
 * An Abstract base class for OutputLayers which implements the parent layer
 * functionality. Only getResultPopulation(), needs to be implemented by sub-classes.
 * 
 * @author echng
 */
public abstract class AbstractOutputLayer implements OutputLayer {

	/**
	 * The parent OutputLayer (the one being decorated by this layer).
	 */
	private OutputLayer parent;
	
	/**
	 * The string to append to the base name of the parent.
	 */
	private String appendedName;
	
	/**
	 * Constructor.
	 * @param parent THe OutputLayer that is the parent of the created Layer.
	 * If null, then this layer has no parent.
	 */
	public AbstractOutputLayer(OutputLayer parent) {
		this.parent = parent;
		appendedName = "";
	}
	
	public OutputLayer getParentLayer() {
		return parent;
	}
	
	public String getResultBaseName() {
		return parent == null ? appendedName : parent.getResultBaseName() + appendedName;
	}
	
	/**
	 * For use by sub-classes. Appends the given string to the parent layer's base name.
	 * Repeated calls will append the string one after another and will not replace
	 * them.
	 * 
	 * @param str The string to append to the base name.
	 */
	protected void appendToResultBaseName(String str) {
		this.appendedName += str;		
	}
}
