package org.flowcyt.facejava.faceflow.relations;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;

/**
 * <p>
 * A RelationVisitor is used to process Relations. This is a variation on the classic
 * GoF Visitor pattern. The problem with the GoF pattern is that it only works when a
 * fixed set of elements can be visited. If a new Visitable element is created, this
 * interface and *all* implementors must be updated with a visit() method for the new
 * type of element. Clearly, this is not suitable for our case where we need to any
 * new type of relations must be able to be visited.
 * 
 * <p>
 * Our solution to this problem is to use a Reflective Visitor (see the "Easy Element
 * and Operation Adder" pattern in 
 * http://jerry.cs.uiuc.edu/~plop/plop2001/accepted_submissions/PLoP2001/ymai0/PLoP2001_ymai0_1.pdf)
 * with the modification of using Java 5 Annotations rather than relying on the method
 * being named "visit".
 * 
 * <p>
 * We provide a dispatch() method which takes a Relation object (as the Relation supertype)
 * and uses Reflection to determine the concrete type of the Relation. Then (again using
 * Reflection) it tries to find a method in the visitor class which is annotated with
 * the @VisitMethod annotation and takes one argument which is the same concrete type
 * as the Relation. If found, the method is invoked, otherwise the Relation is passed to the
 * defaultVisit method where the concrete Visitor can provide default behaviour for
 * handling types of Relations which it does not know about.
 * 
 * <p>
 * A Visitor's visit methods are allowed to return some arbitrary value as an Object
 * (use null if it doesn't make sense). A subtype may override the dispatch method
 * to downcast the return object from Object if all its VisitMethods return a common
 * supertype (i.e., return (T)super.dispatch(); where T is the common supertype). 
 * 
 * <p>
 * Note that the accept() method in Relations is no longer needed as in the GoF pattern.
 * 
 * <p>
 * Inheritance is handled with Visitors and Relations as follows:
 * <ol>
 * <li>Start with the concrete types of the Relation to be visited and the 
 *      RelationsVisitor.
 * <li>Find a method in the visitor, which handles that specific type of relation.
 * <li>If none exists then try to find such a method in the superclass of the visitor.
 *     Repeat with the super-class of the super-class of the visitor (and so on)
 *     until we get past RelationsVisitor. 
 * <li>If still no method is found, repeat (2) and (3) with the Relation's super-class.
 * <li>Repeat (4) up the Relation hierarchy until we get past Relation.
 *     If no method is found when we have reached the top of both hierarchies,
 *     then use the defaultVisit method (defaultVisit is dispatched as per usual
 *     Java mechanics).
 * </ol>
 *        
 * <p>
 * Thus, it first tries to find the method that can handle the most concrete type of
 * the Relation and if there are multiple methods in the Visitor's hierarchy that 
 * does so, it chooses the method in the most concrete Visitor type. 
 *      
 * <p>
 * So to handle Relations, implementers of the visitor interface must provide a 
 * method which is annotated with @VisitMethod and which takes one argument of
 * the type of Relation to be handled by that method.
 *
 * <p>
 * Since Gating, Compensation, and Transformation are Relations defined in the standard
 * their visit() methods are given in this interface to make sure that implementers will
 * knowingly handle them (even if they are just ignored). Experiment Description and
 * Instrumentation are not included since they are not essential for interpreting
 * FCS data.
 * 
 * <p>
 * An alternative solution that doesn't use Reflection is the Acyclic Visitor pattern
 * (http://www.objectmentor.com/resources/articles/acv.pdf). It was not used
 * because the parallel inheritance hierarchies needed between Relations and their
 * Visitors leads to an explosion in the number of classes, which was viewed as
 * undesirable for developers who wish to use the library. With this solution,
 * developers just need to remember to provide the correct visit() method in their
 * Visitors.
 * 
 * @author echng
 */
public abstract class RelationVisitor {
	/**
	 * The Class object for the top of the Relations hierarchy. (So we don't
	 * go past it when searching.)
	 */
	public static final Class<Relation> RELATION_BASE_INTERFACE_CLASS = Relation.class;

