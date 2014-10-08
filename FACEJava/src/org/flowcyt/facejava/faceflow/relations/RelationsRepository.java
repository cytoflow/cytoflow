package org.flowcyt.facejava.faceflow.relations;

import java.util.Set;

import org.flowcyt.facejava.faceflow.exception.DuplicateRelationException;

/**
 * <p>
 * A RelationsRepository holds Relations between a FCS data set and some other value (stored in the 
 * Relation). FCS data sets are identified by the location of the datafile (as a string) they reside in
 * and their dataset number (which starts from 1) within the file.
 * 
 * <p>
 * The location does not have to be a file path but may be a URI, URL, etc. It is left to the
 * implentations to decide on how it refers to files. Obviously, care must be taken to make sure that
 * queries match the type of location string used by the concrete implementation and that when loading
 * the data files for processing the loading method uses the correct location type.
 * 
 * <p>
 * The repository makes no assumptions about whether or not an FCS Data File is located at the given
 * location. It simply associates a Relation with that location.
 * 
 * @author echng
 */
public interface RelationsRepository {
	
	/**
	 * Adds a Relation for a whole data file (i.e., all data sets within the file) to the repository.
	 * Relations added for whole data files can be overriden for specific data sets within the file
	 * by using addRelation(String, int, Relation).
	 * 
	 * @param dataFileLocation The location of the data file. Used to identify data files within the
	 * repository.
	 * @param relation The Relation to be added for all data sets within the data file.
	 * @throws DuplicateRelationException Thrown if a relation is added where another relation of the
	 * same type (which does not allow duplicates) is already associated with the data file.
	 * Relations of the same type specified for specific data sets are not considered to be
	 * duplicates (due to the overriding rules).
	 */
	public void addRelation(String dataFileLocation, Relation relation) throws DuplicateRelationException;

	/**
	 * Adds a Relation for a specific data set within a data file. This Relation will override any Relations
	 * that are associated with the whole data file that have the same type as the given Relation. 
	 * i.e. Data File X contains Data Sets Y and Z and Relations R and S have the same type. Let R be
	 * associated with X and S with Y. Then, Z has only R while Y has only S. 
	 * 
	 * @param dataFileLocation The location of the data file. Used to identify data files within the
	 * repository.
	 * @param dataSetNumber The data set number within the data file of the data set to be associated
	 * with the Relation.
	 * @param relation The relation to be added for the specific data set identified by data file 
	 * location and data set number.
	 * @throws DuplicateRelationException Thrown if a relation is added where another relation of the
	 * same type (which does not allow duplicates) is already associated with the same data set. Relations of the same type specified for 
	 * the whole data file that the data set is in are not considered to be duplicates (due to the
	 * overriding rules).
	 */
	public void addRelation(String dataFileLocation, int dataSetNumber, Relation relation) throws DuplicateRelationException;
	
	/**
	 * <p>
	 * Get the locations of data fies in the repository.
	 * 
	 * <p>
	 * <b>Notes:</p>
	 * <ul>
	 * <li>(Valid) FCS files may or may not actually exist at these locations</li>
	 * <li>How these locations are described (e.g., URI, file path, etc.) is left up to
	 *     implementers. Care must be taken to make sure that these locations match with how the files
	 *     will be loaded. (See FileLoader).</li>
	 * <li>To get all Relations for all Data Sets within all Data Files, one would:
	 *    <ol>
	 *    <li>Get all data file locations.</li>
	 *    <li>For each location
	 *        <ol>
	 *        <li>Load the data file. If doesn't exist or not valid, skip it</li>
	 *        <li>For each data set within the data file, find all Relations that apply to it
	 *            by using getRelations().</li>
	 *        </ol>
	 *    </li>
	 *    </ol>
	 * </li>
	 * </ul>
	 * 
	 * <p>
	 * See RelationsRepositoryIterator for an implementation.   
	 *          
	 * @return Returns a set containing all the locations for the data files that have Relations
	 * associated with them.
	 *
	 */
	public Set<String> getDataFileLocations();
	
	/**
	 * <p>
	 * Finds all Relations that apply to the data set identified by the given location and data set number.
	 * The overriding rules are taken into account, that is, the Relations returned are associated with:
	 * <ul>
	 * <li>the specific data set OR
	 * <li>the entire data file containing the data set UNLESS a relation of the same type was specified
	 * <li>for the specific data set. (Note that relations with a specific data set completely override
	 * <li>relations with the whole data file even when duplicates are allowed, i.e., if there are three
	 *     relations of type X associated with the whole data file but only one of type X associated with
	 *     the data set, only the single relation will be part of the returned set. 
	 * </ul>
	 * 
	 * <p>
	 * Relations can only be queried by Data Set (i.e., data file location and data set number) due to
	 * the overriding rules. Relations for a whole data file may not apply to some (or any) of the data
	 * sets within the file and as such are useless. 
	 *  
	 * @param dataFileLocation The location of the data file containing the data set.
	 * @param dataSetNumber The number of the data set within the data file at location.
	 * @return Returns a RelationCollection containing the Relations that are
	 * associated with the data set. The returned RelationCollection is not necessarily
	 * backed by the repository, i.e., adding a Relation to the RelationCollection
	 * may not (and most likely will not) add it to the Repository as well. Always
	 * add Relations to the RelationsRepository if you want them to be available for queueing
	 * later.
	 * @throws DuplicateRelationException Thrown if the data set is found to have multiple relations of 
	 * the same type (which does not allow duplicates) associated with it *after* the overriding rules are
	 * applied (i.e., either multiple relations of same type were associated with the specific data set
	 * or associated with the whole data file but were not overriden for the specfic data set.) Even
	 * though addRelation checks for duplicates duplicate relations may still exist if the repository was 
	 * instantiated with a whole store of Relations (i.e., an RDF file or a database) and a sanity check
	 * was not performed during loading (e.g., for performance reasons). 
	 */
	public RelationCollection getRelations(String dataFileLocation, int dataSetNumber) throws DuplicateRelationException;

}
