package org.flowcyt.facejava.fcsdata.impl;

import java.util.Collections;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Parameter;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;

/**
 * <p>
 * Represents a single parameter in the FCS Data File.
 * 
 * @author echng
 */
public class FcsParameter implements Parameter {
	/**
	 * The parameter's Number in the data set. Starts from 1.
	 */
	private int parameterNumber;
	
	/**
	 * The identifier this Parameter can be referenced by (its shortname, $PnN).
	 */
	private ParameterReference reference;
	
	/**
	 * Creates a Parameter object with no shortname.
	 * @param parameterNumber The parameter's Number in the data set. Starts from 1.
	 */
	public FcsParameter(int parameterNumber) {
		this(null, parameterNumber);
	}
	
	/**
	 * Creates a Parameter object with the given shortname.
	 * @param shortname The short name ($PnN) of the FCS parameter that the object represents.
	 * If the parameter has no short name specified, use the other constructor.
	 * @param parameterNumber The parameter's Number in the data set. Starts from 1.
	 */
	public FcsParameter(String shortname, int parameterNumber) {
		this.parameterNumber = parameterNumber;
		
		if (shortname != null)
			reference = new ParameterReference(shortname);
		else
			reference = ParameterReference.UNREFERENCABLE;
	}
	
	/**
	 * @return Returns this Parameter's parameter number in the FCS file. Starts from 1.
	 */
	public int getParameterNumber() {
		return this.parameterNumber;
	}
	
	/**
	 * @return Returns the shortname ($PnN) as a ParameterReference. If there is no shortname
	 * ParameterReference.UNREFERENCABLE is returned.
	 */
	public ParameterReference getReference() {
		return reference;
	}
	
	public Set<ParameterReference> getDependencies() {
		return Collections.emptySet();
	}
	
	public double getScale(Event ev, DataRetriever retriever) throws DataRetrievalException {
		return ev.getScale(this.parameterNumber);
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("FCS Parameter Number ");
		builder.append(this.getParameterNumber());
		builder.append(" (");
		builder.append(this.getReference() == null ? "Short Name not set" : this.getReference());
		builder.append(")");
		return builder.toString();
	}
}
