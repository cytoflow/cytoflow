
/**
 * <p>
 * Contains FileLoader classes which are the main abstractions for loading all the
 * different types of Files that are part of the FACEJava project. Since file locations
 * may not always be expressed as URIs, FileLoaders take strings as arguments and it
 * is up to each different implementation to try and interepret the string as they know
 * how. For new types of location Strings, most implementations will want to subclass
 * from CachingFileLoader.
 *   
 * @author echng
 */
package org.flowcyt.facejava.faceflow.loader;