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
cytoflow.operations.flowclean
---------------------------

The `flowclean` module has two classes:

`FlowCleanOp` -- gates an `Experiment` based on a variation in fluorescence
channels over time.

`FlowCleanView` -- diagnostic views for FlowCleanOp.

"""

from traits.api import (HasStrictTraits, Str, Dict, Any, Instance, 
                        Constant, List, provides, Array, Int, Float,
                        Union, Tuple, Bool)

import math
import numpy as np
import scipy.stats
import scipy.ndimage.filters
import scipy.signal
import scipy.optimize
import sklearn.neighbors
import sklearn.mixture
import statsmodels.nonparametric.bandwidths
import pandas as pd
import matplotlib.pyplot as plt
from warnings import warn

from cytoflow.experiment import Experiment
from cytoflow.operations.import_op import Tube
from cytoflow.views import IView, DensityView, ScatterplotView
import cytoflow.utility as util
import cytoflow.views
from .base_op_views import OpView


from .i_operation import IOperation
from .base_op_views import By2DView, AnnotatingView

@provides(IOperation)
class FlowCleanOp(HasStrictTraits):
    """
    This module gates events from time slices whose density is low or
    whose events' fluorescence intensity varies substantially from other slices. 
    This is often due to a bubble or transient clog in the flow cell.
    
    The operation assesses whether a tube is "clean" using an algorithm 
    described below. If the tube is already clean, only low-density slices are 
    removed. If the tube is not clean, then a cleaning is attempted, removing
    slices that are substantially statistically different than the majority.
    Cleanliness is then assessed again. After calling `estimate()`, `tube_status` 
    is set for each tube, indicating whether it was CLEAN (clean before the operation),
    CLEANED (clean after the gated events are dropped), or UNCLEAN (still unclean 
    after the gated events are dropped.) Additional metadata is also added about the 
    results of the cleaning algorithm.
    
    This operation is applied to every tube independently -- that is, to every
    subset of events with a unique combination of experimental metadata 
    (as determined by the experiment's `Experiment.metadata`). Thus, there
    is no ``by`` attribute, as with many other data-driven gating operations.
    
    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column.
    
    time_channel : Str
        The channel that represents time -- often ``HDR-T`` or similar.
        
    channels : Dict(Str : {"linear", "logicle", "log"})
        Which fluorescence channel or channels are analyzed for variation,
        and how should they be scaled before cleaning.
    
    segment_size : Int (default = 500)
        The number of events in each bin in the analysis.

    density_cutoff : Float (default = 0.05)
        The proportion of low-density bins to filter.
        
    max_discontinuity : Float (default = 0.1)
        The critical "continuity" -- determines how "different" an adjacent
        segment must be to be for a tube to be flagged as suspicious.

    max_drift : Float (default = 0.15)
        The maximum any individual channel can drift before being flagged as
        needing cleaning.
        
    max_mean_drift : Float (default = 0.13)
        The maximum the mean of all channels' drift can be before the tube is
        flagged as needing to be cleaned.
        
    min_segment_weight : Float (default = 0.95)
               
    detect_worst_channels : Union(Tuple(Int, Int), None) (default = None)
        Should `FlowCutOp` try to detect the worst channels and use them to 
        flag tubes or trim events? If this attribute is defined, it must be
        a 2-tuple of integers, each of which is 0 or greater. The first
        integer is the number of channels to choose using the range of the 
        mean of the bins' fluorescence distribution, and the second
        is the number of channels choose when evaluating the standard
        deviation. ``(1, 2)`` often seems to work well.
        
    measures : List(String) (default = ("5th percentile", "20th percentile", "50th percentile", "80th percentile", "95th percentile", "mean", "variance", "skewness") ).
        Which measures should be considered when comparing segments? Must be
        a subset of the default. 
        
    force_clean : Bool (default = False)
        If ``True``, force cleaning even if the tube passes the original quality checks.
        Remember, the operation **always** removes low-density bins.
        
    TODO - document metadata
    
    Notes
    -----
    
    This is a fairly direct implementation of the flowCut algorithm in the 
    Bioconductor package ``flowCut``, by Justin Meskas and Sherrie Wang. 
    The Bioconductor package page is 
    https://www.bioconductor.org/packages/release/bioc/html/flowCut.html.
    
    The algorithm works in the following way:
    
    1. Bin the events along the time they were collected. The bin size is 
       determined by `segment_size`.
       
    2. Compute the density (events per unit time) of each bin, and remove the 
       lowest `density_cutoff` proportion of them.
       
    3. For each channel, compute the mean intensity in each bin (after scaling 
       the data), then compute the mean drift and the differences between 
       adjacent bins. The mean drift is the (difference between the maximum 
       and minimum mean) divided by the (98th - 2nd percentile difference). If
       the mean drift is greater than `max_channel_drift`, flag the tube as 
       needing to be cleaned.
       
    4. Compute the mean drift across all channels. If the mean drift is greater
       than `max_mean_channel_drift`, flag the tube as needing to be cleaned.
       
    5. For each channel, see if any adjacent bins have differences in their mean
       fluorescence more than `max_discontinuity`. If so, flag the tube as
       needing to be cleaned.
       
    6. If the file needs to be cleaned, compute the measures from `measures`
       for each bin in each channel, then sum them over all the channels to obtain 
       a single number for each bin. Smooth this distribution using 
       `scipy.signal.savgol_filter`, then find peaks with 
       `scipy.signal.find_peaks_cwt`. (This bit is different than the canonical 
       flowCut algorithm.) Finally, compute a gaussian mixture model using the peaks
       as the means. Choose the largest peak as the set of bins to keep, and discard
       bins that don't have a weight of `min_segment_weight` in that component.
       
    7. Re-compute the drift in each channel and add it to the experiments' metadata,
       along a flag about whether the tube was CLEAN, CLEANED, or UNCLEAN.
       
       
   """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.flowcut')
    friendly_id = Constant("FlowCut Cleaning")
    
    name = Str
    time_channel = Str
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    
    tube_status = Dict(Tube, Str)
    
    segment_size = Int(500)
    density_cutoff = Float(0.05)
    max_drift = Float(0.15)
    max_mean_drift = Float(0.13)
    max_discontinuity = Float(0.1)
    
    min_segment_probability = 0.05
    
    detect_worst_channels_range = Int(0)
    detect_worst_channels_sd = Int(0)
    measures = List(Str, value = ("5th percentile", "20th percentile", "50th percentile", "80th percentile", "95th percentile", "mean", "variance", "skewness"))
    force_clean = Bool(False)

    _tube_bins = Dict(Tube, pd.api.typing.DataFrameGroupBy)    
    _bin_kept = Dict(Tube, Instance(np.ndarray))
    _bin_measures = Dict(Tube, Instance(np.ndarray))
    _tube_channels = Dict(Tube, List(Str))
    _channel_stats = Dict(Tube, Instance(pd.DataFrame))
    
    _kde = Dict(Tube, Any)
    _pdf = Dict(Tube, Any)
    _peaks = Dict(Tube, Any)
    
    _scale = Dict(Str, Instance(util.IScale), transient = True)
    
    def estimate(self, experiment, subset = None):
        # check that subset is None
        if subset is not None:
            raise util.CytoflowOpError(None,
                                       "'subset' must be None for FlowCutOp.estimate().")
            
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
        if len(self.channels) == 0:
            raise util.CytoflowOpError('channels',
                                       "Must set at least one channel")

        if len(self.channels) != len(set(self.channels)):
            raise util.CytoflowOpError('channels', 
                                       "Must not duplicate channels")

        if self.time_channel not in experiment.data:
            raise util.CytoflowOpError('time_channel',
                                       "Time channel {} not found in experiment"
                                       .format(self.time_channel))

        for c in self.channels:
            if c not in experiment.data:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not found in the experiment"
                                      .format(c))
                
        for c in self.scale:
            if c not in self.channels:
                raise util.CytoflowOpError('channels',
                                           "Scale set for channel {0}, but it isn't "
                                           "in the 'channels'"
                                           .format(c))     
                
        if self.detect_worst_channels_range and self.detect_worst_channels_range > len(self.channels):
            raise util.CytoflowOpError('detect_worst_channels_range',
                                       "detect_worst_channels_range can't be "
                                       "more than {}".format(length(self.channels)))   
            
        if self.detect_worst_channels_sd and self.detect_worst_channels_sd > len(self.channels):
            raise util.CytoflowOpError('detect_worst_channels_sd',
                                       "detect_worst_channels_sd can't be "
                                       "more than {}".format(length(self.channels)))   
        
        # instantiate scales. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        for c in self.channels:
            if c in self.scale:
                self._scale[c] = util.scale_factory(self.scale[c], experiment, channel = c)
#                 if self.scale[c] == 'log':
#                     self._scale[c].mode = 'mask'
            else:
                self._scale[c] = util.scale_factory(util.get_default_scale(), experiment, channel = c)
        
        conditions = list(experiment.history[0].tubes[0].conditions.keys())
        if len(experiment.history[0].tubes) > 1:
            g = experiment.data.groupby(conditions, observed = True)
        
        for tube in experiment.history[0].tubes:
            if len(experiment.history[0].tubes) > 1:
                tube_events = g.get_group(tuple(tube.conditions.values()))
            else:
                tube_events = experiment.data.copy(deep = True)
               
            # check that the events for a tube are monotonic in the time channel! 
            dx = np.diff(tube_events[self.time_channel])
            if not np.all(dx >= 0):
                raise util.CytoflowOpError(None,
                                           "Events in tube {} do not have monotonically "
                                           "increasing time. Please log a bug, and include "
                                           "the FCS file that gave you the error."
                                           .format(tube.file))
                
            for c in self.channels:
                tube_events.loc[:, c] = self._scale[c](tube_events[c])
            num_segments = int(len(tube_events) / self.segment_size)
            segment_size = int(len(tube_events) / num_segments)
            labels = np.repeat(range(0, num_segments), segment_size)
            np.append(labels, [num_segments - 1] * (len(tube_events) - len(labels)))
            self._tube_bins[tube] = tube_events.groupby(labels)
            self._bin_kept[tube] = np.full((num_segments), True)
            self._bin_measures[tube] = np.zeros((num_segments))
            self._channel_stats[tube] = pd.DataFrame(index = self.channels,
                                                     columns = ['Bin Mean Range', 
                                                                'Bin Mean SD',
                                                                'Drift Pre',
                                                                'Drift Post',
                                                                'Max Discontinuity Pre',
                                                                'Max Discontinuity Post'])   
            channel_stats = self._channel_stats[tube]

            self.tube_status[tube] = "CLEAN"

            # compute density for each bin
            bin_density = np.zeros((num_segments))
            
            for bin, events in self._tube_bins[tube]:                
                start_time = events[self.time_channel].iat[0]
                end_time = events[self.time_channel].iat[len(events) - 1]
                assert(end_time >= start_time)
                bin_density[bin] = len(events) / (end_time - start_time)
              
            # find the quantile for the density cutoff. 
            density_cutoff_quantile = np.quantile(bin_density, (self.density_cutoff))
            
            # trim the low-density bins
            for bin, events in self._tube_bins[tube]:
                if bin_density[bin] <= density_cutoff_quantile:
                    self._bin_kept[tube][bin] = False
                    
            # compute bin means
            bin_means = {channel : np.zeros((num_segments)) for channel in self.channels}
            kept_bin_means = {}
            for channel in self.channels:
                for bin, events in self._tube_bins[tube]:
                    bin_means[channel][bin] = events[channel].mean()
                kept_bin_means[channel] = np.compress(self._bin_kept[tube], bin_means[channel])
                channel_stats.loc[channel, 'Bin Mean Range'] = np.ptp(kept_bin_means[channel])
                channel_stats.loc[channel, 'Bin Mean SD'] = np.std(kept_bin_means[channel])

            # find the "worst" channels
            worst_channels_range = []
            if self.detect_worst_channels_range:
                worst_channels_range = list(channel_stats.sort_values(by = 'Bin Mean Range').index[-1 * self.detect_worst_channels_range :])
                
            worst_channels_sd = []
            if self.detect_worst_channels_sd:
                worst_channels_sd = list(channel_stats.sort_values(by = 'Bin Mean SD').index[-1 * self.detect_worst_channels_sd :])
                
            if worst_channels_range and not worst_channels_sd:
                channels = worst_channels_range
            elif worst_channels_sd and not worst_channels_range:
                channels = worst_channels_sd
            elif worst_channels_range and worst_channels_sd:
                channels = list(set(worst_channels_range).union(set(worst_channels_sd)))
            else:
                channels = self.channels
                
            self._tube_channels[tube] = channels
                
            # compute each channel's drift and see if it is in spec or whether
            # the tube needs cleaning
            for channel in channels:
                drift = (np.max(kept_bin_means[channel]) - np.min(kept_bin_means[channel])) / (tube_events[channel].quantile(0.98) - tube_events[channel].quantile(0.02))
                channel_stats.loc[channel, "Drift Pre"] = drift
                if drift > self.max_drift:
                    self.tube_status[tube] = "UNCLEAN"

            # compute the mean of the means and see whether it's in spec, or
            # the tube needs to be cleaned
            mean_drift = channel_stats.loc[:, "Drift Pre"].mean(skipna = True)
            if mean_drift > self.max_mean_drift:
                self.tube_status[tube] = "UNCLEAN"
            
            # check for discontinuities in the channel means
            for channel in channels:
                max_discontinuity = 0.0
                for i in range(1, len(kept_bin_means[channel])):
                    d = abs(kept_bin_means[channel][i] - kept_bin_means[channel][i-1]) / kept_bin_means[channel][i-1]
                    if d > max_discontinuity:
                        max_discontinuity = d
                channel_stats.loc[channel, "Max Discontinuity Pre"] = max_discontinuity
                    
                if max_discontinuity > self.max_discontinuity:
                    self.tube_status[tube] = "UNCLEAN"
                    
            if self.tube_status[tube] == "CLEAN" and not self.force_clean:
                continue
            
            # time for cleaning. first, compute all the measures and sum them
            measure_sum = np.zeros((num_segments))
            for bin, events in self._tube_bins[tube]:
                for channel in channels:
                    if '5th percentile' in self.measures:
                        measure_sum[bin] += events[channel].quantile(0.05)
                    
                    if '20th percentile' in self.measures:
                        measure_sum[bin] += events[channel].quantile(0.20)
                    
                    if '50th percentile' in self.measures:
                        measure_sum[bin] += events[channel].quantile(0.50)
                    
                    if '80th percentile' in self.measures:
                        measure_sum[bin] += events[channel].quantile(0.80)
                    
                    if '95th percentile' in self.measures:
                        measure_sum[bin] += events[channel].quantile(0.95)
                    
                    if 'mean' in self.measures:
                        measure_sum[bin] += events[channel].mean()
                    
                    if 'variance' in self.measures:
                        measure_sum[bin] += events[channel].var()
                    
                    if 'skewness' in self.measures:
                        measure_sum[bin] += events[channel].skew()
                        
            # kernel density estimator
            bandwidth = statsmodels.nonparametric.bandwidths.bw_scott(measure_sum, "gaussian")
            support_min = measure_sum.min() - bandwidth * 3
            support_max = measure_sum.max() + bandwidth * 3
            support = np.linspace(support_min, support_max, 100)
            kde = sklearn.neighbors.KernelDensity(kernel = "gaussian", bandwidth = bandwidth).fit(measure_sum[:, np.newaxis])
            log_density = kde.score_samples(support[:, np.newaxis])
            density = np.exp(log_density)
            self._kde[tube] = (support, density)

            # find peaks in the kde
            peaks, peak_props = scipy.signal.find_peaks(density,
                                                        prominence = 0)
            peaks = [support[x] for x in peaks]
            self._peaks[tube] = peaks
            
            if len(peaks) == 0:
                warn("No peaks found for {}".format(tube.file),
                     util.CytoflowOpWarning)
                continue

            # fit a gaussian with the mean at the maximum peak
            max_peak_idx = np.argmax(peak_props['prominences'])
            max_peak = self._peaks[tube][max_peak_idx]            
            pdf = lambda x, sd: scipy.stats.norm.pdf(x, loc = max_peak, scale = sd)
            opt_sd = scipy.optimize.curve_fit(pdf, support, density)[0][0]

            # compute the probability of observing each element in measure_sum
            self._pdf[tube] = (max_peak, opt_sd)
            measure_probability = scipy.stats.norm.pdf(measure_sum, loc = max_peak, scale = opt_sd)
            
            # remove low-probability bins
            for bin, _ in self._tube_bins[tube]:
                if measure_probability[bin] < self.min_segment_probability:
                    self._bin_kept[tube][bin] = False
                    
            kept_bin_means = {}
            for channel in channels:
                kept_bin_means[channel] = np.compress(self._bin_kept[tube], bin_means[channel])

            # now, re-check the tube with the kept bins
            self.tube_status[tube] = "CLEANED"

            # compute each channel's drift and see if it is in spec or whether
            # the tube needs cleaning
            for channel in channels:
                drift = (np.max(kept_bin_means[channel]) - np.min(kept_bin_means[channel])) / (tube_events[channel].quantile(0.98) - tube_events[channel].quantile(0.02))
                channel_stats.loc[channel, "Drift Post"] = drift
                if drift > self.max_drift:
                    self.tube_status[tube] = "UNCLEAN"

            # compute the mean of the means and see whether it's in spec, or
            # the tube needs to be cleaned
            mean_drift = channel_stats.loc[:, "Drift Post"].mean(skipna = True)
            if mean_drift > self.max_mean_drift:
                self.tube_status[tube] = "UNCLEAN"
            
            # check for discontinuities in the channel means
            for channel in channels:
                max_discontinuity = 0.0
                for i in range(1, len(kept_bin_means[channel])):
                    d = abs(kept_bin_means[channel][i] - kept_bin_means[channel][i-1]) / kept_bin_means[channel][i-1]
                    if d > max_discontinuity:
                        max_discontinuity = d
                channel_stats.loc[channel, "Max Discontinuity Post"] = max_discontinuity
                    
                if max_discontinuity > self.max_discontinuity:
                    self.tube_status[tube] = "UNCLEAN"
                    
    def apply(self, experiment):
        """
        Creates a new condition based on whether the event was dropped by the
        cleaning procedure in `estimate()` -- essentially, a "gate" that cleans
        each tube's data
        
        Parameters
        ----------
        experiment : `Experiment`
            the `Experiment` to apply the gate to.
            
        Returns
        -------
        `Experiment`
            a new `Experiment` with the new condition.
        """
            
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the gate's name "
                                       "before applying it!")
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name))  

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError('name',
                                       "Experiment already has a column named {0}"
                                       .format(self.name))
            
        if not self._tube_bins.keys():
            raise util.CytoflowOpError(None,
                                       "No tubes were analyzed. Did you forget to "
                                       "call estimate()?")
            
        if set(self._tube_bins.keys()) != set(experiment.history[0].tubes):
            raise util.CytoflowOpError(None,
                                       "estimate() seems to have been called on "
                                       "a different Experiment than apply() is?")
            
        event_assignments = pd.Series([True] * len(experiment), dtype = "bool")
        for tube, tube_bins in self._tube_bins.items():
            for bin, events in tube_bins:
                 if not self._bin_kept[tube][bin]:
                     event_assignments.loc[events.index] = False
                    
        new_experiment = experiment.clone(deep = False)
        new_experiment.add_condition(self.name, "bool", event_assignments)
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment
                                
                    
    def default_view(self, **kwargs):
        """
        Returns diagnostic plots of `FlowCutOp`'s actions.
        
        Returns
        -------
        `IView`
            an `IView`, call `plot` to see the diagnostic plot.
        """
        
        v = FlowCleanDiagnostic(op = self)
        v.trait_set(**kwargs)
        return v
                    
            
@provides(cytoflow.views.IView)
class FlowCleanDiagnostic(HasStrictTraits):
    """
    A diagnostic view for `FlowCleanOp`.
    
    Plots.... TODO
    
    Attributes
    ----------
    op : Instance(`FlowCleanOp`)
        The operation instance whose diagnostic we're plotting. Set automatically
        if you create the instance using `FlowCleanOp.default_view`.
    """

    id = Constant("edu.mit.synbio.cytoflow.view.flowcleanview")
    friendly_id = Constant("FlowClean Diagnostic")
    
    op = Instance(FlowCleanOp)

    
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce -- in this case, the `Tube` filenames.  The values returned 
        can be passed to the ``plot_name`` keyword of `plot`.
        
        Parameters
        ----------
        experiment : `Experiment`
            The `Experiment` that will be producing the plots.
        """
        pass
        
    
    def plot(self, experiment, **kwargs):
        """
        Make a diagnostic plot for a `FlowCleanView` operation.
        
        Parameters
        ----------
        plot_name : Str
            The tube filename to plot. The filenames can also be retrieved from
            `enum_plots`.
                    
        alpha : float (default = 0.25)
            The alpha blending value, between 0 (transparent) and 1 (opaque).
            
        s : int (default = 0.5)
            The size in points^2.
            
        marker : a matplotlib marker style, usually a string
            Specfies the glyph to draw for each point on the scatterplot.
            See `matplotlib.markers <http://matplotlib.org/api/markers_api.html#module-matplotlib.markers>`_ for examples.  Default: 'o'
            
        
        Notes
        -----
        Other ``kwargs`` are passed to `matplotlib.pyplot.scatter <https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.scatter.html>`_
        """
            
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        plot_name = kwargs.pop('plot_name', None)
        if plot_name is None:
            raise util.CytoflowViewError('plot_name',
                                         "'plot_name' must be a tube filename")
            
        if plot_name not in [tube.file for tube in experiment.history[0].tubes]:
            raise util.CytoflowViewError('plot_name',
                                         "'plot_name' must be a tube in `experiment`")
            
        kwargs.setdefault('alpha', 0.25)
        kwargs.setdefault('s', 0.5)
        kwargs.setdefault('marker', 'o')
        kwargs.setdefault('antialiased', True)

        tube = next((tube for tube in experiment.history[0].tubes if tube.file == plot_name))
        assert(tube in experiment.history[0].tubes)
        if tube not in self.op.tube_status:
            raise util.CytoflowViewError(None,
                                         "Tube {} was not found in the operation -- did you call estimate()?"
                                         .format(tube.file))
        
        num_plots = len(self.op._tube_channels[tube])
        if tube in self.op._kde:
            num_plots += 1
        nrow = math.ceil(num_plots / 2)
                            
        if len(experiment.history[0].tubes) > 1:
            experiment = experiment.subset(list(tube.conditions.keys()), tuple(tube.conditions.values()))
        
        for idx, channel in enumerate(self.op._tube_channels[tube]):
            
            if self.op.tube_status[tube] == "CLEANED" or self.op.tube_status[tube] == "UNCLEAN":
                title = "{} : {:.3f} - {:.3f} / {:.3f} - {:.3f}" \
                             .format(channel, 
                                     self.op._channel_stats[tube].loc[channel, "Drift Pre"],
                                     self.op._channel_stats[tube].loc[channel, "Drift Post"],
                                     self.op._channel_stats[tube].loc[channel, "Max Discontinuity Pre"],
                                     self.op._channel_stats[tube].loc[channel, "Max Discontinuity Post"])
            else:
                title = "{} : {:.3f} / {:.3f}" \
                             .format(channel, 
                                     self.op._channel_stats[tube].loc[channel, "Drift Pre"],
                                     self.op._channel_stats[tube].loc[channel, "Max Discontinuity Pre"])
            ax = plt.subplot(nrow, 2, idx + 1, title = title)

            # TODO - subset by _kept_bins instead of assuming that `experiment` is the result
            # of this op's apply() call
            
            for bin, events in self.op._tube_bins[tube]:                
                plt.scatter(x = events[self.op.time_channel],
                            y = self.op._scale[channel](events[channel]),
                            c = 'tab:blue' if self.op._bin_kept[tube][bin] else 'tab:orange',
                            **kwargs)         

        if tube in self.op._kde:
            ax = plt.subplot(nrow, 2, num_plots, title = "Measures Distribution")
            support, density = self.op._kde[tube]
            plt.plot(support, density)
            for peak in self.op._peaks[tube]:
                plt.axvline(peak, color = 'r')
        
            if tube in self.op._pdf:
                loc, scale = self.op._pdf[tube]
                plt.plot(support, 
                         scipy.stats.norm.pdf(support, loc = loc, scale = scale),
                         color = 'r',
                         linestyle = 'dotted')
            support, pdf = self.op._pdf[tube]
            plt.plot(support, pdf, color = 'r')
                        

        plt.tight_layout(pad = 0.8)


        
            
        
         
            
            
        
        
    
    