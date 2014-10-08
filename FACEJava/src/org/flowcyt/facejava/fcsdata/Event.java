package org.flowcyt.facejava.fcsdata;

import java.util.Arrays;

/**
 * <p>
 * Represents a single Event in the data set. Event data can (or at least should) only be
 * retrieved using DataRetrievers.
 * 
 * <p>
 * Since we only use scale when performing analyses, Events store the scale value and
 * not channel. In fact, there is absolutely no support for channel in this library (beyond reading
 * it from the FCS file.
 * 
 * <p>
 * Events are immutable.
 * 
 * @author echng
 */
public final class Event {
	/**
	 * An array of the scale data in the event. The order of the array corresponds
	 * to the order of the FCS parameter list. e.g., the 5th data point in this array
	 * corresponds to the 5th parameter in the DataSet's parameter list. An array is used to
	 * avoid the auto-unboxing that would happen in a list.
	 */
	private final double[] eventScaleData;
	
	/**
	 * Creates an Event using the given (scale) double data.
	 * 
	 * @param scaleData The data points for the event. The order in the array must
	 * correspond to the parameter order.
	 */
	public Event(double[] scaleData) {
		eventScaleData = scaleData;
	}
	
	/**
	 * DataRetrievers should be used to get Event data.
	 * 
	 * @param parameterNumber The parameter number of the Parameter to get the data 
	 * value for. Starts from 1.
	 * @return Returns the scale value for the given parameter in this event.
	 */
	public double getScale(int parameterNumber) {
		return eventScaleData[parameterNumber - 1];
	}
	
	/**
	 * @return Returns a copy of the array that stores the scale data in the event. The
	 * data in the array corresponds to the FcsParameter order of the data set that contains this
	 * event.  
	 */
	public double[] getData() {
		double[] copy = new double[eventScaleData.length];
		System.arraycopy(eventScaleData, 0, copy, 0, eventScaleData.length);
		return copy;
	}
	
	/**
	 * Determines if the other event has the same data, within an epsilon. Mainly used for
	 * testing, since events that have the same data are not necessarily equal.
	 * 
	 * @param other The other event.
	 * @param epsilon The allowed difference between any two data points in the
	 * two events.
	 * @return Returns true if the two events have the same data to within the
	 * given espilon.
	 */
	public boolean hasSameData(Event other, double epsilon) {
		for (int i = 0; i < eventScaleData.length; ++i) {
			if (other.eventScaleData[i] < (eventScaleData[i] - epsilon) || 
					other.eventScaleData[i] > eventScaleData[i] + epsilon)
				return false;
		}
		return true;
	}
	
	/**
	 * Determines if the other event has the same data. Mainly used for
	 * testing, since events that have the same data are not necessarily equal.
	 * 
	 * @param other The other event.
	 * @return Returns true if the two events have the same data
	 */
	public boolean hasSameData(Event other) {
		return Arrays.equals(eventScaleData, other.eventScaleData);
	}
	
	public String toString() {
		return Arrays.toString(eventScaleData);
	}
}
