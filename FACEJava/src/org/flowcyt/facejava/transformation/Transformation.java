package org.flowcyt.facejava.transformation;

import org.flowcyt.facejava.fcsdata.Parameter;

/**
 * <p>
 * A Transformation applies a transformation to data retrieved from some other Parameter(s)
 * before returning its data value for an event. Thus, a Transformation depends on at
 * least one other Parameter.
 * 
 * @author echng
 */
public interface Transformation extends Parameter {

}
