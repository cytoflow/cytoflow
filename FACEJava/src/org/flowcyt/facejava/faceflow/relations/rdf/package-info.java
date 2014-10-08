
/**
 * <p>
 * Contains an implementation of RelationsRepository which uses Flow Relations RDF
 * files as its backing store. The RdfRelationsRepository handles querying for and
 * adding Relations to the RDF model represented by an RDF file. It also handles
 * converting between a RDF statement and the corresponding Relation (both ways) as
 * needed to perform the additions and queries. The JENA library is used to work with
 * RDF.
 *  
 * <p>
 * By default, support is only added for Relations and RDF properties which are part
 * of the Flow Relations standard. To support new types of properties in the RDF file,
 * one does not need to change RdfRelationsRepository which is designed to support
 * any type of Relation. Instead, one needs to define how to convert a RDF Statement
 * (from JENA) to a Relation based on the property in the statement and back. To do
 * the former, create a new RelationCreator that can create a Relation with the
 * information in that type of Statement and register it with the RdfRelationFactory
 * used by the RdfRelationsRepository. To do the latter, create a new method in a 
 * StatementFactoryVisitor which can visit the new Relation type and create the
 * appropriate RDF Statement. StatementFactoryVisitorImpl can be subclassed to keep
 * using default methods for the standard Relation types, while providing an
 * implementation for new Relation types.  
 *   
 * @author echng
 */
package org.flowcyt.facejava.faceflow.relations.rdf;