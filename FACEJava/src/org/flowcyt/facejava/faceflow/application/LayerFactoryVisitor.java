package org.flowcyt.facejava.faceflow.application;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;


import org.flowcyt.facejava.compensation.SpilloverMatrix;
import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.compensation.exception.InvalidCompensationMatrixException;
import org.flowcyt.facejava.faceflow.application.outputlayers.BaseDataSetLayer;
import org.flowcyt.facejava.faceflow.application.outputlayers.CompensationLayer;
import org.flowcyt.facejava.faceflow.application.outputlayers.GateLayer;
import org.flowcyt.facejava.faceflow.application.outputlayers.OutputLayer;
import org.flowcyt.facejava.faceflow.application.outputlayers.TransformationLayer;
import org.flowcyt.facejava.faceflow.exception.FileLoaderException;
import org.flowcyt.facejava.faceflow.loader.FileLoader;
import org.flowcyt.facejava.faceflow.relations.CompensationRelation;
import org.flowcyt.facejava.faceflow.relations.DataSetRelations;
import org.flowcyt.facejava.faceflow.relations.DataSetRelationsVisitor;
import org.flowcyt.facejava.faceflow.relations.ExperimentDescriptionRelation;
import org.flowcyt.facejava.faceflow.relations.GatingRelation;
import org.flowcyt.facejava.faceflow.relations.InstrumentationRelation;
import org.flowcyt.facejava.faceflow.relations.Relation;
import org.flowcyt.facejava.faceflow.relations.RelationOrder;
import org.flowcyt.facejava.faceflow.relations.TransformationRelation;
import org.flowcyt.facejava.faceflow.relations.UnknownRelation;
import org.flowcyt.facejava.faceflow.relations.VisitMethod;
import org.flowcyt.facejava.fcsdata.exception.CircularParameterDependencyException;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.transformation.TransformationCollection;

/**
 * <p>
 * LayerFactoryVisitor is a DataSetRelationsVisitor which creates and saves the
 * the OutputLayers which correspond to the visited Relation for a given
 * DataSetRelations. The OutputLayers are created with the data set layer being
 * the base, while a compensation layer decorates that, which is decorated by a 
 * transformation layer, which is decorated by a gating layer for each of the gates
 * in the gating file. If any of the Relations don't exist for the DataSetRelations,
 * the corresponding layer is omitted.
 * 
 * <p>
 * In addition to GatingRelation, CompensationRelation and TransformationRelation
 * it can also visit ExperimentDescriptionRelation, InstrumenatationRelation and
 * UnknownRelation (for which it prints out the Relation information but performs
 * no other operation).
 * 
 * <p>
 * Upon an error preventing a layer from being created (a bad file or an Exception
 * when applying the layer (e.g., a non-invertible compensation matrix)), the rest of
 * the Relations for the data set are skipped and the OutputLayers for the data set
 * are not added to the List returned by getFinalLayers(). An exception to the rule
 * is that for an error when applying a Gate in a GatingLayer, only the layer for
 * that gate is not added to the final layer List.  
 * 
 * <p>
 * It's defaultVisit() is also overrided to print out the type of the Relation
 * for which it doesn't know about.
 * 
 * At each visit() call, the list of OutputLayers for the current DataSetRelations
 * is returned.
 * 
 * @author echng
 */
public class LayerFactoryVisitor extends DataSetRelationsVisitor {

	/**
	 * The following are names of the relations to use during logging.
	 */
	private static final String TRANSFORMATION_RELATION_NAME = "Transformation-ML";

	private static final String COMPENSATION_RELATION_NAME = "Compensation-ML";

	private static final String GATING_RELATION_NAME = "Gating-ML";

	private static final String INSTRUMENTATION_RELATION_NAME = "Instrumentation";

	private static final String EXPERIMENT_RELATION_NAME = "Experiment Description";

	private static final String UNKNOWN_RELATION_NAME = "Unknown";

