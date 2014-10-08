package org.flowcyt.facejava.fcsdata.statistics;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;

import org.apache.commons.math.stat.descriptive.AbstractUnivariateStatistic;
import org.apache.commons.math.stat.descriptive.DescriptiveStatistics;
import org.apache.commons.math.stat.descriptive.UnivariateStatistic;
import org.apache.commons.math.stat.descriptive.moment.StandardDeviation;
import org.apache.commons.math.stat.descriptive.moment.Variance;
import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Parameter;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;

/**
 * <p>
 * Contains the descriptive statistics for a Population for one Parameter. 
 *
 * @author echng
 */
public class PopulationParameterStatistics {
	
	/**
	 * The Parameter that the statistics are for.
	 */
	private Parameter parameter;
	
	/**
	 * The PopulationStatistics object that this ParameterStatistics object is a part of.
	 */
	private PopulationStatistics popStats;
	
	/**
	 * The Commons Math DescriptiveStatistics object. It is kept around so that an arbitrary
	 * percentile can be calculated. It also allows us to be able to apply an aribitrary
	 * (Univariate) Statistic to the event data for the Parameter and get a value. 
	 */
	private DescriptiveStatistics stats;
	
	/*
	 * The following statistics are all just cached values for the results returned by calling
	 * their respective methods in DescriptiveStatistics. DescriptiveStatistics always
	 * recalculates the value on each call but since the insideEvent data should not change 
	 * we can save time by caching the results during each update() call. 
	 */ 
	
	private double min = Double.NaN;
	
	private double max = Double.NaN;
	
	private double mean = Double.NaN;
	
	private double geomMean = Double.NaN;
	
	private double kurtosis = Double.NaN;
	
	private double sumSq = Double.NaN;
	
	private double sum = Double.NaN;
	
	private double unbiasedVariance = Double.NaN;
	
	private double biasedVariance = Double.NaN;
	
	private double unbiasedStdDev = Double.NaN;
	
	private double biasedStdDev = Double.NaN;
	
	private double median = Double.NaN;
	
	private double firstQuartile = Double.NaN;
	
	private double thirdQuartile = Double.NaN;
	
	private double skewness = Double.NaN;
	
	private int modeFrequency = 0;
	
	private double[] modes = {};
	
	/**
	 * Constructor. Protected so that it is only created by PopulationStatistics. Consumers only
	 * need to read the info from this class.
	 *
	 * @param popStat The PopulationStatistics object the new 
	 * PopulationParameterStatistics object is a part of.
	 * @param param The Parameter the stats are for.
	 */
	protected PopulationParameterStatistics(PopulationStatistics popStat, Parameter param) {
		this.parameter = param;
		this.popStats = popStat;
		stats = DescriptiveStatistics.newInstance();
		stats.setWindowSize(DescriptiveStatistics.INFINITE_WINDOW);
	}
	
	/**
	 * Updates the calculated statistics to include the new inside events.
	 * Protected since it should only be called when the PopulationStatistics object has its
	 * update() called. 
	 
	 * @param newEvents A Collection containing the new Events to update the stats with. These
	 * Events must not have already been in a set that update() was called with (or else there
	 * values will be double counted).
	 * @throws DataRetrievalException Thrown if there was a problem retrieving data
	 * from the Events during stats calculations.
	 */
	protected void update(Collection<Event> newEvents) throws DataRetrievalException {
		DataRetriever retriever = popStats.getRetriever();
		for (Event insideEvent : newEvents) {
			stats.addValue(retriever.getScale(parameter, insideEvent));
		}
		min = stats.getMin();
		max = stats.getMax();
		mean = stats.getMean();
		geomMean = stats.getGeometricMean();
		kurtosis = stats.getKurtosis();
		sumSq = stats.getSumsq();
		sum = stats.getSum();
		unbiasedVariance = stats.getVariance();
		biasedVariance = stats.apply(new Variance(false));
		unbiasedStdDev = stats.getStandardDeviation();
		biasedStdDev = stats.apply(new StandardDeviation(false));
		median = stats.getPercentile(50);
		firstQuartile = stats.getPercentile(25);
		thirdQuartile = stats.getPercentile(75);
		skewness = stats.getSkewness();
		
		Mode mode = new Mode();
		stats.apply(mode);
		modeFrequency = mode.getModeFrequency();
		modes = mode.getModes();
	}
	
	/**
	 * @return Returns the Parameter these Statistics are for.
	 */
	public Parameter getParameter() {
		return parameter;
	}	
	
	/**
	 * Applies a arbitrary Univariate Statistic to the Event data for the Parameter.
	 * 
	 * @param stat The statistic to get the value for.
	 * @return Returns the value of the statistic for the Event Data for the Parameter.
	 */
	public double apply(UnivariateStatistic stat) {
		return stats.apply(stat);
	}
	
