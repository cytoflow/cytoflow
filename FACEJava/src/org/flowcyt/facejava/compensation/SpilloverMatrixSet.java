package org.flowcyt.facejava.compensation;

import java.util.AbstractSet;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

/**
 * <p>
 * A specialized Set which contains SpilloverMatrices. No two matrices in the set
 * can have the same id (since that's what determines equality). This class also
 * supports lookup, removal and containment checking by matrix id.
 * 
 * <p>
 * Even though this class does perform a mapping from matrix id to the matrix object,
 * it is not truly a Map since it cannot map any type of string to a matrix object.
 * 
 * <p>
 * The Set is modifiable and supports all optional Collection nethods. Null matrices
 * are not allowed in the Set.
 * 
 * @author echng
 */
public class SpilloverMatrixSet extends AbstractSet<SpilloverMatrix> {
	
	/**
	 * Maps the id of the SpilloverMatrix element to its object.
	 */
	private Map<String, SpilloverMatrix> idToMatrixMap;
	
	/**
	 * Constructor. Creates an empty set with no SpilloverMatrices in it.
	 */
	public SpilloverMatrixSet() {
		super();
		idToMatrixMap = new HashMap<String, SpilloverMatrix>();
	}
	
	/**
	 * Constructor. Creates a SpilloverMatrixSet containing the SpilloverMatrices in the
	 * given Collection. Note that for duplicate matrices (i.e., same id), only the
	 * first matrix (as presented by the Collection's iterator) is in the created
	 * object.
	 *   
	 * @param coll The Collection whose matrices will be in the created set.
	 */
	public SpilloverMatrixSet(Collection<? extends SpilloverMatrix> coll) {
		this();
		this.addAll(coll);
	}
	
	/**
	 * @param matrixId The id of the SpilloverMatrix object to return.
	 * @return Returns the SpilloverMatrix with the given id or null if no such Spillovermatrix
	 * exists in the collection.
	 */
	public SpilloverMatrix get(String matrixId) {
		return idToMatrixMap.get(matrixId);
	}
	
	/**
	 * Removes the SpilloverMatrix with the given id from the Set, if present.
	 * 
	 * @param matrixId The id of the SpilloverMatrix to remove.
	 * @return Returns true if the SpilloverMatrix was removed.
	 */
	public boolean removeById(String matrixId) {
		return idToMatrixMap.remove(matrixId) != null; 
	}
	
	/**
	 * Determines if there is a matrix with the given id in the Set.
	 *  
	 * @param matrixId The matrix id to check for.
	 * @return Returns true iff there is a matrix in the Set with the given id.  
	 */
	public boolean containsById(String matrixId) {
		return idToMatrixMap.containsKey(matrixId);
	}
	
	/**
	 * Adds a SpilloverMatrix.
	 * 
	 * @param matrix The matrix to add. Nulls are not allowed to be added
	 * and a NullPointerExcception is thrown. If a matrix with the same id as the
	 * given matrix already exists in the set, the given matrix is not added and
	 * false is returned.
	 * @return Returns true if the matrix was added. 
	 */
	public boolean add(SpilloverMatrix matrix) {
		if (idToMatrixMap.containsKey(matrix.getId()))
			return false;
		
		idToMatrixMap.put(matrix.getId(), matrix);
		return true;
	}
	
	public boolean contains(Object o) {
		return o != null && 
			o instanceof SpilloverMatrix && 
			idToMatrixMap.containsKey(((SpilloverMatrix)o).getId());
	}
	
	public boolean remove(Object o) {
		if (o == null || !(o instanceof SpilloverMatrix))
			return false;
		
		return idToMatrixMap.remove(((SpilloverMatrix)o).getId()) != null;
	}

	@Override public Iterator<SpilloverMatrix> iterator() {
		return idToMatrixMap.values().iterator();
	}

	@Override public int size() {
		return idToMatrixMap.size();
	}
}
