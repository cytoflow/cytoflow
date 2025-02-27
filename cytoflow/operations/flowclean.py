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
                        Union, Tuple)

import numpy as np
import scipy.stats
import scipy.ndimage.filters
import pandas as pd

from cytoflow.experiment import Experiment
from cytoflow.operations.import_op import Tube
from cytoflow.views import IView, DensityView
import cytoflow.utility as util

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
    Cleanliness is then assessed again. Metadata is added to the `Experiment` for
    each tube, indicating whether it was CLEAN (clean before the operation),
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
        
    crit_continuity : Float (default = 0.1)
        The critical "continuity" -- determines how "different" an adjacent
        segment must be to be for a tube to be flagged as suspicious.
        
    crit_mean_of_means : Float (default = 0.13)
        The critical mean-of-means value to flag a file as needing cleaning --
        indates a large gradual change of fluorescence in all channels over 
        time.
        
    crit_max_of_means : Float (default = 0.15)
        The critical maximum-of-means value used to flag a file as needing 
        cleaning -- indicates a large graduate change of fluorescence in all 
        channels over time.
        
    min_segment_weight : Float (default = 0.95)
               
    detect_worst_channels : Union(Tuple(Int, Int), None) (default = None)
        Should `FlowCutOp` try to detect the worst channels and use them to 
        flag tubes or trim events? If this attribute is defined, it must be
        a 2-tuple of integers, each of which is 0 or greater. The first
        integer is the number of channels to choose using the range of the 
        mean of the bins' fluorescence distribution, and the second
        is the number of channels choose when evaluating the standard
        deviation. ``(1, 2)`` often seems to work well.
        
    measures : List(String) (default = ("5th_percentile", "20th_percentile", "50th_percentile", "80th_percentile", "95th_percentile", "mean", "variance", "skewness") ).
        Which measures should be considered when comparing segments? Must be
        a subset of the default. 
        
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
       and minimum mean) divided by the (2-98th percentile difference).
       
    4. For each channel, compare the mean drift to `crit_max_of_means`, and
       the mean-of-means across all fluorescence channels to `crit_mean_of_means`. 
       If either is greater than the corresponding critical value, flag the tube 
       as needing to be cleaned.
       
    5. For each channel, compare the maximum difference in intensity between 
       adjacent bins to `crit_continuity`. If the maximum difference is greater 
       than the critical value, flag the tube as needing to be cleaned.
       
    6. If the file needs to be cleaned, compute the 8 measures from `measures`
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
    
    segment_size = Int(500)
    density_cutoff = Float(0.05)
    crit_continuity = Float(0.1)
    crit_mean_of_means = Float(0.13)
    crit_max_of_means = Float(0.15)
    
    min_segment_weight = 0.95
    detect_worst_channels = Union(Tuple(Int, Int), None)
    measures = List(Str, value = ("5th_percentile", "20th_percentile", "50th_percentile", "80th_percentile", "95th_percentile", "mean", "variance", "skewness"))

    _tube_bins = Dict(Tube, pd.api.typing.DataFrameGroupBy)    
    _bin_density = Dict(Tube, Instance(np.ndarray))
    _bin_kept = Dict(Tube, Instance(np.ndarray))
    _bin_means = Dict(Tube, Dict(Str, Instance(np.ndarray)))
    _bin_measures = Dict(Tube, Instance(np.ndarray))
    _bin_kept = Dict(Tube, Instance(np.ndarray))
    
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
        
        # TODO - double-check that events in the tube groups are monotonic in the
        # time channel
        
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
        g = experiment.data.groupby(conditions, observed = True)
        
        for tube in experiment.history[0].tubes:
            tube_events = g.get_group(tuple(tube.conditions.values()))
            num_events = len(tube_events)
            num_segments = int(len(tube_events) / self.segment_size)
            segment_size = int(len(tube_events) / num_segments)
            labels = np.repeat(range(0, num_segments), segment_size)
            np.append(labels, [num_segments - 1] * (len(tube_events) - len(labels)))
            self._tube_bins[tube] = tube_events.groupby(labels)
            self._bin_kept[tube] = np.full((num_segments), True)
            self._bin_density[tube] = np.zeros((num_segments))
            self._bin_means[tube] = {channel : np.zeros((num_segments)) for channel in self.channels}
            self._bin_measures[tube] = np.zeros((num_segments))

            # compute density for each bin            
            for bin, events in self._tube_bins[tube]:                
                start_time = events[self.time_channel].iat[0]
                end_time = events[self.time_channel].iat[len(events) - 1]
                assert(end_time >= start_time)
                self._bin_density[tube][bin] = len(events) / (end_time - start_time)
              
            # find the quantile for the density cutoff. 
            density_cutoff_quantile = np.quantile(self._bin_density[tube], (self.density_cutoff))
            
            # trim the low-density bins
            for bin, events in self._tube_bins[tube]:
                if self._bin_density[tube][bin] <= density_cutoff_quantile:
                    self._bin_kept[tube][bin] = False
                    
            # compute means of the fluorescence channels' bins
            for bin, events in self._tube_bins[tube]:
                for channel in self.channels:
                    self._bin_means[tube][channel][bin] = self._scale[channel](events[channel]).mean() 
            
                 
            
            
         
            
            
        
        
    
    