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

"""
cytoflow.operations.bead_calibration
------------------------------------
"""

from traits.api import (HasStrictTraits, Str, File, Dict, Bool, Int, List, 
                        Float, Constant, provides, Callable, Any,
                        Instance)
import numpy as np
import math
import scipy.signal
import scipy.optimize
import sys
        
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
    
    Computes a log-linear calibration function that maps arbitrary fluorescence
    units to physical units (ie molecules equivalent fluorophore, or *MEF*).
    
    To use, set :attr:`beads_file` to an FCS file containing events collected *using
    the same cytometer settings as the data you're calibrating*.  Specify which 
    beads you ran by setting :attr:`beads_type` to match one of the  values of 
    :data:`BeadCalibrationOp.BEADS`; and set :attr:`units` to which channels you 
    want calibrated and in which units.  Then, call :meth:`estimate()` and check the 
    peak-finding with :meth:`default_view().plot()`.  If the peak-finding is wacky, 
    try adjusting :attr:`bead_peak_quantile` and :attr:`bead_brightness_threshold`.  When 
    the peaks are successfully identified, call :meth:`apply` to scale your 
    experimental data set. 
    
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
    units : Dict(Str, Str)
        A dictionary specifying the channels you want calibrated (keys) and
        the units you want them calibrated in (values).  The units must be
        keys of the :attr:`beads` attribute.       
        
    beads_file : File
        A file containing the FCS events from the beads.

    beads : Dict(Str, List(Float))
        The beads' characteristics.  Keys are calibrated units (ie, MEFL or
        MEAP) and values are ordered lists of known fluorophore levels.  Common
        values for this dict are included in :data:`BeadCalibrationOp.BEADS`.
        
    bead_peak_quantile : Int (default = 80)
        The quantile threshold used to choose bead peaks. 
        
    bead_brightness_threshold : Float (default = 100)
        How bright must a bead peak be to be considered?  
        
    bead_brightness_cutoff : Float
        If a bead peak is above this, then don't consider it.  Takes care of
        clipping saturated detection.  Defaults to 70% of the detector range.
        
    bead_histogram_bins : Int (default = 512)
        The number of bins to use in computing the bead histogram.  Tweak
        this if the peak find is having difficulty, or if you have a small 
        number of events
        
    force_linear : Bool (default = False)
        A linear fit in log space doesn't always go through the origin, which 
        means that the calibration function isn't strictly a multiplicative
        scaling operation.  Set :attr:`force_linear` to force the such
        behavior.  Keep an eye on the diagnostic plot, though, to see how much
        error you're introducing!
   
           
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
    :attr:`bead_brightness_threshold`).
    
    How to convert from a series of peaks to mean equivalent fluorochrome?
    If there's one peak, we assume that it's the brightest peak.  If there
    are two peaks, we assume they're the brightest two.  If there are ``n >=3``
    peaks, we check all the contiguous `n`-subsets of the bead intensities
    and find the one whose linear regression (in log space!) has the smallest
    norm (square-root sum-of-squared-residuals.)
    
    There's a slight subtlety in the fact that we're performing the linear
    regression in log-space: if the relationship in log10-space is ``Y=aX + b``,
    then the same relationship in linear space is ``x = 10**X``, ``y = 10**y``, and
    ``y = (10**b) * (x ** a)``.

    
    Examples
    --------
    Create a small experiment:
    
    .. plot::
        :context: close-figs
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "tasbe/rby.fcs")]
        >>> ex = import_op.apply()
    
    Create and parameterize the operation
    
    .. plot::
        :context: close-figs

        >>> bead_op = flow.BeadCalibrationOp()
        >>> beads = "Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R"
        >>> bead_op.beads = flow.BeadCalibrationOp.BEADS[beads]
        >>> bead_op.units = {"Pacific Blue-A" : "MEBFP",
        ...                  "FITC-A" : "MEFL",
        ...                  "PE-Tx-Red-YG-A" : "MEPTR"}
        >>>
        >>> bead_op.beads_file = "tasbe/beads.fcs"
    
    Estimate the model parameters
    
    .. plot::
        :context: close-figs 
    
        >>> bead_op.estimate(ex)
    
    Plot the diagnostic plot
    
    .. plot::
        :context: close-figs

        >>> bead_op.default_view().plot(ex)  

    Apply the operation to the experiment
    
    .. plot::
        :context: close-figs
    
        >>> ex = bead_op.apply(ex)  
        
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.beads_calibrate')
    friendly_id = Constant("Bead Calibration")
    
    name = Constant("Beads")
    units = Dict(Str, Str)
    
    beads_file = File(exists = True)
    bead_peak_quantile = Int(80)

    bead_brightness_threshold = Float(100.0)
    bead_brightness_cutoff = util.FloatOrNone(None)
    bead_histogram_bins = Int(512)
    
    # TODO - bead_brightness_threshold should probably be different depending
    # on the data range of the input.
    
    force_linear = Bool(False)
    
    beads = Dict(Str, List(Float))

    _histograms = Dict(Str, Any, transient = True)
    _calibration_functions = Dict(Str, Callable, transient = True)
    _peaks = Dict(Str, Any, transient = True)
    _mefs = Dict(Str, Any, transient = True)

    def estimate(self, experiment): 
        """
        Estimate the calibration coefficients from the beads file.
        
        Parameters
        ----------
        experiment : Experiment
            The experiment used to compute the calibration.
            
        """
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        if not self.beads_file:
            raise util.CytoflowOpError('beads_file', "No beads file specified")

        if not set(self.units.keys()) <= set(experiment.channels):
            raise util.CytoflowOpError('units',
                                       "Specified channels that weren't found in "
                                       "the experiment.")
            
        if not set(self.units.values()) <= set(self.beads.keys()):
            raise util.CytoflowOpError('units',
                                       "Units don't match beads.")
            
        self._histograms.clear()
        self._calibration_functions.clear()
        self._peaks.clear()
        self._mefs.clear()
                        
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

            if self.bead_brightness_cutoff is None:
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
            
            self._histograms[channel] = (hist_bins, hist_smooth)
            
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
                raise util.CytoflowOpError('units',
                                           "Invalid unit {0} specified for channel {1}".format(mef_unit, channel))
            
            # "mean equivalent fluorochrome"
            mef = self.beads[mef_unit]
                                                    
            if len(peaks) == 0:
                raise util.CytoflowOpError(None,
                                           "Didn't find any peaks for channel {}; "
                                           "check the diagnostic plot"
                                           .format(channel))
            elif len(peaks) > len(mef):
                raise util.CytoflowOpError(None,
                                           "Found too many peaks for channel {}; "
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
        """
        Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the experiment to which this operation is applied
            
        Returns
        -------
        Experiment 
            A new experiment with the specified channels calibrated in
            physical units.  The calibrated channels also have new metadata:
            
            - **bead_calibration_fn** : Callable (pandas.Series --> pandas.Series)
                The function to calibrate raw data to bead units
        
            - **bead_units** : String
                The units this channel was calibrated to
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        channels = list(self.units.keys())

        if not self.units:
            raise util.CytoflowOpError('units', "No channels to calibrate.")
        
        if not self._calibration_functions:
            raise util.CytoflowOpError(None,
                                       "Calibration not found. "
                                       "Did you forget to call estimate()?")
        
        if not set(channels) <= set(experiment.channels):
            raise util.CytoflowOpError('units',
                                       "Module units don't match experiment channels")
                
        if set(channels) != set(self._calibration_functions.keys()):
            raise util.CytoflowOpError('units',
                                       "Calibration doesn't match units. "
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
        Returns a diagnostic plot to see if the peak finding is working.
        
        Returns
        -------
        IView
            An diagnostic view, call :meth:`~BeadCalibrationDiagnostic.plot` to 
            see the diagnostic plots
        """

        return BeadCalibrationDiagnostic(op = self, **kwargs)
    
    # this silliness is necessary to squash the repr() call in sphinx.autodoc
    class _Beads(dict):
        def __repr__(self):
            if hasattr(sys.modules['sys'], 'IN_SPHINX'):
                return None
            return super().__repr__()
    
    BEADS = _Beads(
    {
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
          "MEAPCY7" : [718, 1920, 5133, 9324, 14210, 26735]}
    })
    """
    A dictionary containing the calibrated beads that Cytoflow currently knows
    about.  The available bead sets, the fluorophores and the laser / filter 
    sets with which they were characterized are below:
    
    - **Spherotech RCP-30-5A Lot AG01, AF02, AD04 and AAE01**
      
      - **MECSB** (Cascade Blue, 405 --> 450/50)
      - **MEBFP** (BFP, 405 --> 530/40)
      - **MEFL** (Fluroscein, 488 --> 530/40)
      - **MEPE** (Phycoerythrin, 488 --> 575/25)
      - **MEPTR** (PE-Texas Red, 488 --> 613/20)
      - **MECY** (Cy5, 488 --> 680/30)
      - **MEPCY7** (PE-Cy7, 488 --> 750 LP)
      - **MEAP** (APC, 633 --> 665/20)
      - **MEAPCY7** (APC-Cy7, 635 --> 750 LP)
      
    - **Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R**
    
      - **MECSB** (Cascade Blue, 405 --> 450/50)
      - **MEBFP** (BFP, 405 --> 530/40)
      - **MEFL** (Flurosceine, 488 --> 530/40)
      - **MEPE** (Phycoerythrin, 488 --> 575/25)
      - **MEPTR** (PE-Texas Red, 488 --> 613/20)
      - **MECY** (Cy5, 488 --> 680/30)
      - **MEPCY7** (PE-Cy7, 488 --> 750 LP)
      - **MEAP** (APC, 633 --> 665/20)
      - **MEAPCY7** (APC-Cy7, 635 --> 750 LP)      
    """
            

