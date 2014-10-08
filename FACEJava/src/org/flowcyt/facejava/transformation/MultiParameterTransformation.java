package org.flowcyt.facejava.transformation;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;

/**
 * <p>
 * An abstract base class for transformations which apply (or can be applied) on more than
 * one other Parameter. 
 * 
 * @author echng
 */
public abstract class MultiParameterTransformation extends AbstractTransformation {

	/**
	 * A set of references to the parameters that are being transformed. 
	 */
	private Set<ParameterReference> parameterReferences;
	
	/**
	 * Constructor.
	 * @param name The name of the transformation
	 * @param parameterReferences A set containing references to the parameters that are a
	 * part of the transformation.  
	 */
	public MultiParameterTransformation(String name, Set<ParameterReference> parameterReferences) {
		super(name);
		this.parameterReferences = parameterReferences;
	}

	public Set<ParameterReference> getDependencies() {
		return parameterReferences;
	}
	
	public double getScale(Event ev, DataRetriever retriever) throws DataRetrievalException {
		Map<ParameterReference, Double> parameterValues = new HashMap<ParameterReference, Double>();
		for (ParameterReference parameterRef : this.parameterReferences) {
			parameterValues.put(parameterRef, retriever.getScale(parameterRef, ev));
		}
		return applyTransformation(parameterValues);
	}
	
	/**
	 * Given data values for each of the dependent parameters, the transformation applies its
	 * transformation using these values.
	 * 
	 * @param parameterValues A map form parameter reference to its data value to be transformed.
	 * @return Returns the result of the transformation applied to the given values.
	 * @throws DataRetrievalException Thrown if there was a problem performing the transformation.
	 */
	protected abstract double applyTransformation(Map<ParameterReference, Double> parameterValues) throws DataRetrievalException;
}
