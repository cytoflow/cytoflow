package org.flowcyt.facejava.faceflow.relations;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

import org.flowcyt.facejava.faceflow.exception.DuplicateRelationException;

/**
 * <p>
 * This class provides a simple implementation of RelationsRepository. It is not
 * backed by any persistent storage so any Relations must be manually added to it
 * before they can be queried for later.
 * 
 * @author echng
 */
public class SimpleRelationsRepository implements RelationsRepository {

	/**
	 * Maps a data file location to the data file's relation map object.
	 */
	public Map<String, DataFileRelationMap> fileRelations;
	
	/**
	 * Constructor. A SimpleRelationsRepository is created which has no Relations
	 * stored in it.
	 */
	public SimpleRelationsRepository() {
		fileRelations = new HashMap<String, DataFileRelationMap>();
	}
	
	public void addRelation(String dataFileLocation, Relation relation) throws DuplicateRelationException {
		DataFileRelationMap fileRel = obtainFileRelationMap(dataFileLocation);
		fileRel.addRelation(relation);
	}

	public void addRelation(String dataFileLocation, int dataSetNumber, Relation relation) throws DuplicateRelationException {
		DataFileRelationMap fileRel = obtainFileRelationMap(dataFileLocation);
		fileRel.addRelation(dataSetNumber, relation);
	}
	
	/**
	 * Retrieves the correct DataFileRelationMap to use with the given location. It
	 * tries to retrieve the map from the fileRelations map but if it doesn't exist
	 * creates a new relation map, adds it to fileRelations and returns it. 
	 * 
	 * @param location The location to obtain a DataFileRelationMap for.
	 * @return Returns the DataFileRelationMap for the location. 
	 */
	private DataFileRelationMap obtainFileRelationMap(String location) {
		DataFileRelationMap rv;
		if (fileRelations.containsKey(location)) {
			rv = fileRelations.get(location);
		} else {
			rv = new DataFileRelationMap(location);
			fileRelations.put(location, rv);
		}
		return rv;
	}

	public Set<String> getDataFileLocations() {
		return Collections.unmodifiableSet(fileRelations.keySet());
	}

	public RelationCollection getRelations(String dataFileLocation, int dataSetNumber) throws DuplicateRelationException {
		if (!fileRelations.containsKey(dataFileLocation))
			return new RelationCollection();
		
		return fileRelations.get(dataFileLocation).getRelations(dataSetNumber);
	}
	
	/**
	 * A helper class which stores the relations associated with the whole data
	 * file (location) and all data sets within the file (by number).
	 * 
	 * @author echng
	 */
	private class DataFileRelationMap {
		/**
		 * The location of the data file.
		 */
		private String location;
		
		/**
		 * Maps a data set number to the Relations that are specifically associated
		 * to that data set.
		 */
		private Map<Integer, RelationCollection> dsRelations;
		
		/**
		 * The Relations that are associated with the entire data set.
		 */
		private RelationCollection fileRelColl;
		
		/**
		 * Constructor. Creates a DataFileRelationMap with no Relations.
		 * 
		 * @param location The location of the data file.
		 */
		public DataFileRelationMap(String location) {
			this.location = location;
			this.fileRelColl = new RelationCollection();
			this.dsRelations = new HashMap<Integer, RelationCollection>();
		}
		
		/**
		 * Adds a Relation that is associated with the whole data file. 
		 * 
		 * @param rel The Relation to add.
		 * @throws DuplicateRelationException Thrown if a Relation of the same type
		 * has already been added for the whole data file which does not allow
		 * duplicates.
		 */
		public void addRelation(Relation rel) throws DuplicateRelationException {
			if (!fileRelColl.add(rel)) {
				throw new DuplicateRelationException(location, rel.getClass());
			}
		}
		
		/**
		 * Adds a Relation that is associated with the data set in the data file that
		 * has the given data set number.
		 * 
		 * @param dsNumber The number of the data set the Relation is for.
		 * @param rel The Relation to associate with the data set.
		 * @throws DuplicateRelationException Thrown if a Relation of the same type
		 * has already been added for the specific data set which does not allow
		 * duplicates.
		 */
		public void addRelation(int dsNumber, Relation rel) throws DuplicateRelationException {
			RelationCollection relColl;
			if (dsRelations.containsKey(dsNumber))
				relColl = dsRelations.get(dsNumber);
			else {
				relColl = new RelationCollection();
				dsRelations.put(dsNumber, relColl);
			}
			
			if (!relColl.add(rel))
				throw new DuplicateRelationException(location, dsNumber, rel.getClass());
		}
		
		/**
		 * Returns a RelationCollection containing the Relations which are associated
		 * with the data set (with the correct overriding rules applied).
		 * 
		 * @param dataSetNumber The number of the data set to get the relations for. 
		 * @return Returns a RelationCollection containing the Relations associated
		 * with the data set.
		 */
		public RelationCollection getRelations(int dataSetNumber) {
			if (!dsRelations.containsKey(dataSetNumber))
				return fileRelColl;
			
			return dsRelations.get(dataSetNumber).merge(fileRelColl);
		}
	}

}