@provides(cytoflow.views.IView)
class BeadCalibrationDiagnostic(HasStrictTraits):
    """
    A diagnostic view for `BeadCalibrationOp`.
        
    Plots the smoothed histogram of the bead data; the peak locations;
    a scatter plot of the raw bead fluorescence values vs the calibrated unit 
    values; and a line plot of the model that was computed.  Make sure that the
    relationship is linear; if it's not, it likely isn't a good calibration!
    
    Attributes
    ----------
    op : Instance(BeadCalibrationOp)
        The operation instance whose parameters we're plotting.  Set 
        automatically if you created the instance using 
        :meth:`BeadCalibrationOp.default_view`.

    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.beadcalibrationdiagnosticview")
    friendly_id = Constant("Bead Calibration Diagnostic")
        
    op = Instance(BeadCalibrationOp)
    
    def plot(self, experiment):
        """
        Plots the diagnostic view.
        
        Parameters
        ----------
        experiment : Experiment
            The experiment used to create the diagnostic plot.
        
        """

        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")

        channels = list(self.op.units.keys())

        if not channels:
            raise util.CytoflowViewError(None, "No channels to plot")

        if set(channels) != set(self.op._histograms.keys()):
            raise util.CytoflowViewError(None, "You must estimate the parameters "
                                               "before plotting")

        plt.figure()
        
        for idx, channel in enumerate(channels):            
            hist_bins, hist_smooth = self.op._histograms[channel]
                
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
            