	/**
	 * The RelationOrder in which the visitor needs to visit Relations.
	 */
	private static RelationOrder relOrder;
	
	/**
	 * A list containing the final OutputLayers which have been created by the 
	 * visitor for the DataSetRelations it has visited.
	 */
	private List<OutputLayer> resultLayers;
	
	/**
	 * A list containing the current layers being worked upon as the Relations in a
	 * single DataSetRelations are being visited. We do a lot of enqueueing and
	 * dequeueing without any need for random access so we'll use a LinkedList. 
	 */
	private LinkedList<OutputLayer> currentLayers;
	
	/**
	 * We'll cache the locations for gating/compensation/transformation files for
	 * which we've had errors when loading them. So that in case they are related
	 * to another data set, we won't bother trying to load them again.
	 * 
	 * We need separate caches because e.g., what's invalid as a Compensation file may
	 * be valid as a Gating file.
	 */
	
	private Set<String> gatingFileErrors;
	
	private Set<String> transformationFileErrors;
	
	private Set<String> compensationFileErrors;
	
	/**
	 * A flag to indicate if an error has been found while processing the Relations
	 * in the current DataSetRelations. When this is true, Relation processing is
	 * halted for until startVisit() is called for the next DataSetRelations.
	 */
	private boolean errorFound;
	
	/**
	 * The Logger to use the log the events that happen as Relations are processed.
	 */
	private Logger logger;
	
	/**
	 * The FileLoader to use to load the Relations. The type of locations strings
	 * the loader supports must be the same as the RelationsRepository holds.s
	 */
	private FileLoader loader;
	
	static {
		List<Class<? extends Relation>> orderList = new ArrayList<Class<? extends Relation>>();
		orderList.add(CompensationRelation.class);
		orderList.add(TransformationRelation.class);
		orderList.add(GatingRelation.class);
		// The rest we don't care about as long as they come at the end (which is
		// what happens if we don't specify them).
		
		relOrder = new RelationOrder(orderList);
	}
	
	/**
	 * Constructor.
	 *  
	 * @param logger The logger to use.
	 * @param loader The FileLoader to use.
	 */
	public LayerFactoryVisitor(Logger logger, FileLoader loader) {
		this.resultLayers = new ArrayList<OutputLayer>();
		this.currentLayers = new LinkedList<OutputLayer>();
		
		gatingFileErrors = new HashSet<String>();
		transformationFileErrors = new HashSet<String>();
		compensationFileErrors = new HashSet<String>();

		errorFound = false;
		
		this.logger = logger;
		this.loader = loader;
	}
	
	/**
	 * @return Our visit order assures that CompensationLayers will only be created on top
	 * of a BaseDataSetLayer.
	 */
	public RelationOrder getVisitOrder() {
		return relOrder;
	}

	/**
	 * @return Returns the current list of OutputLayers for the current DataSetRelations being
	 * processed. 
	 */
	public List<OutputLayer> startVisit(DataSetRelations relations) {
		// reset our state variables for the new DataSetRelations
		currentLayers.clear();
		errorFound = false;
		
		logger.logDataSetStart(relations);
		
		// Set-up the first later
		OutputLayer baseLayer = new BaseDataSetLayer(relations.getDataSet(), relations.getDataFileLocation());
		currentLayers.add(baseLayer);
		
		return getFinalLayers();
	}
	
	/**
	 * @return Returns the current list of OutputLayers for the current DataSetRelations being
	 * processed.
	 */
	public List<OutputLayer> endVisit(DataSetRelations relations) {
		if (!errorFound)
			resultLayers.addAll(currentLayers);
		
		logger.logDataSetEnd(relations, !errorFound);
		return getFinalLayers();
	}
	
