#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Aug 31, 2015

@author: brian
'''
from traits.api import (HasStrictTraits, Str, File, Dict, Bool, Int, List, 
                        Float, Constant, provides, Undefined, Callable, Any,
                        Instance)
import numpy as np
import math
import scipy.signal
import scipy.optimize
        
import matplotlib.pyplot as plt

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation
from .import_op import check_tube, Tube, ImportOp

@provides(IOperation)
class BeadCalibrationOp(HasStrictTraits):
    """
    Calibrate arbitrary channels to molecules-of-fluorophore using fluorescent
    beads (eg, the Spherotech RCP-30-5A rainbow beads.)
    
    To use, set the `beads_file` property to an FCS file containing the beads'
    events; specify which beads you ran by setting the `beads_type` property
    to match one of the values of BeadCalibrationOp.BEADS; and set the
    `units` dict to which channels you want calibrated and in which units.
    Then, call `estimate()` and check the peak-finding with 
    `default_view().plot()`.  If the peak-finding is wacky, try adjusting
    `bead_peak_quantile` and `bead_brightness_threshold`.  When the peaks are
    successfully identified, call apply() on your experimental data set. 
    
    If you can't make the peak finding work, please submit a bug report!
    
    This procedure works best when the beads file is very clean data.  It does
    not do its own gating (maybe a future addition?)  In the meantime, 
    I recommend gating the *acquisition* on the FSC/SSC channels in order
    to get rid of debris, cells, and other noise.
    
    Finally, because you can't have a negative number of fluorescent molecules
    (MEFLs, etc) (as well as for math reasons), this module filters out
    negative values.
    
    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation.)

    units : Dict(Str, Str)
        A dictionary specifying the channels you want calibrated (keys) and
        the units you want them calibrated in (values).  The units must be
        keys of the `beads` attribute.       
        
    beads_file : File
        A file containing the FCS events from the beads.  Must be set to use
        `estimate()`.  This isn't persisted by `pickle()`.

    beads : Dict(Str, List(Float))
        The beads' characteristics.  Keys are calibrated units (ie, MEFL or
        MEAP) and values are ordered lists of known fluorophore levels.  Common
        values for this dict are included in BeadCalibrationOp.BEADS.
        Must be set to use `estimate()`.
        
    bead_peak_quantile : Int (default = 80)
        The quantile threshold used to choose bead peaks.  Must be set to use 
        `estimate()`.
        
    bead_brightness_threshold : Float (default = 100)
        How bright must a bead peak be to be considered?  Must be set to use 
        `estimate()`.
        
    bead_brightness_cutoff : Float
        If a bead peak is above this, then don't consider it.  Takes care of
        clipping saturated detection.  Defaults to 70% of the detector range.
        
    bead_histogram_bins : Int (default = 512)
        The number of bins to use in computing the bead histogram.  Tweak
        this if the peak find is having difficulty, or if you have a small 
        number of events
        
    force_linear : Bool(False)
        A linear fit in log space doesn't always go through the origin, which 
        means that the calibration function isn't strictly a multiplicative
        scaling operation.  Set `force_linear` to force the such
        behavior.  Keep an eye on the diagnostic plot, though, to see how much
        error you're introducing!
        
        
    Metadata
    --------
    bead_calibration_fn : Callable (pandas.Series --> pandas.Series)
        The function to calibrate raw data to bead units
        
    bead_units : String
        The units this channel was calibrated to
        
        
    Notes
    -----
    The peak finding is rather sophisticated.  
    
    For each channel, a 256-bin histogram is computed on the log-transformed
    bead data, and then the histogram is smoothed with a Savitzky-Golay 
    filter (with a window length of 5 and a polynomial order of 1).  
    
    Next, a wavelet-based peak-finding algorithm is used: it convolves the
    smoothed histogram with a series of wavelets and looks for relative 
    maxima at various length-scales.  The parameters of the smoothing 
    algorithm were arrived at empircally, using beads collected at a wide 
    range of PMT voltages.
    
    Finally, the peaks are filtered by height (the histogram bin has a quantile
    greater than `bead_peak_quantile`) and intensity (brighter than 
    `bead_brightness_threshold`).
    
    How to convert from a series of peaks to mean equivalent fluorochrome?
    If there's one peak, we assume that it's the brightest peak.  If there
    are two peaks, we assume they're the brightest two.  If there are n >=3
    peaks, we check all the contiguous n-subsets of the bead intensities
    and find the one whose linear regression (in log space!) has the smallest
    norm (square-root sum-of-squared-residuals.)
    
    There's a slight subtlety in the fact that we're performing the linear
    regression in log-space: if the relationship in log10-space is Y=aX + b,
    then the same relationship in linear space is x = 10**X, y = 10**y, and
    y = (10**b) * (x ** a).
    
    One more thing.  Because the beads are (log) evenly spaced across all
    the channels, we can directly compute the fluorophore equivalent in channels
    where we wouldn't usually measure that fluorophore: for example, you can
    compute MEFL (mean equivalent fluorosceine) in the PE-Texas Red channel,
    because the bead peak pattern is the same in the PE-Texas Red channel
    as it would be in the FITC channel.
    
    Examples
    --------
    >>> bead_op = flow.BeadCalibrationOp()
    >>> bead_op.beads = flow.BeadCalibrationOp.BEADS["Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R"]
    >>> bead_op.units = {"Pacific Blue-A" : "MEFL",
                         "FITC-A" : "MEFL",
                         "PE-Tx-Red-YG-A" : "MEFL"}
    >>>
    >>> bead_op.beads_file = "beads.fcs"
    >>> bead_op.estimate(ex3)
    >>>
    >>> bead_op.default_view().plot(ex3)  
    >>> # check the plot!
    >>>
    >>> ex4 = bead_op.apply(ex3)  
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.beads_calibrate')
    friendly_id = Constant("Bead Calibration")
    
    name = Constant("Bead Calibration")
    units = Dict(Str, Str)
    
    beads_file = File(exists = True)
    bead_peak_quantile = Int(80)

    bead_brightness_threshold = Float(100)
    bead_brightness_cutoff = Float(Undefined)
    bead_histogram_bins = Int(512)
    
    # TODO - bead_brightness_threshold should probably be different depending
    # on the data range of the input.
    
    force_linear = Bool(False)
    
    beads = Dict(Str, List(Float))

    _calibration_functions = Dict(Str, Callable, transient = True)
    _peaks = Dict(Str, Any, transient = True)
    _mefs = Dict(Str, Any, transient = True)

    def estimate(self, experiment, subset = None): 
        """
        Estimate the calibration coefficients from the beads file.
        """
        if experiment is None:
            raise util.CytoflowOpError("No experiment specified")
        
        if not self.beads_file:
            raise util.CytoflowOpError("No beads file specified")

        if not set(self.units.keys()) <= set(experiment.channels):
            raise util.CytoflowOpError("Specified channels that weren't found in "
                                  "the experiment.")
            
        if not set(self.units.values()) <= set(self.beads.keys()):
            raise util.CytoflowOpError("Units don't match beads.")
                        
        # make a little Experiment
        check_tube(self.beads_file, experiment)
        beads_exp = ImportOp(tubes = [Tube(file = self.beads_file)],
                             channels = {experiment.metadata[c]["fcs_name"] : c for c in experiment.channels},
                             name_metadata = experiment.metadata['name_metadata']).apply()
        
        channels = list(self.units.keys())

        for channel in channels:
            data = beads_exp.data[channel]
            
            # TODO - this assumes the data is on a linear scale.  check it!
            data_range = experiment.metadata[channel]['range']

            if self.bead_brightness_cutoff is Undefined:
                cutoff = 0.7 * data_range
            else:
                cutoff = self.bead_brightness_cutoff
                                            
            # bin the data on a log scale

            hist_bins = np.logspace(1, math.log(data_range, 2), num = self.bead_histogram_bins, base = 2)
            hist = np.histogram(data, bins = hist_bins)
            
            # mask off-scale values
            hist[0][0] = 0
            hist[0][-1] = 0
            
            # smooth it with a Savitzky-Golay filter
            hist_smooth = scipy.signal.savgol_filter(hist[0], 5, 1)
            
            # find peaks
            peak_bins = scipy.signal.find_peaks_cwt(hist_smooth, 
                                                    widths = np.arange(3, 20),
                                                    max_distances = np.arange(3, 20) / 2)
                                    
            # filter by height and intensity
            peak_threshold = np.percentile(hist_smooth, self.bead_peak_quantile)
            peak_bins_filtered = \
                [x for x in peak_bins if hist_smooth[x] > peak_threshold 
                 and hist[1][x] > self.bead_brightness_threshold
                 and hist[1][x] < cutoff]
            
            peaks = [hist_bins[x] for x in peak_bins_filtered]            
            mef_unit = self.units[channel]
            
            if not mef_unit in self.beads:
                raise util.CytoflowOpError("Invalid unit {0} specified for channel {1}".format(mef_unit, channel))
            
            # "mean equivalent fluorochrome"
            mef = self.beads[mef_unit]
                                                    
            if len(peaks) == 0:
                raise util.CytoflowOpError("Didn't find any peaks for channel {}; "
                                           "check the diagnostic plot"
                                           .format(channel))
            elif len(peaks) > len(mef):
                raise util.CytoflowOpError("Found too many peaks for channel {}; "
                                           "check the diagnostic plot"
                                           .format(channel))
            elif len(peaks) == 1:
                # if we only have one peak, assume it's the brightest peak
                a = mef[-1] / peaks[0]
                self._peaks[channel] = peaks
                self._mefs[channel] = [mef[-1]]
                self._calibration_functions[channel] = lambda x, a=a: a * x
            elif len(peaks) == 2:
                # if we have only two peaks, assume they're the brightest two
                self._peaks[channel] = peaks
                self._mefs[channel] = [mef[-2], mef[-1]]
                a = (mef[-1] - mef[-2]) / (peaks[1] - peaks[0])
                self._calibration_functions[channel] = lambda x, a=a: a * x
            else:
                # if there are n > 2 peaks, check all the contiguous n-subsets
                # of mef for the one whose linear regression with the peaks
                # has the smallest (norm) sum-of-residuals.
                
                # do it in log10 space because otherwise the brightest peaks
                # have an outsized influence.
                                
                best_resid = np.inf
                for start, end in [(x, x+len(peaks)) for x in range(len(mef) - len(peaks) + 1)]:
                    mef_subset = mef[start:end]
                    
                    # linear regression of the peak locations against mef subset
                    lr = np.polyfit(np.log10(peaks), 
                                    np.log10(mef_subset), 
                                    deg = 1, 
                                    full = True)
                                        
                    resid = lr[1][0]
                    if resid < best_resid:
                        best_lr = lr[0]
                        best_resid = resid
                        self._peaks[channel] = peaks
                        self._mefs[channel] = mef_subset
   
                if self.force_linear:
                    # if we're forcing a linear scale for the calibration
                    # function, find that scale with an optimization.  (we can't
                    # use this above, to find the MEFs from the peaks, because
                    # when i tried it mis-identified the proper subset.)
                    
                    # even though this keeps things a linear scale, it can
                    # actually introduce *more* errors because "blank" beads
                    # still fluoresce.
                    
                    def s(x):
                        p = np.multiply(self._peaks[channel], x)
                        return np.sum(np.abs(np.subtract(p, self._mefs[channel])))
                    
                    res = scipy.optimize.minimize(s, [1])
                    
                    a = res.x[0]
                    self._calibration_functions[channel] = \
                        lambda x, a=a: a * x
                              
                else:              
                    # remember, these (linear) coefficients came from logspace, so 
                    # if the relationship in log10 space is Y = aX + b, then in
                    # linear space the relationship is x = 10**X, y = 10**Y,
                    # and y = (10**b) * x ^ a
                    
                    # also remember that the result of np.polyfit is a list of
                    # coefficients with the highest power first!  so if we
                    # solve y=ax + b, coeff #0 is a and coeff #1 is b
                    
                    a = best_lr[0]
                    b = 10 ** best_lr[1]
                    self._calibration_functions[channel] = \
                        lambda x, a=a, b=b: b * np.power(x, a)


    def apply(self, experiment):
        """Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        old_experiment : Experiment
            the experiment to which this op is applied
            
        Returns
        -------
            a new experiment calibrated in physical units.
        """
        if experiment is None:
            raise util.CytoflowOpError("No experiment specified")
        
        channels = list(self.units.keys())

        if not self.units:
            raise util.CytoflowOpError("No channels to calibrate.")
        
        if not self._calibration_functions:
            raise util.CytoflowOpError("Calibration not found. "
                                  "Did you forget to call estimate()?")
        
        if not set(channels) <= set(experiment.channels):
            raise util.CytoflowOpError("Module units don't match experiment channels")
                
        if set(channels) != set(self._calibration_functions.keys()):
            raise util.CytoflowOpError("Calibration doesn't match units. "
                                  "Did you forget to call estimate()?")

        # two things.  first, you can't raise a negative value to a non-integer
        # power.  second, negative physical units don't make sense -- how can
        # you have the equivalent of -5 molecules of fluoresceine?  so,
        # we filter out negative values here.

        new_experiment = experiment.clone()
        
        for channel in channels:
            new_experiment.data = \
                new_experiment.data[new_experiment.data[channel] > 0]
                
        new_experiment.data.reset_index(drop = True, inplace = True)
        
        for channel in channels:
            calibration_fn = self._calibration_functions[channel]
            
            new_experiment[channel] = calibration_fn(new_experiment[channel])
            new_experiment.metadata[channel]['bead_calibration_fn'] = calibration_fn
            new_experiment.metadata[channel]['bead_units'] = self.units[channel]
            if 'range' in experiment.metadata[channel]:
                new_experiment.metadata[channel]['range'] = calibration_fn(experiment.metadata[channel]['range'])
            
        new_experiment.history.append(self.clone_traits(transient = lambda t: True)) 
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to see if the bleedthrough spline estimation
        is working.
        
        Returns
        -------
            IView : An IView, call plot() to see the diagnostic plots
        """

        return BeadCalibrationDiagnostic(op = self, **kwargs)
    
    BEADS = {
             # from http://www.spherotech.com/RCP-30-5a%20%20rev%20H%20ML%20071712.xls
             "Spherotech RCP-30-5A Lot AG01, AF02, AD04 and AAE01" :
                { "MECSB" : [216, 464, 1232, 2940, 7669, 19812, 35474],
                  "MEBFP" : [861, 1997, 5776, 15233, 45389, 152562, 396759],
                  "MEFL" :  [792, 2079, 6588, 16471, 47497, 137049, 271647],
                  "MEPE" :  [531, 1504, 4819, 12506, 36159, 109588, 250892],
                  "MEPTR" : [233, 669, 2179, 5929, 18219, 63944, 188785],
                  "MECY" : [1614, 4035, 12025, 31896, 95682, 353225, 1077421],
                  "MEPCY7" : [14916, 42336, 153840, 494263],
                  "MEAP" :  [373, 1079, 3633, 9896, 28189, 79831, 151008],
                  "MEAPCY7" : [2864, 7644, 19081, 37258]},
             # from http://www.spherotech.com/RCP-30-5a%20%20rev%20G.2.xls
             "Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R":
                { "MECSB" : [179, 400, 993, 3203, 6083, 17777, 36331],
                  "MEBFP" : [700, 1705, 4262, 17546, 35669, 133387, 412089],
                  "MEFL" :  [692, 2192, 6028, 17493, 35674, 126907, 290983],
                  "MEPE" :  [505, 1777, 4974, 13118, 26757, 94930, 250470],
                  "MEPTR" : [207, 750, 2198, 6063, 12887, 51686, 170219],
                  "MECY" :  [1437, 4693, 12901, 36837, 76621, 261671, 1069858],
                  "MEPCY7" : [32907, 107787, 503797],
                  "MEAP" :  [587, 2433, 6720, 17962, 30866, 51704, 146080],
                  "MEAPCY7" : [718, 1920, 5133, 9324, 14210, 26735]}}
    
@provides(cytoflow.views.IView)
class BeadCalibrationDiagnostic(HasStrictTraits):
    """
    Plots diagnostic histograms of the peak finding algorithm.
    
    Attributes
    ----------
    name : Str
        The instance name (for serialization, UI etc.)
    
    op : Instance(BeadCalibrationDiagnostic)
        The op whose parameters we're viewing
        
    """
    
    # traits   
    _id = "edu.mit.synbio.cytoflow.view.autofluorescencediagnosticview"
    _friendly_id = "Autofluorescence Diagnostic" 
    
    name = Str
    
    # TODO - why can't I use BeadCalibrationOp here?
    op = Instance(IOperation)
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted histogram view of a channel"""

        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")

        channels = list(self.op.units.keys())

        if not channels:
            raise util.CytoflowViewError("No channels to plot")

        # make a little Experiment
        try:
            check_tube(self.op.beads_file, experiment)
            beads_exp = ImportOp(tubes = [Tube(file = self.op.beads_file)],
                                 channels = {experiment.metadata[c]["fcs_name"] : c for c in experiment.channels},
                                 name_metadata = experiment.metadata['name_metadata']).apply()
        except util.CytoflowOpError as e:
            raise util.CytoflowViewError(e.__str__()) from e

        plt.figure()
        
        for idx, channel in enumerate(channels):
            if channel not in beads_exp.channels:
                raise util.CytoflowViewError("Channel {} not in the beads!"
                                             .format(channel))
            data = beads_exp.data[channel]
            data_range = experiment.metadata[channel]['range']
                
            # bin the data on a log scale            
            hist_bins = np.logspace(1, math.log(data_range, 2), num = self.op.bead_histogram_bins, base = 2)
            hist = np.histogram(data, bins = hist_bins)
            
            # mask off-scale values
            hist[0][0] = 0
            hist[0][-1] = 0
            
            hist_smooth = scipy.signal.savgol_filter(hist[0], 5, 1)
                
            plt.subplot(len(channels), 2, 2 * idx + 1)
            plt.xscale('log')
            plt.xlabel(channel)
            plt.plot(hist_bins[1:], hist_smooth)

            if channel in self.op._peaks and channel in self.op._mefs:
                for peak in self.op._peaks[channel]:
                    plt.axvline(peak, color = 'r')
                plt.subplot(len(channels), 2, 2 * idx + 2)
                plt.xscale('log')
                plt.yscale('log')
                plt.xlabel(channel)
                plt.ylabel(self.op.units[channel])
                plt.plot(self.op._peaks[channel], 
                         self.op._mefs[channel], 
                         marker = 'o')
                
                xmin, xmax = plt.xlim()
                x = np.logspace(np.log10(xmin), np.log10(xmax))
                plt.plot(x, 
                         self.op._calibration_functions[channel](x), 
                         color = 'r', linestyle = ':')
            
        plt.tight_layout(pad = 0.8)
            