	/**
	 * The Class object for the top of the RelationVisitor hierarchy. (So we don't
	 * go past it when searching.)
	 */
	public static final Class<RelationVisitor> VISITOR_BASE_INTERFACE_CLASS = RelationVisitor.class;
	
	/**
	 * We'll cache the results of the method search for each type of Relation. If
	 * null is associated with the type of Relation, then no method was found.
	 * 
	 * We must map the pair of the concrete type of visitor and the concrete type of the
	 * relation class to method since the map is shared by sub-classes (i.e multiple
	 * visitors).
	 */
	private static Map<MethodCacheKey, Method> methodsCache = new HashMap<MethodCacheKey, Method>();
	
	/**
	 * <p>
	 * Uses Reflection to find the correct visit() method to be called for the concrete
	 * type of the given Relation and invokes it. If no method is found, defaultVisit()
	 * is called for the Relation. See class comments for more info.
	 * 
	 * <p>
	 * All Relations to be visited should be called with this method.
	 * 
	 * @param rel The Relation to be handled.
	 * @return Returns the return value of the method (the found visit() or
	 * defaultVisit()) that was invoked. 
	 */
	public Object dispatch(Relation rel) {
		Method m;
		MethodCacheKey key = new MethodCacheKey(this.getClass(), rel.getClass());
		if (methodsCache.containsKey(key)) {
			m = methodsCache.get(rel.getClass());
		} else {
			m = findMethod(rel);
			// We'll cache it even if null and no method was found. There shouldn't 
			// magically be a method on the next call... 
			methodsCache.put(key, m);
		}
		
		Object rv;
		if (m == null) {
			rv = this.defaultVisit(rel);
		} else {
			try {
				rv = m.invoke(this, new Object[] {rel});
			} catch (IllegalArgumentException e) {
				rv = this.defaultVisit(rel);
			} catch (IllegalAccessException e) {
				rv = this.defaultVisit(rel);
			} catch (InvocationTargetException e) {
				rv = this.defaultVisit(rel);
			}
		}
		return rv;
	}
	
	/**
	 * Performs the method search as described in the class comments.
	 * 
	 * @param rel The Relation whose class the method should be for.
	 * @return Return the Method object if found, or null if not.
	 */
	private Method findMethod(Relation rel) {
		Class<?> relClass = rel.getClass();
		while (RELATION_BASE_INTERFACE_CLASS.isAssignableFrom(relClass)) {
			Class<?> visitorClass = this.getClass();
			while (VISITOR_BASE_INTERFACE_CLASS.isAssignableFrom(visitorClass)) {
				for (Method m : visitorClass.getMethods()) {
					if (m.isAnnotationPresent(VisitMethod.class)) {
						Class<?>[] paramTypes = m.getParameterTypes();
						if (paramTypes.length == 1 && paramTypes[0].equals(relClass)) {
							return m;
						}
					}
				}
				visitorClass = visitorClass.getSuperclass();
			}
			relClass = relClass.getSuperclass();
		}
		return null;
	}
	
	/**
	 * Called when no visit method could be found (see class comments) that can handle
	 * the type of the given Relation. Allows implementers to provide some default
	 * behaviour.
	 * 
	 * @param rel The Relation to be visited.
	 * @return An arbitrary return value that is defined by the concrete Visitor 
	 * (use null if it doesn't make sense).
	 */
	public abstract Object defaultVisit(Relation rel);
	
	private class MethodCacheKey {
		
		private Class<? extends RelationVisitor> visitorClass;
		
		private Class<? extends Relation> visitedClass;

		public MethodCacheKey(Class<? extends RelationVisitor>visitorClass, Class<? extends Relation> visitedClass) {
			this.visitorClass = visitorClass;
			this.visitedClass = visitedClass;
		}
		
		public boolean equals(Object other) {
			if (other instanceof MethodCacheKey) {
				MethodCacheKey otherKey = (MethodCacheKey) other;
				return otherKey.visitorClass.equals(this.visitorClass) &&
						otherKey.visitedClass.equals(this.visitedClass);
			}
			return false;
		}
		
	}
}
