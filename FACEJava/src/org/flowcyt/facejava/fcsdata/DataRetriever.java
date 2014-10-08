package org.flowcyt.facejava.fcsdata;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Stack;

import org.flowcyt.facejava.fcsdata.exception.CircularParameterDependencyException;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.fcsdata.exception.NoSuchParameterException;

/**
 * <p>
 * This class contains two important abstractions which is used just about everywhere.
 * It abstracts away the details needed to deal with multiple ParameterCollections by
 * being able to resolve a ParameterReference against all of them. It also abstracts
 * out the detail needed to retrieve data values from an Event for Parameters. It makes
 * sure the data is retrievable for a given Parameter and knows how to use the Parameter
 * to perform the retrieval.
 * 
 * <p>
 * DataRetriever should be the only way clients get the data to use during analysis.
 * It know how to deal with Parameters.
 *  
 * <p>
 * Before any retrieval can be done, the DataRetriever must be given the 
 * ParameterCollections to use when resolving all Parameter references. It will only
 * search through the collections it is given. There can be no duplicate ParameterReferences 
 * across all the given ParameterCollections (that is, no two Parameters can have the 
 * same ParameterReference in the sets returned by Parameter.getParameterReferences()) --
 * otherwise, it could be ambiguous as to which Parameter a ParameterReference is referring to.
 * 
 * <p>
 * DataRetrievers are immutable in the sense that no ParameterCollections can be added after
 * construction.
 * 
 * @author echng
 */
public class DataRetriever {
	
	/**
	 * A list of all the ParameterCollections it should search when resolving references.
	 */
	private List<ParameterCollection<?>> parameterCollections;
	
	/**
	 * We'll cache Parameters that we've resolved so we don't have to search again.
	 * getDataPoint() will be called for each Parameter in each Gate for each Event.
	 * So we might as well reduce the resolving to a map lookup, since there are
	 * relatively few Parameters and each Parameter will need to be found many many
	 * times.
	 */
	private Map<ParameterReference, Parameter> parameterCache;
	
	/**
	 * A cache for all the parameters in the given ParameterCollections.
	 */
	private List<Parameter> allParameters;
	
	/**
	 * Constructor. Creates a DataRetriever that uses the given ParameterCollections to resolve
	 * any references. If the list is empty then no references can be resolved.
	 * 
	 * @param parameterCollections A list containing all the parameter collections to
	 * use when resolving references. Must not be null.
	 * @throws DuplicateParameterReferenceException Thrown if there are any duplicate
	 * ParameterReferences amongst the given ParameterCollections. i.e., There exists two sets
	 * of ParameterReferences returned by ParameterCollection.getParameterReferences() for
	 * two, different, given ParameterCollections where there interesection is not empty. 
	 * @throws CircularParameterDependencyException Thrown if any Parameter is 
	 * (even indirectly) dependent on itself.
	 */
	public DataRetriever(List<? extends ParameterCollection<?>> parameterCollections) throws DuplicateParameterReferenceException, CircularParameterDependencyException {
		this(null, parameterCollections);
	}
	
	/**
	 * <p>
	 * Constructor. Creates a DataRetriever that uses the ParameterCollections used by the
	 * given original DataRetriever and in the given list to resolve any references.
	 * 
	 * <p>
	 * See getAllParameters() for how the order of the DataRetriever and ParameterCollections 
	 * affects the Parameter order in getAllParameters().
	 * 
	 * @param original The ParameterCollections used by original will also be used by the
	 * new DataRetriever. Can be null. If so, only the ParameterCollections in the list are
	 * used.
	 * @param additionalParameterCollections A list containing all the parameter collections to
	 * use when resolving references in addition to any in the given original DataRetriever.
	 * Must not be null.
	 * @throws DuplicateParameterReferenceException Thrown if there are any duplicate
	 * ParameterReferences amongst the given ParameterCollections. i.e., There exists two sets
	 * of ParameterReferences returned by ParameterCollection.getParameterReferences() for
	 * two, different, given ParameterCollections where there interesection is not empty. 
	 * @throws CircularParameterDependencyException Thrown if any Parameter is 
	 * (even indirectly) dependent on itself.
	 */
	public DataRetriever(DataRetriever original, List<? extends ParameterCollection<?>> additionalParameterCollections) throws DuplicateParameterReferenceException, CircularParameterDependencyException {
		this.parameterCollections = new ArrayList<ParameterCollection<?>>();
		if (original != null)
			this.parameterCollections.addAll(original.parameterCollections);
		this.parameterCollections.addAll(additionalParameterCollections);
		
		this.allParameters = new ArrayList<Parameter>();
		for (ParameterCollection<?> paramColl : parameterCollections) {
			allParameters.addAll(paramColl);
		}
		
		this.parameterCache = new HashMap<ParameterReference, Parameter>(allParameters.size());
		
		Set<ParameterReference> duplicates = duplicateNameCheck();
		if (duplicates.size() > 0)
			throw new DuplicateParameterReferenceException(duplicates);
		
		dependencyCycleCheck();
	}	
	