	/**
	 * Creates a CompensationLayer to decorate the data setlayer for the
	 * CompensationRelation.
	 *  
	 * @param rel The CompensationRelation to be visited.
	 * @return Returns the current list of OutputLayers for the current DataSetRelations being
	 * processed.
	 */
	@VisitMethod
	public List<OutputLayer> visit(CompensationRelation rel) {
		if (errorFound)
			return getFinalLayers();
		
		String location = rel.getLocation();
		
		if (compensationFileErrors.contains(location)) {
			errorFound = true;
			logger.logPreviousRelationError(COMPENSATION_RELATION_NAME, location);
			return getFinalLayers();
		}
		
		logger.logLoadedRelation(COMPENSATION_RELATION_NAME, location);
		
		SpilloverMatrixSet matrixColl;
		try {
			matrixColl = loader.loadCompensationFile(location);
		} catch (FileLoaderException e) {
			compensationFileErrors.add(location);
			errorFound = true;
			logger.logRelationError(e);
			return getFinalLayers();
		}
	
		if (rel.getMatrixId() == null) {
			errorFound = true;
			logger.logNoMatrixError();
			return getFinalLayers();
		}
		
		SpilloverMatrix matrix = matrixColl.get(rel.getMatrixId());
		if (matrix == null) {
			errorFound = true;
			logger.logCompensationError(rel.getMatrixId());
			return getFinalLayers();
		}		
		
		// We want the size before we start to make sure we get all of them since we add to
		// the list during the operation.
		int numLayers = currentLayers.size();
		for (int i = 0; i < numLayers; ++i) {
			OutputLayer oldLayer = currentLayers.removeFirst();
			try {
				OutputLayer newLayer = new CompensationLayer((BaseDataSetLayer)oldLayer, matrix);
				currentLayers.add(newLayer);
			} catch (InvalidCompensationMatrixException e) {
				// Not a file error since the SpilloverMatrix might be valid for
				// another data set. So we don't save the location as one to be skipped
				errorFound = true;
				logger.logRelationError(e);
				return getFinalLayers();
			}			
		}
		return getFinalLayers();
	}

	/**
	 * Creates a GatingLayer for each Gate to decorate each of the current Layers
	 * (i.e, like a cross product).
	 *  
	 * @param rel The GatingRelation to be visited.
	 * @return Returns the current list of OutputLayers for the current DataSetRelations being
	 * processed.
	 */
	@VisitMethod
	public List<OutputLayer> visit(GatingRelation rel) {
		if (errorFound)
			return getFinalLayers();
		
		String location = rel.getLocation();
		
		if (gatingFileErrors.contains(location)) {
			errorFound = true;
			logger.logPreviousRelationError(GATING_RELATION_NAME, location);
			return getFinalLayers();
		}
		
		logger.logLoadedRelation(GATING_RELATION_NAME, location);
		
		GateSet loadedGateSet;
		try {
			loadedGateSet = loader.loadGatingFile(location);
		} catch (FileLoaderException e) {
			gatingFileErrors.add(location);
			errorFound = true;
			logger.logRelationError(e);
			return getFinalLayers();
		}
		
		Collection<Gate> gateColl = new HashSet<Gate>();
		if (rel.getGateId() != null) {
			Gate gate = loadedGateSet.get(rel.getGateId());
			if (gate == null) {
				errorFound = true;
				logger.logNoGateError(rel.getGateId());
				return getFinalLayers();
			}
			gateColl.add(gate);
		} else {
			gateColl = loadedGateSet;
		}
		
		// We want the size before we start to make sure we get all of them since we add to
		// the list during the operation.
		int numLayers = currentLayers.size();
		for (int i = 0; i < numLayers; ++i) {
			OutputLayer oldLayer = currentLayers.removeFirst();
			for (Gate gate : gateColl) {
				try {
					OutputLayer newLayer = new GateLayer(oldLayer, gate);
					currentLayers.add(newLayer);
				} catch (DataRetrievalException e) {
					// Don't need to skip data set. We'll skip only this gate so just
					// continue in the loop.				
					logger.logGateError(gate, e);
				}
			}
		}
		return getFinalLayers();
	}

