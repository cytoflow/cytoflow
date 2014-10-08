package org.flowcyt.facejava.compensation.xmlio;

import org.flowcyt.facejava.compensation.SpilloverMatrix;
import org.flowcyt.facejava.compensation.jaxb.Coefficient;
import org.flowcyt.facejava.compensation.jaxb.Spillover;
import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * A factory class to create SpilloverMatrices from their JAXB representation.
 * 
 * @author echng
 */
public class SpilloverMatrixFactory {
	
	/**
	 * @param jaxbMatrix The JAXB object containing the data in the spilloverMatrix element.
	 * @return A SpilloverMatrix containing the spillover values in the given JAXB version of
	 * the matrix.
	 */
	public static SpilloverMatrix createMatrix(org.flowcyt.facejava.compensation.jaxb.SpilloverMatrix jaxbMatrix) {
		SpilloverMatrix rv = new SpilloverMatrix(jaxbMatrix.getId());
		
		for (Spillover spill : jaxbMatrix.getSpillover()) {
			ParameterReference spillRef = new ParameterReference(spill.getParameter());
			for (Coefficient coeff : spill.getCoefficient()) {
				rv.setSpilloverValue(spillRef, new ParameterReference(coeff.getParameter()), coeff.getValue());
			}
		}
		
		return rv;
	}
}