	/**
	 * @return Returns a List containing all the parameters used to retrieve data points
	 * by this retriever (i.e., all the Parameters in all the ParameterCollections). Since some
	 * ParameterCollections might have order while some might not, a list is returned so that
	 * the order is maintained where it matters. The order in the list is determined by appending
	 * the following to an empty list (in the order returned by the methods):
	 * 
	 * <ol>
	 * <li>original.getAllParameters(), where original is the DataRetriever given during
	 *    construction (if it is not null).
	 * <li>collection.getParameters(), where collection is each of the ParameterCollections in
	 *    the list given during Construction and in the order given in the list.
	 * </ol> 
	 */
	public List<Parameter> getAllParameters() {
		return allParameters;		
	}
	
	/**
	 * Checks for any duplicate references amongst all the Parameters in the Parameter Collection.
	 * Note that NO duplicate references are allowed, including numbers.
	 * 
	 * @return Returns a Set containing all the duplicate references in the
	 * ParameterCollection list.
	 */
	private Set<ParameterReference> duplicateNameCheck() {
		// To perform the check AND get which names are duplicates. We do the following:
		//
		// Let Ai be the set containing the parameter names in the ith
		// ParameterCollection for i = 0, ..., n-1, where there are n collections in
		// the list. Then, for j = 1, ..., n-1, Let 
		// Dj = (A0 U ... U Aj-1) {intersection} Aj. Thus, the set of duplicate names
		// is D = D1 U ... U Dn-1. 
		Set<ParameterReference> duplicates = new HashSet<ParameterReference>();
		for (int numBaseSets = 1; numBaseSets < parameterCollections.size(); ++numBaseSets) {
			Set<ParameterReference> allInBaseSets = new HashSet<ParameterReference>();
			for (int i = 0; i < numBaseSets; ++i)  {
				allInBaseSets.addAll(parameterCollections.get(i).getParameterReferences());				
			}
			
			allInBaseSets.retainAll(parameterCollections.get(numBaseSets).getParameterReferences());
			duplicates.addAll(allInBaseSets);
		}
		
		return duplicates;				
	}
	
	/**
	 * Determines if any of the Parameters in all the ParameterCollections have a circular
	 * dependency. That is, they depend on themselves. This method will throw an 
	 * exception if one is found. If all Parameters are OK, the method returns normally.
	 * 
	 * @throws CircularParameterDependencyException Thrown if a Parameter is found to 
	 * depend on itself.
	 */
	private void dependencyCycleCheck() throws CircularParameterDependencyException {
		// First build a set containing all the Parameters in the collections.
		Set<Parameter> parametersToCheck = new HashSet<Parameter>(this.getAllParameters());
		
		// Keep going until all Parameters are tested.
		while (!parametersToCheck.isEmpty()) {
			Stack<Parameter> cyclePath = new Stack<Parameter>();
			Parameter startParam = parametersToCheck.iterator().next();
			if (dependencyCycleCheckHelper(startParam, cyclePath, parametersToCheck)) {
				// Extract the cycle to give to the exception.
				Parameter cycleParam = cyclePath.peek();
				int firstOccurrence = cyclePath.indexOf(cycleParam);
				int lastOccurrence = cyclePath.lastIndexOf(cycleParam);
				throw new CircularParameterDependencyException(cyclePath.subList(firstOccurrence, lastOccurrence + 1));
			}
		}
	}
	
