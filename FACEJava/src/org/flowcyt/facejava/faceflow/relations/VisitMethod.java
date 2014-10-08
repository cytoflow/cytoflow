package org.flowcyt.facejava.faceflow.relations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Used to annotate methods in subclasses of RelationsVisitor which can be called by
 * RelationsVisitor.dispatch() to handle visiting a Relation. Methods annotated by
 * VisitMethod must take one argument which is a subclass of Relation.
 * 
 * @author echng
 */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface VisitMethod {
}
