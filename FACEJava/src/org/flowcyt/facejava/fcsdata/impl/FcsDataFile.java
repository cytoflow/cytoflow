package org.flowcyt.facejava.fcsdata.impl;

import java.util.AbstractList;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/**
 * <p>
 * Represents a single FCS Data File which can contain one or more FcsDataSets. Since it
 * keeps multiple Populations (FcsDataSets) it is also implements the Collection
 * interface for Populations. The Populations in an FcsDataFile are ordered by the order
 * of their appearance in the actual data file. That order is maintained in FcsDataFile.   
 * 
 * <p>
 * The collection is unmodifiable an any attempt at addition or removal will throw an
 * UnsupportedOperationException in the data file. 
 * 
 * @author echng
 */
public class FcsDataFile extends AbstractList<FcsDataSet> {
	/**
	 * The FcsDataSets in the FCS file in the order they appear in the file. (i.e., by Data Set
	 * Number)
	 */
	private List<FcsDataSet> dataSets;
	
	/**
	 * Constructor. Creates an empty FcsDataFile with no FcsDataSets in it.
	 * Since the Collection is unmodifiable, this constructor is not that useful. 
	 */
	public FcsDataFile() {
		dataSets = new ArrayList<FcsDataSet>();
	}
	
	/**
	 * Constructor. Creates a FcsDataFile which contains the FcsDataSets in the given
	 * collection. 
	 * 
	 * @param coll A Collection containing the FcsDataSets to put in the created
	 * FcsDataFile.
	 */
	public FcsDataFile(Collection<? extends FcsDataSet> coll) {
		this();
		
		for (FcsDataSet ds : coll) {
			dataSets.add(ds);
		}
		
		Collections.sort(dataSets, new Comparator<FcsDataSet>() {
			public int compare(FcsDataSet o1, FcsDataSet o2) {
				return o1.getDataSetNumber() - o2.getDataSetNumber();
			}
		});
	}
	
	/**
	 * Retrieves the FcsDataSet with the given data set number.
	 * 
	 * @param dataSetnumber The number of the data set to return. Starts from 1 and are in the
	 * order they appeared in the data file.
	 * @return Returns the data set whose data set is the given number.
	 */
	public FcsDataSet getByDataSetNumber(int dataSetnumber) {
		return dataSets.get(dataSetnumber - 1);
	}
	
	/**
	 * This get retrieves by list index (which starts from 0) and not by data set number.
	 */
	@Override public FcsDataSet get(int index) {
		return dataSets.get(index);
	}

	@Override public int size() {
		return dataSets.size();
	}
}
