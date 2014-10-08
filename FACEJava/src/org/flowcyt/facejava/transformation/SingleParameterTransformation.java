package org.flowcyt.facejava.transformation;

import java.util.Collections;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.transformation.exception.RootFindingException;

/**
 * <p>
 * An abstract super-class for Transformation which only transforms the data point from
 * a single other Parameter.
 *  
 * @author echng
 */
public abstract class SingleParameterTransformation extends AbstractTransformation {
	/**
	 * The reference to the parameter whose data point it transforms.
	 */
	private ParameterReference parameterRef;
	
	/**
	 * Constructor.
	 * @param name The name of the Transformation.
	 * @param parameterReference A reference to the parameter it transforms. 
	 */
	public SingleParameterTransformation(String name, ParameterReference parameterReference) {
		super(name);
		this.parameterRef = parameterReference;
	}
	
	/**
	 * @return Returns the reference to the parameter to be transformed.
	 */
	public ParameterReference getTransformedParameter() {
		return parameterRef;
	}
	
	public Set<ParameterReference> getDependencies() {
		return Collections.singleton(parameterRef);
	}
	
	public double getScale(Event ev, DataRetriever retriever) throws DataRetrievalException {
		return applyTransformation(retriever.getScale(this.getTransformedParameter(), ev));
	}
	
	/**
	 * Given the ParameterValue, this method will apply the Transformation represented by the
	 * concrete sub-type.
	 * 
	 * @param parameterValue The parameteralue to transform.
	 * @return Returns the transformed value given the parameterValue.
	 * @throws RootFindingException Thrown if there was a problem finding a root for the
	 * transformation.
	 */
	protected abstract double applyTransformation(double parameterValue) throws RootFindingException;
}
