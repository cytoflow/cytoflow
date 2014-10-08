package org.flowcyt.facejava.transformation;

import java.util.Map;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;

import com.albin.archimedes.DoubleNumber;
import com.albin.archimedes.EvaluationException;
import com.albin.archimedes.MathObject;
import com.albin.archimedes.ParameterContext;

/**
 * <p>
 * Applies an arbitrary transformation to one or more parameters. According to the specification
 * the transformation is specified using MathML 2. We currently use Archimedes MathJ to perform
 * the transformation but its support for MathML is not great (see project README).
 * 
 * @author echng
 */
public class UniversalTransformation extends MultiParameterTransformation {
	
	/**
	 * The MathJ object that will carry out the transformation. 
	 */
	private MathObject transformation;

	/**
	 * Constructor.
	 * @param name THe name of the transformation
	 * @param parameters A set containing the references to the parameters that will be
	 * transformed.
	 * @param transObj The MathJ MathObject that will carry out the transformation
	 */
	public UniversalTransformation(String name, Set<ParameterReference> parameters, MathObject transObj) {
		super(name, parameters);
		transformation = transObj;
	}

	public double applyTransformation(Map<ParameterReference, Double> parameterValues) throws DataRetrievalException {
		ParameterContext context = new ParameterContext();
		for (Map.Entry<ParameterReference, Double> entry : parameterValues.entrySet()) {
			context.setParameter(entry.getKey().getValue(), entry.getValue());
		}
		try {
			return ((DoubleNumber)transformation.getApplication().evaluate(context)).doubleValue();
		} catch (EvaluationException e) {
			throw new DataRetrievalException("MathML Expression could not be evaluated.", e);
		} catch (NullPointerException e) {
			throw new DataRetrievalException("Use of unimplemented MathML element.");
		}
	}
	
	public String toString() {
		return "Universal " + super.toString();
	}
}
