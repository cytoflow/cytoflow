package org.flowcyt.facejava.gating.gates;

import java.util.AbstractSet;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

/**
 * <p>
 * GateSet is a specialized Set which contains Gates. No two Gates in the Set
 * can have the same id (since that's what determines equality). This class also
 * supports lookup, removal and containment checking by Gate id.
 * 
 * <p>
 * Even though this class does perform a mapping from Gate id to the Gate object,
 * it is not truly a Map since it cannot map any string to a Gate object. It only
 * maps ids to Gates with that id.
 * 
 * <p>
 * The Set is modifiable and supports all the optional Collection methods.
 * Null Gates are not allowed in the Set.
 * 
 * @author sli (orignal author), echng (heavily modified)
 */
public class GateSet extends AbstractSet<Gate> {
	/**
	 * Maps the gate's id to the actual gate object. Ids define Gate equality so 
	 * so we know there can not be more than one Gate in this Set with the same id..
	 */
	private Map<String, Gate> idToGateMap;
	
	/**
	 * Constructor. Creates an empty GateSet.
	 */
	public GateSet() {
		this.idToGateMap = new HashMap<String, Gate>();
	}
	
	/**
	 * Constructor. Creates a GateSet containing the Gates in the given Collection.
	 * Note that for duplicate Gates (ones with the same id) only the first one 
	 * (as presented by the Collection's iterator) will be in the created Set.
	 *  
	 * @param coll The Collection whose Gates will be put into the new GateSet.
	 */
	public GateSet(Collection<? extends Gate> coll) {
		this();
		this.addAll(coll);
	}
	
	/**
	 * @param gateId The id of the gate to return
	 * @return Returns the gate with the given id and null if no such gate exists.
	 */
	public Gate get(String gateId){
		return idToGateMap.get(gateId);
	}
	
	/**
	 * Removes the Gate with the given id from the Set, if present.
	 * 
	 * @param gateId The id of the Gate to remove.
	 * @return Returns true if the Gate was removed.
	 */
	public boolean removeById(String gateId) {
		return idToGateMap.remove(gateId) != null; 
	}
	
	/**
	 * Determines if there is a Gate with the given id in the Set.
	 *  
	 * @param gateId The Gate id to check for.
	 * @return Returns true iff there is a Gate in the Set with the given id.  
	 */
	public boolean containsById(String gateId) {
		return idToGateMap.containsKey(gateId);
	}
	
	/**
	 * Nulls are not allowed to be added and a NullPointerException is thrown. 
	 * If a Gate with the same id as the given Gate already exists in the set,
	 * the given Gate is not added and false is returned. 
	 */
	public boolean add(Gate gate) {
		if (idToGateMap.containsKey(gate.getId()))
			return false;
		
		idToGateMap.put(gate.getId(), gate);
		return true;
	}
	
	public boolean contains(Object o) {
		return o != null && 
			o instanceof Gate && 
			idToGateMap.containsKey(((Gate)o).getId());
	}
	
	public boolean remove(Object o) {
		if (o == null || !(o instanceof Gate))
			return false;
		
		return idToGateMap.remove(((Gate)o).getId()) != null;
	}
	
	@Override public Iterator<Gate> iterator() {
		return idToGateMap.values().iterator();
	}

	@Override public int size() {
		return idToGateMap.size();
	}	
}
