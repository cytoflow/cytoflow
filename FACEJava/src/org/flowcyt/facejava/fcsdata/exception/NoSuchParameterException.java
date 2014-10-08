package org.flowcyt.facejava.fcsdata.exception;

import org.flowcyt.facejava.fcsdata.ParameterReference;

/**
 * <p>
 * Thrown if no Parameter can be found that has the given ParameterReference when the reference
 * is being resolved.
 * 
 * @author echng
 */
public class NoSuchParameterException extends DataRetrievalException {
	private static final long serialVersionUID = 4815459630904317851L;

	private ParameterReference badParamReference;
	
	public NoSuchParameterException(ParameterReference badParameterReference) {
		super("Can't find parameter referenced by: " + badParameterReference);
		this.badParamReference = badParameterReference;
	}
	
	public ParameterReference getBadParameterReference() {
		return badParamReference;
	}
}
