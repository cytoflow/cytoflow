
/**
 * <p>
 * Contains classes and interfaces used to represent the Relations between the different
 * types of Files in the FACEJava project as well as any other metadata about those
 * files. These classes are meant to be used and extended by people wishing to use
 * FACEFlow as a library to process the Relations. New types of metadata Relations can
 * be added by subclassing Relation, while RelationsRepository is a way of adding 
 * and determining what Relations are associated with a data set. The 
 * RelationsRepositoryIterator, RelationsVisitor, DataSetRelations and
 * DataSetRelationsVisitor classes are all part of the provided framework for processing
 * Relations.
 *   
 * @author echng
 */
package org.flowcyt.facejava.faceflow.relations;