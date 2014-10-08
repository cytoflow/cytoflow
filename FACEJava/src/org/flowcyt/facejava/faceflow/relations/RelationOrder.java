package org.flowcyt.facejava.faceflow.relations;

import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;


/**
 * <p>
 * RelationOrders are used as a way for DataSetRelationsVisitors to specify the order in which they
 * should visit Relations (because in some cases it may matter) based on their type. The RelationOrder
 * is meant to be used as a Comparator when sorting Lists of Relations.
 * 
 * @author echng
 */
public class RelationOrder implements Comparator<Relation> {
	/**
	 * Instead of searching through a list (twice) for each comparison use a lookup. 
	 */
	private Map<Class<? extends Relation>, Integer> desiredOrderMap;
	
	/**
	 * Constructor. Creates a RelationOrder which will order Relations by their type according to the
	 * given List.
	 * 
	 * @param desiredOrder The desired order of Relations by their type. Any type not included will
	 * default to be last in the order. No order is defined between relations whose types are not in the
	 * list, i.e., they are equal and will appear in one big unordered chunk at the end.
	 */
	public RelationOrder(List<Class<? extends Relation>> desiredOrder) {
		this.desiredOrderMap = new HashMap<Class<? extends Relation>, Integer>();
		int i = 0;
		for (Class<? extends Relation> c : desiredOrder) {
			this.desiredOrderMap.put(c, i++);
		}
	}
	
	/**
	 * <p>
	 * Compared based on the type of the Relation as given in the Constructor.
	 * 
	 * <p>
	 * Relations X is
	 * <ul> 
	 * <li>equal to Relation Y if
	 *     <ul>
	 *     <li>X has the same type as Y <b>OR</b></li>
	 *     <li>both X and Y have types which were not in the list</li>
	 *     </ul>
	 * </li>
	 * <li>before Relation Y if
	 * 		<ul>
	 *      <li>Y's type is not in the list <b>OR</b></li>
	 *      <li>X's type is before Y's type in the list</li>
	 *      </ul>
	 * </li>
	 * <li>after Relation Y if
	 *      <ul>
	 *      <li>X's type is not in the list <b>OR</b></li>
	 *      <li>X's type is after Y's type in the list</li>
	 *      </ul>
	 * </li>
	 * </ul>
	 */
	public int compare(Relation relation, Relation otherRelation) {
		Integer relPos = desiredOrderMap.get(relation.getClass());
		Integer otherRelPos = desiredOrderMap.get(otherRelation.getClass());
		
		if (relPos == null && otherRelPos == null)
			return 0;
		
		if (otherRelPos == null)
			return -1;
		
		if (relPos == null)
			return 1;
		
		return relPos - otherRelPos;
	}
}
