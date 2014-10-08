package org.flowcyt.facejava.faceflow.application.outputlayers;

import org.flowcyt.facejava.compensation.CompensatedDataSet;
import org.flowcyt.facejava.compensation.SpilloverMatrix;
import org.flowcyt.facejava.compensation.exception.InvalidCompensationMatrixException;

/**
 * <p>
 * The CompensationLater decorates its parent layer by applying a compensation to
 * the result population of another layer (the Events of the lower layer are not
 * changed just hidden.) The result population of this layer contains the same
 * Parameters but the Events have been compensated.
 * 
 * <p>
 * Note that since only FcsDataSets can be compensated, CompensationLayers can only
 * have BaseDataSetLayers as parents.
 * 
 * @author echng
 */
public class CompensationLayer extends AbstractOutputLayer {
	
	/**
	 * The result of compensating the FcsDataSet.
	 */
	private CompensatedDataSet result;

	/**
	 * Constructor. The compensation is calculated during construction so large
	 * data sets may take a while.
	 * 
	 * @param parent The parent layer. Must be a BaseDataSetLayer since only
	 * FcsDataSets can be compensated.
	 * @param matrix The SpilloverMatrix that has the spillover values to use
	 * during Compensation.
	 * @throws InvalidCompensationMatrixException Thrown if a valid compensation
	 * matrix could not be computed to use when copmensating Events.
	 */
	public CompensationLayer(BaseDataSetLayer parent, SpilloverMatrix matrix) throws InvalidCompensationMatrixException {
		super(parent);
		result = new CompensatedDataSet(parent.getResultPopulation(), matrix);
		this.appendToResultBaseName("-C" + matrix.getId());
	}

	/**
	 * @return Returns the population with compensated events.
	 */
	public CompensatedDataSet getResultPopulation() {
		return result;
	}

}