	/**
	 * @return Returns the minumum datum in the Event data for the Parameter. 
	 */
	public double getMin() {
		return min;
	}
	
	/**
	 * @return Returns the maximum datum in the Event data for the Parameter. 
	 */
	public double getMax() {
		return max;
	}
	
	/**
	 * @return Returns the mean of the Event data for the Parameter. 
	 */
	public double getMean() {
		return mean;
	}
	
	/**
	 * @return Returns the geometric mean of the Event data for the Parameter. 
	 */
	public double getGeometricMean() {
		return geomMean;
	}
	
	/**
	 * @return Returns the sum of squares of the Event data for the Parameter. 
	 */
	public double getSumSquares() {
		return sumSq;
	}
	
	/**
	 * @return Returns the sum of the Event data for the Parameter. 
	 */
	public double getSum() {
		return sum;
	}
	
	/**
	 * @return Returns the unbiased standard deviation of the Event data for the Parameter. 
	 */
	public double getUnbiasedStdDev() {
		return unbiasedStdDev;
	}
	
	/**
	 * @return Returns the biased standard deviation of the Event data for the Parameter. 
	 */
	public double getBiasedStdDev() {
		return biasedStdDev;
	}
	
	/**
	 * @return Returns the unbiased variance of the Event data for the Parameter. 
	 */
	public double getUnbiasedVariance() {
		return unbiasedVariance;
	}
	
	/**
	 * @return Returns the biased variance of the Event data for the Parameter. 
	 */	
	public double getBiasedVariance() {
		return biasedVariance;
	}
	
	/**
	 * @return Returns the median of the Event data for the Parameter. 
	 */
	public double getMedian() {
		return median;
	}
	
	/**
	 * @return Returns the first quartile (25th percentile) of the Event data for the
	 * Parameter. 
	 */
	public double getFirstQuartile() {
		return firstQuartile;
	}
	
	/**
	 * @return Returns the second quartile (50th percentile) of the Event data for the
	 * Parameter. This value is the same as the value returned by getMedian(). 
	 */
	public double getSecondQuartile() {
		return getMedian();
	}
	
	/**
	 * @return Returns the third quartile (75th percentile) of the Event data for the
	 * Parameter. 
	 */
	public double getThirdQuartile() {
		return thirdQuartile;
	}
	
	/**
	 * @return Returns the fourth quartile (100 percentile) of the Event data for the
	 * Parameter. This value is the same as the value returned by getMax(); 
	 */
	public double getFourthQuartile() {
		return getMax();
	}
	
	/**
	 * @param p The percentile to return. Must be in the interval [0, 100]. 
	 * @return Returns the pth percentile of the Event data for the Parameter.
	 */
	public double getPercentile(double p) {
		return stats.getPercentile(p);
	}
	
	/**
	 * @return Returns the skewness of the Event data for the Parameter. 
	 */
	public double getSkewness() {
		return skewness;
	}
	
	/**
	 * @return Returns the kurtosis of the Event data for the Parameter. 
	 */
	public double getKurtosis() {
		return kurtosis;
	}
	
	/**
	 * @return Returns the standard error of the Event data for the Parameter. Uses the
	 * biased standard deviation for calculation. 
	 */
	public double getStandardError() {
		return getUnbiasedStdDev() / Math.sqrt(popStats.getN());
	}
	
	/**
	 * @return Returns the coefficient of variation of the Event data for the Parameter. Uses
	 * the biased standard deviation for calculation. It is calculated as std. dev. / mean * 100.
	 */
	public double getCoefficientOfVariation() {
		return 100 * getUnbiasedStdDev() / getMean();
	}
	
	/**
	 * @return Returns the mode frequency. That is the number of times the mode(s) appears in
	 * the inside Event set. If there is no mode (e.g., 0 values or no number appears more than
	 * once), 0 is returned.
	 */
	public int getModeFrequency() {
		return modeFrequency;
	}
	
	/**
	 * @return Returns the mode that is the smallest. Returns Double.Nan if there are no modes.
	 */
	public double getSmallestMode() {
		return modes.length > 0 ? modes[0] : Double.NaN;
	}
	
