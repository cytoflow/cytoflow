package org.flowcyt.facejava.faceflow.application.outputlayers;

import java.util.Collections;

import org.flowcyt.facejava.fcsdata.AbstractOrderedPopulation;
import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.CircularParameterDependencyException;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.transformation.TransformationCollection;

/**
 * <p>
 * The TransformationLayer decorates its parent layer by adding the Transformations
 * in a TransformationCollection to the paret layer's result population's default
 * retriever. Thus, this layer's result population's retriever will be able to
 * resolve ParameterReferences to the Transformations in the TransformationCollection
 * as well as any Parameters that the parent layer's result population's retriever
 * could reolve. 
 * 
 * @author echng
 */
public class TransformationLayer extends AbstractOutputLayer {

	/**
	 * The new DataRetriever which has the same ParameterCollections as the parent
	 * layer's retriever as well as the TransformationCollection.
	 */
	private DataRetriever updatedRetriever;
	
	/**
	 * The result population which uses the new retriever.
	 */
	private Population resultPop;
	
	/**
	 * Constructor. The new DataRetriever is created to be used in the result
	 * population.
	 * 
	 * @param parent The parent layer. 
	 * @param transColl The TransformationCollection which contains the Transformations
	 * to be added to the DataRetriever.
	 * @throws DuplicateParameterReferenceException Thrown if there is another
	 * Parameter in the parent layer's population's DataRetriever which has the same
	 * ParameterReference as a Transformation in the given TransformationCollection/ 
	 * @throws CircularParameterDependencyException Thrown if a circular dependency
	 * results from using the Transformations in the TransformationCollection.
	 */
	public TransformationLayer(OutputLayer parent, TransformationCollection transColl) throws DuplicateParameterReferenceException, CircularParameterDependencyException {
		super(parent);
		updatedRetriever = new DataRetriever(parent.getResultPopulation().getRetriever(), Collections.singletonList(transColl));
		resultPop = new TransformationPopulation();
	}
	
	/**
	 * Returns a population which has had the TransformationCollection added to
	 * the parent layer's default population.
	 */
	public Population getResultPopulation() {
		return resultPop;
	}
	
	/**
	 * <p>
	 * A private inner class which is the type of Population returned by
	 * getResultPopulation(). It returns the same values as the parent layer's
	 * Population except for getRetriever(), which has the TransformationCollection
	 * includedm, and getStatistics(), so that stats will be calculated for the
	 * new Transformations as well.
	 * 
	 * @author echng
	 */
	private class TransformationPopulation extends AbstractOrderedPopulation {
		public TransformationPopulation() {
			super(getParentLayer().getResultPopulation().getParentPopulation(), getParentLayer().getResultPopulation());
		}

		public DataRetriever getRetriever() {
			return updatedRetriever;
		}
	}

}
