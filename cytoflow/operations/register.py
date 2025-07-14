#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflow.operations.registration
------------------------------------

The `registration` module contains two classes:

`RegistrationOp` -- warps channels to bring areas of high density into registration

`RegistrationDiagnostic` -- a diagnostic view to make sure
that `RegistrationOp` performed correctlyu
"""

from traits.api import (HasStrictTraits, Str, Dict, Int, List, 
                        Float, Constant, provides, Instance, Union,
                        Callable, Any, Enum, Tuple)
import numpy as np
import math
import scipy.signal
import scipy.optimize
from sklearn.neighbors import KernelDensity
from statsmodels.nonparametric.bandwidths import bw_scott, bw_silverman
        
import matplotlib.pyplot as plt

import cytoflow.views
import cytoflow.utility as util
from cytoflow.views.kde_1d import _kde_support

from .i_operation import IOperation
from .import_op import check_tube, Tube, ImportOp

@provides(IOperation)
class RegistrationOp(HasStrictTraits):
    """
    `RegistrationOp` is used to *register* different data sets with eachother.
    It identifies areas of high density that are shared across all most of the
    data sets, then applies a warp function to align those areas of high
    density. This is commonly used to correct sample-to-sample variation
    across large data sets. This is *not* a multidimensional algorithm --
    if you apply it to multiple channels, each channel is warped 
    independently.
    
    Attributes
    ----------
   
    channels : List(Str)
        The channels to register.
        
    scale : Dict(Str : {"linear", "logicle", "log"})
        How to scale the channels before registering.
        
    by : List(Str)
        Which conditions to use to group samples? These are usually
        experimental conditions, not gates!
        
    subset : Str
        How to filter the data before estimating the transformation?
        
    **Smoothing parameters**
        
    kernel : Str (default = ``gaussian``)
        The kernel to use for the kernel density estimate. Choices are:
        
            - ``gaussian`` (the default)
            - ``tophat``
            - ``epanechnikov``
            - ``exponential``
            - ``linear``
            - ``cosine``
            
    bw : Str or Float (deafult = ``scott``)
        The bandwidth for the kernel, controls how lumpy or smooth the
        kernel estimate is.  Choices are:
        
            - ``scott`` (the default) - ``1.059 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
            - ``silverman`` - ``.9 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
            
        If a float is given, it is the bandwidth.   Note, this is in 
        scaled units, not data units.
        
    gridsize : int (default = 100)
        How many locations should we evaluate the kernel?
        
    ** Peak finding parameters **
    
    ** Peak clustering parameters **
        
    
    Notes
    -----
    The registration algorithm follows the approach from the ``warpSet`` 
    function in the R/Bioconductor ``flowStats`` package. The precise details
    differ depending on what is available in the scientific Python ecosystem,
    but the overall flow remains the same. For each channel:
    
    - Rescale the data (if necessary)
    
    - Smooth the data using a kernel density estimate
    
    - Use a peak-finding algorithm to find landmarks in the distribution
    
    - Use 1-dimensional K-means across groups to group landmarks together
    
    - Determine the median of each group. These are the "destinations" for our 
      warp functions.
      
    - Using tools from functional data analysis, compute a "warp" function
      that can be applied to each group to move the landmarks to the median.
      
    - Apply the warp function to the underlying data, scaling and then 
      inverting as you do so.
      
    Every step except the last is performed by the `estimate` function. The 
    diagnostic plot shows the smoothed distribution, the peaks, their medians
    and clusters for each division of data.
    
    Examples
    --------
        
    """
    
    # traits
    id = Constant('cytoflow.operations.registration')
    friendly_id = Constant("Density Registration")
    
    name = Constant("Registration")
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    by = List(Str)
    
    # Smoothing
    
    kernel = Enum('gaussian','tophat','epanechnikov','exponential','linear','cosine')
    bw = Union(Enum('scott', 'silverman'), Float)
    gridsize = Int(100)
    
    # Peak clustering
    max_clusters = 
    _scale = Dict(Str, Instance(util.IScale))
    _kde = Dict(Tuple(Any, Str), Tuple(np.ndarray, np.ndarray))
    _peaks = Dict(Tuple(Any, Str), np.ndarray)
    _warp_functions = Dict(Tuple(Any, Str), Callable)


    def estimate(self, experiment, subset = None): 
        """
        Estimate the calibration coefficients from the beads file.
        
        Parameters
        ----------
        experiment : `Experiment`
            The experiment used to compute the calibration.
            
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
        if len(self.channels) == 0:
            raise util.CytoflowOpError('channels',
                                       "Must set at least one channel")

        if len(self.channels) != len(set(self.channels)):
            raise util.CytoflowOpError('channels', 
                                       "Must not duplicate channels")

        for c in self.channels:
            if c not in experiment.data:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not found in the experiment"
                                      .format(c))
                
        for c in self.scale:
            if c not in self.channels:
                raise util.CytoflowOpError('channels',
                                           "Scale set for channel {0}, but it isn't "
                                           "in the experiment"
                                           .format(c))
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                
        if self.kernel not in ['gaussian','tophat','epanechnikov','exponential','linear','cosine']:
            raise util.CytoflowOpError(None,
                                       "kernel must be one of ['gaussian'|'tophat'|'epanechnikov'|'exponential'|'linear'|'cosine']")
                
        if self.num_components > 1 and "Component" in self.by:
            raise util.CytoflowOpError('by',
                                       "'Component' is going to be added as an "
                                       "index level to the new statistic, so you "
                                       "can't use it to aggregate events.")
                
        if subset:
            try:
                experiment = experiment.query(subset)
            except:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(subset))
                
            if len(experiment) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no events"
                                             .format(subset))
                
        if self.by:
            groupby = experiment.data.groupby(self.by, observed = False)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True, observed = False)
            
        self._warp_functions.clear()
        self._scale.clear()
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        for c in self.channels:
            if c in self.scale:
                self._scale[c] = util.scale_factory(self.scale[c], experiment, channel = c)
            else:
                self._scale[c] = util.scale_factory(util.get_default_scale(), experiment, channel = c)
        
   
        warp_functions = {}
        for channel in self.channels:
            for group, group_data in groupby:
            
                #compute the KDE 
                scaled_data = self._scale[channel](group_data[channel])
                
                if self.bw == 'scott':
                    bw = bw_scott(scaled_data)
                elif self.bw == 'silverman':
                    bw = bw_silverman(scaled_data)
                else:
                    bw = self.bw
    
                support = _kde_support(scaled_data, bw, self.gridsize, 3.0, (-np.inf, np.inf))[:, np.newaxis]
                kde = KernelDensity(kernel = self.kernel, bandwidth = bw).fit(scaled_data.to_numpy()[:, np.newaxis])
                density = kde.score_samples(support)
                self._kde[(channel, group)] = (support, density)
                
                # find the peaks
                self._peaks[(channel, group)] = scipy.signal.find_peaks()
                
                
            # cluster the peaks ACROSS GROUPS
            
            
                
        # set atomically to support the GUI
        self._warp_functions = warp_functions
                
    
            data = beads_exp.data[channel]
            data_range = experiment.metadata[channel]['range']
                                     
            # bin the data on a log scale

            hist_bins = np.logspace(1, math.log(data_range, 2), num = self.bead_histogram_bins, base = 2)
            hist = np.histogram(data, bins = hist_bins)
            
            # mask off-scale values
            hist[0][0] = 0
            hist[0][-1] = 0
            
            # smooth it with a Savitzky-Golay filter
            hist_smooth = scipy.signal.savgol_filter(hist[0], 5, 1)
            
            self._histograms[channel] = (hist, hist_bins, hist_smooth)

            
        # find peaks
        for channel in channels:
            # TODO - this assumes the data is on a linear scale.  check it!
            data_range = experiment.metadata[channel]['range']

            if self.bead_brightness_cutoff is None:
                cutoff = 0.7 * data_range
            else:
                cutoff = self.bead_brightness_cutoff
                   
            hist = self._histograms[channel][0]
            hist_bins = self._histograms[channel][1]
            hist_smooth = self._histograms[channel][2]

            peak_bins = scipy.signal.find_peaks_cwt(hist_smooth, 
                                                    widths = np.arange(3, 20),
                                                    max_distances = np.arange(3, 20) / 2)
                                    
            # filter by height and intensity
            peak_threshold = np.percentile(hist_smooth, self.bead_peak_quantile)
            peak_bins_filtered = \
                [x for x in peak_bins if hist_smooth[x] > peak_threshold 
                 and hist[1][x] > self.bead_brightness_threshold
                 and hist[1][x] < cutoff]
            
            self._peaks[channel] = [hist_bins[x] for x in peak_bins_filtered]    


        # compute the conversion        
        calibration_functions = {}
        for channel in channels:
            peaks = self._peaks[channel]
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
                self._mefs[channel] = [mef[-1]]
                calibration_functions[channel] = lambda x, a=a: a * x
            elif len(peaks) == 2:
                # if we have only two peaks, assume they're the brightest two
                self._mefs[channel] = [mef[-2], mef[-1]]
                a = (mef[-1] - mef[-2]) / (peaks[1] - peaks[0])
                calibration_functions[channel] = lambda x, a=a: a * x
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
                    calibration_functions[channel] = \
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
                    calibration_functions[channel] = \
                        lambda x, a=a, b=b: b * np.power(x, a)
                        
        # set this atomically to support GUI
        self._calibration_functions = calibration_functions


    def apply(self, experiment):
        """
        Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        experiment : `Experiment`
            the experiment to which this operation is applied
            
        Returns
        -------
        Experiment 
            A new experiment with the specified channels calibrated in
            physical units.  The calibrated channels also have new metadata:
            
            - **bead_calibration_fn** : Callable (`pandas.Series` --> `pandas.Series`)
                The function to calibrate raw data to bead units
        
            - **bead_units** : Str
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

        new_experiment = experiment.clone(deep = True)
        
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
            if 'voltage' in experiment.metadata[channel]:
                del new_experiment.metadata[channel]['voltage']
            
        new_experiment.history.append(self.clone_traits(transient = lambda t: True)) 
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to see if the peak finding is working.
        
        Returns
        -------
        `IView`
            An diagnostic view, call `BeadCalibrationDiagnostic.plot` to 
            see the diagnostic plots
        """

        v = RegistrationDiagnosticView(op = self)
        v.trait_set(**kwargs)
        return v
    