	/**
	 * @return Returns an array containing all the modes of the inside events. If there is no
	 * mode (the mode frequency is 0 -- e.g., 0 values or no number appears more than once),
	 * then an empty array is returned.
	 */
	public double[] getModes() {
		return modes;
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append(parameter.toString());
		
		builder.append("\nMinimum: ");
		builder.append(getMin());
		
		builder.append("\nMaximum: ");
		builder.append(getMax());
		
		builder.append("\nMean: ");
		builder.append(getMean());
		
		builder.append("\nMode Frequency: ");
		builder.append(getModeFrequency());
		
		builder.append("\nModes: ");
		builder.append(Arrays.toString(getModes()));
		
		builder.append("\nGeometric Mean: ");
		builder.append(getGeometricMean());
		
		builder.append("\nSum of Squares: ");
		builder.append(getSumSquares());
		
		builder.append("\nSum: ");
		builder.append(getSum());
		
		builder.append("\nUnbiased Standard Deviation: ");
		builder.append(getUnbiasedStdDev());
		
		builder.append("\nBiased Standard Deviation: ");
		builder.append(getBiasedStdDev());
		
		builder.append("\nUnbiased Variance: ");
		builder.append(getUnbiasedVariance());
		
		builder.append("\nBiased Variance: ");
		builder.append(getBiasedVariance());
		
		builder.append("\nMedian: ");
		builder.append(getMedian());
		
		builder.append("\nFirst Quartile: ");
		builder.append(getFirstQuartile());
		
		builder.append("\nSecond Quartile: ");
		builder.append(getSecondQuartile());
		
		builder.append("\nThird Quartile: ");
		builder.append(getThirdQuartile());
		
		builder.append("\nFourth Quartile: ");
		builder.append(getFourthQuartile());
		
		builder.append("\nSkewness: ");
		builder.append(getSkewness());
		
		builder.append("\nKurtosis: ");
		builder.append(getKurtosis());
		
		builder.append("\nStandard Error: ");
		builder.append(getStandardError());
		
		builder.append("\nCoefficient Of Variation: ");
		builder.append(getCoefficientOfVariation());
		builder.append("\n");
		
		return builder.toString();
	}
	
	/**
	 * <p>
	 * An inner class which implements the calculation of the Mode. It finds all
	 * modes in the given data and also how many times the mode(s) appear (called the mode
	 * value here).
	 * 
	 * @author echng
	 */
	private static class Mode extends AbstractUnivariateStatistic {
		private static final long serialVersionUID = 3334059765274710994L;

		/**
		 * A list of all the modes for the data in the last call to evaluate().
		 */
		private List<Double> modes = new ArrayList<Double>();
		
		/**
		 * The number of times the mode(s) appears.
		 */
		private int modeFrequency = 0;
		
		/**
		 * Returns the smallest mode found. Use getModes() and getModeValue() for all the
		 * modes and how many times they appear, respectively. If each of the values appears
		 * only once, then there is no mode and Double.NaN is returned.
		 */
		public double evaluate(double[] values, int begin, int length) {
			modes.clear();
			modeFrequency = 0;
			
			if (values.length <= 0 || length <= 0)
				return Double.NaN;
			
			int end = begin + length;
			
			Arrays.sort(values, begin, end);
			
			double previousValue = 0;
			int maxOccurs = -Integer.MIN_VALUE;
			int currentOccurs = 0;
			
			int i = begin;
			
			do {
				// The first element is a special case.
				if (i == begin) {
					previousValue = values[i];
					++currentOccurs;
				} else if (previousValue == values[i]) {
					++currentOccurs;
				} else {
					maxOccurs = updateModes(previousValue, currentOccurs, maxOccurs);
					currentOccurs = 1;
					previousValue = values[i]; 
				}
				++i;
			} while (i < end);
			
			modeFrequency = updateModes(previousValue, currentOccurs, maxOccurs);
			
			if (modeFrequency == 1) {
				modes.clear();
				modeFrequency = 0;
				return Double.NaN;
			}
			
			return modes.get(0);
		}
		
		/**
		 * A helper function which updates the member variables as needed and returns 
		 * max{currentOccurs, maxOccurs}. i.e., if currentOccurs > maxOccurs, previousValue
		 * becomes the new mode and currentOccurs, is returned. If currentOccurs == maxOccurs,
		 * previousValue is added as a mode. Othewrwise, nothing changes.
		 * 
		 * @param previousValue
		 * @param currentOccurs
		 * @param maxOccurs
		 * @return
		 */
		private int updateModes(double previousValue, int currentOccurs, int maxOccurs) {
			int rv = maxOccurs;
			if (currentOccurs > maxOccurs) {
				modes.clear();
				modes.add(previousValue);
				rv = currentOccurs;
			} else if (currentOccurs == maxOccurs) {
				modes.add(previousValue);
			}
			return rv;
		}
		
		/**
		 * @return Returns the number of times the mode(s) appears.
		 */
		public int getModeFrequency() {
			return modeFrequency;
		}
		
		/**
		 * @return Returns an array containing all the modes of the data given in the
		 * last call to evaluate(). If there is no mode (0 values or no number appears more than
		 * once), then an empty array is returned. 
		 */
		public double[] getModes() {
			double[] rv = new double[modes.size()];
			for (int i = 0; i < modes.size(); ++i) {
				rv[i] = modes.get(i);
			}
			return rv;
		}
	}
}
	
