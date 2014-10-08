package org.flowcyt.facejava.fcsdata.impl;

import java.util.AbstractList;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.flowcyt.facejava.fcsdata.ParameterCollection;
import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.fcsdata.exception.InvalidParameterNumberException;

/**
 * <p>
 * A ParameterCollection for the FcsParameters in a FCS data set. The FcsParameters
 * are ordered by their ParameterNumbers. 
 * 
 * <p>
 * This collection is unmodifiable since it represents the Parameters in an actual
 * FCS data set.
 * 
 * @author echng
 */
public class FcsParameterList extends AbstractList<FcsParameter> implements ParameterCollection<FcsParameter> {
	/**
	 * Maps the ParameterReference to its parameter object. Only ParameterReferences that
	 * will have a Parameter returned by getParameter() should be in the map.
	 */
    private Map<ParameterReference, FcsParameter> refToParamMap;
    
    /**
     * Keeps a list of all the FcsParameters (those defined in the FCS file) ordered by
     * their parameter number. Since Parameter Numbers start from 1, the ith parameter
     * will appear at index i-1 in the list.
     */
    private List<FcsParameter> parameterList;

    /**
     * Constructor. Creates an empty list.
     *
     */
    public FcsParameterList() {
    	refToParamMap = new HashMap<ParameterReference, FcsParameter>();
    	parameterList = new ArrayList<FcsParameter>();
    }
    
    /**
     * Constructor. Creates a FcsParameterList with the FcsParameters in the given
     * collection. A sanity check for the Parameter numbers and references is performed
     * and if they do not pass, an exception is thrown. Since an FcsParameterList
     * represents the parameters in an FCS data set, the List must meet those
     * requirements. The Collection will first be sorted by ParameterNumber and it is
     * checked that the first Parameter has a number of 1 and the second Parameter has
     * a number of 2 and so on. Duplicate References will also cause an exception
     * to be thrown.
     *
     * @param coll The Collection whose FcsParameterNumbers.
     * @throws InvalidParameterNumberException Thrown if the parameter number of at least one
	 * of the given parameters is not the expected Parameter number. (i.e., equal to one more
	 * than the list index it's at.) 
	 * @throws DuplicateParameterReferenceException Thrown if there are multiple Parameter that
	 * can be referenced with the same ParameterReference
     */
    public FcsParameterList(Collection<? extends FcsParameter> coll) throws DuplicateParameterReferenceException, InvalidParameterNumberException {
    	this();
    	
    	List<FcsParameter> sorted = new ArrayList<FcsParameter>(coll);
    	Collections.sort(sorted, new Comparator<FcsParameter>() {
			public int compare(FcsParameter o1, FcsParameter o2) {
				return o1.getParameterNumber() - o2.getParameterNumber();
			}
    	});
    	
		int i = 1;
		for (FcsParameter param : sorted) {
			if (param.getParameterNumber() != i)
				throw new InvalidParameterNumberException(this, param.getParameterNumber());
			
			parameterList.add(param);
			
			ParameterReference reference = param.getReference();
			if (refToParamMap.containsKey(reference))
				throw new DuplicateParameterReferenceException(reference);
			else if (!reference.equals(ParameterReference.UNREFERENCABLE))
				refToParamMap.put(reference, param);			
			
			i++;
		}
    }
    
    /**
     * Note this is different from get() since that is indexed starting from zero
     * while this is indexed starting from 1.
     *
     * @param paramNumber The parameter number to get the FcsParameter for.
     * @return Returns the FcsParameter with the given number.
     */
	public FcsParameter getByParameterNumber(int paramNumber) {
		return parameterList.get(paramNumber - 1);
	}

	/**
	 * Gets by list index and not parameter number
	 */
	@Override public FcsParameter get(int index) {
		return parameterList.get(index);
	}

	@Override public int size() {
		return parameterList.size();
	}

	public boolean containsByReference(ParameterReference ref) {
		return refToParamMap.containsKey(ref);
	}

	public FcsParameter get(ParameterReference reference) {
		if (reference.equals(ParameterReference.UNREFERENCABLE))
    		return null;
    	
    	return refToParamMap.get(reference);
	}

	public Set<ParameterReference> getParameterReferences() {
		return Collections.unmodifiableSet(refToParamMap.keySet());
	}	
}