@provides(cytoflow.views.IView)
class RegistrationDiagnosticView(HasStrictTraits):
    """
    A diagnostic view for `RegistrationOp`.
        
    Plots the smoothed histogram of the bead data; the peak locations;
    a scatter plot of the raw bead fluorescence values vs the calibrated unit 
    values; and a line plot of the model that was computed.  Make sure that the
    relationship is linear; if it's not, it likely isn't a good calibration!
    
    Attributes
    ----------
    op : Instance(`BeadCalibrationOp`)
        The operation instance whose diagnostic we're plotting.  Set 
        automatically if you created the instance using 
        `BeadCalibrationOp.default_view`.

    """
    
    # traits   
    id = Constant("cytoflow.view.beadcalibrationdiagnosticview")
    friendly_id = Constant("Bead Calibration Diagnostic")
        
    op = Instance(RegistrationOp)
    channel = Str
    
    def plot(self, experiment):
        """
        Plots the diagnostic view.
        
        Parameters
        ----------
        experiment : `Experiment`
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
            _, hist_bins, hist_smooth = self.op._histograms[channel]
                
            plt.subplot(len(channels), 2, 2 * idx + 1)
            plt.xscale('log')
            plt.xlabel(channel)
            plt.plot(hist_bins[1:], hist_smooth)
            
            plt.axvline(self.op.bead_brightness_threshold, color = 'blue', linestyle = '--' )
            if self.op.bead_brightness_cutoff:
                plt.axvline(self.op.bead_brightness_cutoff, color = 'blue', linestyle = '--' )
            else:
                plt.axvline(experiment.metadata[channel]['range'] * 0.7, color = 'blue', linestyle = '--')                

            if channel in self.op._peaks:
                for peak in self.op._peaks[channel]:
                    plt.axvline(peak, color = 'r')
                    
            if channel in self.op._peaks and channel in self.op._mefs:
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
            
