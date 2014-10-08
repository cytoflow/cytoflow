package org.flowcyt.facejava.gating.analysis;

import org.flowcyt.facejava.gating.gates.Gate;

/**
 * <p>
 * An AnalysisError that only prevent a gate from being used during analysis, rather than
 * preventing a whole DataSet from being analyzed. 
 * 
 * @author echng
 */
public class GateAnalysisError extends AnalysisError {

	/**
	 * The Gate that the error occurred for.
	 */
	private Gate gate;
	
	/**
	 * Constructor.
	 * 
	 * @param gate The gate the error occurred for.
	 * @param cause The cause of the error.
	 */
	public GateAnalysisError(Gate gate, Exception cause) {
		super(cause);
		this.gate = gate;
	}
	
	public String toString() {
		return "Gate \"" + gate.getId() + "\"" + super.toString();
	}
}