	/**
	 * Starting at currentParam, it recursively performs a DFS looking for a cycle. The
	 * graph that is searched is a directed graph where a node exists for each parameter
	 * and an edge [p,q] exists if Parameter p depends on the Parameter q to retrieve its
	 * data points.
	 * 
	 * @param currentParam The current Parameter that is being checked. It is the
	 * last node on the current path being followed.
	 * @param pathToCurrentParam The path leading up (but not including) currentParam.
	 * @param parametersToCheck A set containing parameters that haven't been tested yet.
	 * Any Parameter not in this set has already been found not to be involved in a
	 * cycle. Parameters should be removed from this set when they don't have cycles.
	 * @return Returns true if a Parameter is found to have a circular dependency.
	 * pathToCurrentParam will contain the cycle at the top of the stack (That is,
	 * the top Parameter will occur somewhere else in the Stack and the elements in
	 * between the two occurence form the dependency cycle.) 
	 */
	private boolean dependencyCycleCheckHelper(Parameter currentParam, Stack<Parameter> pathToCurrentParam, Set<Parameter> parametersToCheck) {
		if (pathToCurrentParam.contains(currentParam)) {
			pathToCurrentParam.push(currentParam);
			return true;
		}
		
		if (currentParam.getDependencies().size() > 0) {
			pathToCurrentParam.push(currentParam);
			
			for (ParameterReference dependencyReference : currentParam.getDependencies()) {
				try {
					Parameter dependency = resolveReference(dependencyReference);
					// We only need to follow this dependency if we haven't already 
					// found it to not have a cycle.
					if (parametersToCheck.contains(dependency) && 
							dependencyCycleCheckHelper(dependency, pathToCurrentParam, parametersToCheck))
						return true;
				} catch (NoSuchParameterException e) {
					// We'll hide the exception here since there may (will probably) be
					// some Gates that don't use the bad reference and thus Analysis for
					// them would be OK.				
				}
			}
			
			pathToCurrentParam.pop();
		}
		
		// We've finished checking currentParam and we know it has no cycle.
		parametersToCheck.remove(currentParam);
		
		return false;
	}
	
	/**
	 * <p>
	 * Returns the Parameter for the given reference. 
	 * 
	 * <p>
	 * Parameter references are resolved by finding the first ParameterCollection that has a 
	 * Parameter that can be referenced by the given Reference. 
	 *
	 * <p>
	 * If no ParameterCollection contains a Parameter for the given reference, a
	 * NoSuchParameterException is thrown.
	 * 
	 * @param parameterReference The ParameterReference to be resolved.
	 * @return Returns the parameter for the given reference.
	 * @throws NoSuchParameterException Thrown if there is no Parameter in the given
	 * ParameterCollections that has the given reference. 
	 */
	public Parameter resolveReference(ParameterReference parameterReference) throws NoSuchParameterException {
		Parameter referencedParam = null;
		
		referencedParam = parameterCache.get(parameterReference);
		if (referencedParam != null)
			return referencedParam;
		
		for (ParameterCollection<?> paramColl : parameterCollections) {
			referencedParam = paramColl.get(parameterReference);
			
			if (referencedParam != null)
				break;
		}
		
		if (referencedParam == null)
			throw new NoSuchParameterException(parameterReference);
		
		parameterCache.put(parameterReference, referencedParam);
		
		return referencedParam;
	}
	
	/**
	 * @param parameterReference The ParameterReference to the Parameter to get the scale value
	 * for. This is a convenience method for calling resolveReference() then getScale with the
	 * returned Parameter.
	 * @param ev The event to get the scale data from
	 * @return Returns the scale value from the given event for the referenced parameter. 
	 * @throws NoSuchParameterException Thrown if there is no Parameter in the given
	 * ParameterCollections that has the given reference. 
	 * @throws DataRetrievalException  Thrown if there was an error retrieving the
	 * data point. Check the exception's concrete type to see the specific cause.
	 */
	public double getScale(ParameterReference parameterReference, Event ev) throws NoSuchParameterException, DataRetrievalException {
		Parameter referencedParam = resolveReference(parameterReference);
		return this.getScale(referencedParam, ev);
	}
	
	/**
	 * @param param The Parameter to get the data for.
	 * @param ev The Event to get the data from.
	 * @return Returns the channel data from the given event for the given parameter.
	 * @throws DataRetrievalException Thrown if there was an error retrieving the
	 * data point. Check the exception's concrete type to see the specific cause.
	 */
	public double getScale(Parameter param, Event ev) throws DataRetrievalException {
		return param.getScale(ev, this);
	}
}