	/**
	 * Creates a TransformationLayer to decorate the current Layers in the visitor.
	 *  
	 * @param rel The TransformationRelation to be visited.
	 * @return Returns the current list of OutputLayers for the current DataSetRelations being
	 * processed.
	 */
	@VisitMethod
	public List<OutputLayer> visit(TransformationRelation rel) {
		if (errorFound)
			return getFinalLayers();
		
		String location = rel.getLocation();
		
		if (transformationFileErrors.contains(location)) {
			errorFound = true;
			logger.logPreviousRelationError(TRANSFORMATION_RELATION_NAME, location);
			return getFinalLayers();
		}
		
		logger.logLoadedRelation(TRANSFORMATION_RELATION_NAME, location);
		
		TransformationCollection transColl;
		try {
			transColl = loader.loadTransformationFile(location);
		} catch (Exception e) {
			transformationFileErrors.add(location);
			errorFound = true;
			logger.logRelationError(e);
			return getFinalLayers();
		}
		
		// We want the size before we start to make sure we get all of them since we add to
		// the list during the operation.
		int numLayers = currentLayers.size();
		for (int i = 0; i < numLayers; ++i) {
			OutputLayer oldLayer = currentLayers.removeFirst();
			try {
				OutputLayer newLayer = new TransformationLayer(oldLayer, transColl);
				currentLayers.add(newLayer);
			} catch (DuplicateParameterReferenceException e) {
				// Not a file error as it could be valid with another data set. So
				// don't save it as a location to be skipped.
				errorFound = true;
				logger.logRelationError(e);
				return getFinalLayers();
			} catch (CircularParameterDependencyException e) {
				// Not a file error as it could be valid with another data set. So
				// don't save it as a location to be skipped.
				errorFound = true;
				logger.logRelationError(e);
				return getFinalLayers();
			}			
		}
		return getFinalLayers();
	}
	
	/**
	 * Visits a ExperimentDescriptionRelation. Prints out the information but performs
	 * no other operation.
	 * 
	 * @param rel The ExperimentDescriptionRelation.
	 * @return Returns the current list of OutputLayers for the current
	 * DataSetRelations being processed.
	 */
	@VisitMethod
	public List<OutputLayer> visit(ExperimentDescriptionRelation rel) {
		logger.logIgnoredRelation(EXPERIMENT_RELATION_NAME, rel.getLocation());
		return getFinalLayers();
	}

	/**
	 * Visits a InstrumentationRelation. Prints out the information but performs
	 * no other operation.
	 * 
	 * @param rel The InstrumenatationRelation.
	 * @return Returns the current list of OutputLayers for the current
	 * DataSetRelations being processed.
	 */
	@VisitMethod
	public List<OutputLayer> visit(InstrumentationRelation rel) {
		logger.logIgnoredRelation(INSTRUMENTATION_RELATION_NAME, rel.getLocation());
		return getFinalLayers();
	}

	/**
	 * Visits a UnknownRelation. Prints out the information but performs
	 * no other operation.
	 * 
	 * @param rel The UnknownRelation.
	 * @return Returns the current list of OutputLayers for the current
	 * DataSetRelations being processed.
	 */
	@VisitMethod
	public List<OutputLayer> visit(UnknownRelation rel) {
		logger.logIgnoredRelation(UNKNOWN_RELATION_NAME, rel.getIdentifier() + " : " + rel.getValue());
		return getFinalLayers();
	}
	
	/**
	 * @return Returns the current list of OutputLayers for the current DataSetRelations being processed.
	 */
	public List<OutputLayer> defaultVisit(Relation rel) {
		logger.logDefaultRelation(rel.getClass().getSimpleName());
		return getFinalLayers();
	}
	
	public List<OutputLayer> getFinalLayers() {
		return Collections.unmodifiableList(resultLayers);
	}
}
