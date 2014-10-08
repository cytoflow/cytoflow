package org.flowcyt.facejava.faceflow.application.outputlayers;

import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSubPopulation;

/**
 * <p>
 * The GateLayer decorates the parent layer by applying a Gate to the parent's result
 * population.
 * 
 * @author echng
 */
public class GateLayer extends AbstractOutputLayer {

	/**
	 * The gated population.
	 */
	private GateSubPopulation gateSubPop;
	
	/**
	 * Constructor. The gating operation is performed during Construction.
	 * 
	 * @param parent The parent layer whose result popuylation will be gated.
	 * @param gate The Gate to use to gate on the parent layer.
	 * @throws DataRetrievalException Thrown if there was a problem retrieveing
	 * data from Events when applying the gate.
	 */
	public GateLayer(OutputLayer parent, Gate gate) throws DataRetrievalException {
		super(parent);
		this.gateSubPop = gate.isInside(parent.getResultPopulation());
		this.appendToResultBaseName("-G" + gate.getId());
	}

	/**
	 * @return Returns a popoulation that is the result of applying the Gate to the
	 * parent layer's result population
	 */
	public GateSubPopulation getResultPopulation() {
		return gateSubPop;
	}

}
