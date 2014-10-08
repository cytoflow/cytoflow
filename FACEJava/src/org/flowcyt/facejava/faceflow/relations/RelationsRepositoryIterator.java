package org.flowcyt.facejava.faceflow.relations;

import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Set;

import org.flowcyt.facejava.faceflow.exception.DuplicateRelationException;
import org.flowcyt.facejava.faceflow.exception.FileLoaderException;
import org.flowcyt.facejava.faceflow.loader.FileLoader;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;

/**
 * <p>
 * The RelationsRepositoryIterator will take a RelationsRepository and a FileLoader
 * and use the FileLoader to load all the data files in the RelationsRepository and
 * for all data sets in all valid FCS files loaded, it will output a DataSetRelations
 * object which contains an FcsDataSet and all Relations associated with it in the 
 * RelationsRepository.
 * 
 * <p>
 * The iterator performs the loading of FcsDataFiles and querying of the 
 * RelationsRepository as the iteration takes place (i.e., when next() is called)
 * rather than all at once in the beginning. 
 * 
 * <p>
 * A DataSetRelations object will only be produced for data sets in successfully
 * loaded files and where a call to RelationsRepository.getRelations() for the
 * FcsDataSet does not produce a DuplicateRelationException. 
 * 
 * <p>
 * Any errors which have occured so far can be obtained through getErrors() which
 * returns a map from the data file location to the error that occured.
 * 
 * <p>
 * Care should be taken to make sure the given FileLoader is able to correctly load
 * the data file locations as they are identified within the RelationsRepository.
 * 
 * <p>
 * The remove() operation is not supported.
 * 
 * @author echng
 */
public class RelationsRepositoryIterator implements Iterator<DataSetRelations> {

	/**
	 * The RelationsRepository to iterate through.
	 */
	private RelationsRepository relRep;
	
	/**
	 * The Loader object to use to load FcsDataFiles from the locations in the 
	 * RelationRepository.
	 */
	private FileLoader loader;
	
	/**
	 * Maps the data file location to the error that prevented it from being loaded.
	 */
	private Map<String, Exception> errors;
	
	/**
	 * The location of the current data file whose data sets are in the DataSetRelations
	 * being returned by next()
	 */
	private String currentFileLocation;
	
	/**
	 * The Iterator through the Set of locations in the relations repository.
	 */	
	private Iterator<String> locationIter;
	
	/**
	 * The Iterator through the FcsDataSets in the FcsDataFile that was successfully
	 * loaded last. Must never be null for findNextRelations() to work. See comments
	 * in constructor and findNextRelations().
	 */ 
	private Iterator<FcsDataSet> dsIter;
	
	/**
	 * The DataSetRelations to be returned in the next call to next(). Is null if
	 * there are no more.
	 */
	private DataSetRelations nextRelations;
	
	/**
	 * Constructor. Creates an iterator for the repository.
	 * 
	 * @param relRep The RelationsRepository containing the data file locations
	 * and Relations to use to construct the DataSetRelations to be iterated through.
	 * @param loader The FileLoader to use to load FcsDataFiles from the locations
	 * in the repositoiry. Must be able to use whatever type of locations strings
	 * (filepaths, URIs, etc.) are used to identify data files in the repository.
	 */
	public RelationsRepositoryIterator(RelationsRepository relRep, FileLoader loader) {
		this.relRep = relRep;
		this.loader = loader;
		this.errors = new HashMap<String, Exception>();
		
		locationIter = relRep.getDataFileLocations().iterator();
		
		// A marginal hack to get an empty iterator, so that findNextRelations() never
		// has to worry about null iterators and only has to do hasNext() tests. 
		// It greatly simplifies the logic in findNextRelations().
		Set<FcsDataSet> temp = Collections.emptySet();
		dsIter = temp.iterator();
		
		findNextRelations();
	}
	
	/**
	 * Finds (and creates) the next DataSetRelations object that will be returned
	 * by the next next() call and assigns it to the nextRelations member. If there
	 * are no more DataSetRelations to be returned, nextRelations is set to null.
	 */
	private void findNextRelations() {
		// We cannot simply load the next datafile and/or create the appropriate
		// DataSetRelations since either of those steps can fail. So we'll repeatedly
		// try until we either run out of data sets or we succeed.
		while (true) {
			if (!dsIter.hasNext() && !locationIter.hasNext()) {
				// If there are no more data sets and no more data files, there are no more
				// Relations so set it to null.
				//
				// Note that dsIter is never null since it is set to an empty iterator
				// in the constructor.
				nextRelations = null;
				return;
			} else if (dsIter.hasNext()) {
				// We need to finish trying all the data sets in the current data file 
				// before moving on to the next location.
				//
				// Since dsIter is set to an empty iterator at construction, this
				// branch will never be entered until the first successful load of
				// a data file.
				FcsDataSet ds = dsIter.next();
				try {
					RelationCollection relations = relRep.getRelations(currentFileLocation, ds.getDataSetNumber());
					nextRelations = new DataSetRelations(currentFileLocation, ds, relations);
					return;
				} catch (DuplicateRelationException e) {
					// If there's an error, continue the search.
					errors.put(currentFileLocation, e);
				}
			} else {
				// If we get here we know that the current data file has no more data
				// sets but there are locations. So try to load the next one.
				currentFileLocation = locationIter.next();
				FcsDataFile dataFile = loadDataFile(currentFileLocation);
				if (dataFile != null) {
					dsIter = dataFile.iterator();
				}
				// If there was an error (dataFile == null), then we can simply try again
				// on the next iteration of the while loop. dsIter was not changed so
				// if there are still more locations we'll end up in this branch of 
				// the if statement again.( If there are no more, then the first
				// branch will be entered and the search will stop.
			}			
		}
	}
	
	/**
	 * @param location The location of the data file as it's identified in the
	 * RelationsRepository.
	 * @return Returns the FcsDataFile as loaded by the FileLoader given at
	 * construction or null if there was an error loading the file. Any exceptions
	 * are caught and added to the map that can be* accessed through getErrors().
	 */
	private FcsDataFile loadDataFile(String location) {
		FcsDataFile rv = null;
		try {
			rv = loader.loadFcsFile(location);
		} catch (FileLoaderException e) {
			errors.put(location, e);
		}
		return rv;
	}
	
	public boolean hasNext() {
		return nextRelations != null;
	}

	public DataSetRelations next() {
		DataSetRelations rv = nextRelations;
		if (rv == null)
			throw new NoSuchElementException();
		
		findNextRelations();
		return rv;
	}
	
	/**
	 * Not supported. Throws UnsupportedOperationException.
	 */
	public void remove() {
		throw new UnsupportedOperationException("remove() not supported.");		
	}
	
	/**
	 * @return Returns true if there have been any errors so far as iteration has 
	 * progressed.
	 */
	public boolean hasErrors() {
		return !errors.isEmpty();
	}
	
	/**
	 * @return Returns a map containing all the errors that have occured. The Map maps
	 * the data file location for which the error occured to the error.
	 */
	public Map<String, Exception> getErrors() {
		return Collections.unmodifiableMap(errors);
	}
}
