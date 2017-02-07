#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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
Created on Sep 18, 2015

@author: brian
'''

from __future__ import division, absolute_import


from traits.api import (HasStrictTraits, Str, CStr, provides,
                        Instance, DelegatesTo, Constant, Int)
import numpy as np
import bottleneck as bn

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class BinningOp(HasStrictTraits):
    """
    Bin data along an axis.
    
    This operation creates equally spaced bins (in linear or log space)
    along an axis and adds a metadata column assigning each event to a bin.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    channel : Str
        The name of the channel along which to bin.

    scale : Enum("linear", "log", "logicle)
        Make the bins equidistant along what scale?
        
    num_bins = Int
        The number of bins to make.  Must set either `num_bins` or `bin_width`.
        If both are defined, `num_bins` takes precedence.
        
    bin_width = Float
        The width of the bins.  Must set either `num_bins` or `bin_width`.  If
        `scale` is `log`, `bin_width` is in log-10 units; if `scale` is
        `logicle`, and error is thrown because the units are ill-defined.
        If both `num_bins` and `bin_width` are defined, `num_bins` takes 
        precedence. 
        
    bin_count_name : Str
        If `bin_count_name` is set, add another piece of metadata when calling
        `apply()` that contains the number of events in the bin that this event
        falls in.  Useful for filtering bins by # of events.
        
    Examples
    --------
    >>> bin_op = flow.BinningOp(name = "CFP_Bin",
    ...                         channel = "PE-Tx-Red-YG-A",
    ...                         scale = "linear",
    ...                         num_bins = 40)
    >>> ex5_binned = bin_op.apply(ex5)

    >>> h.huefacet = "CFP_Bin"
    >>> h.plot(ex5_binned)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.binning')
    friendly_id = Constant("Binning")
    
    name = CStr()
    bin_count_name = CStr()
    channel = Str()
    num_bins = util.PositiveInt(0, allow_zero = True)
    bin_width = util.PositiveFloat(0, allow_zero = True)
    scale = util.ScaleEnum
    
    _max_num_bins = Int(100)

    def apply(self, experiment):
        """Applies the binning to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.low and
            less than self.high; it is False otherwise.
        """
        if not experiment:
            raise util.CytoflowOpError("no experiment specified")
        
        if not self.name:
            raise util.CytoflowOpError("name is not set")
        
        if self.name in experiment.data.columns:
            raise util.CytoflowOpError("name {0} is in the experiment already"
                                  .format(self.name))
            
        if self.bin_count_name and self.bin_count_name in experiment.data.columns:
            raise util.CytoflowOpError("bin_count_name {0} is in the experiment already"
                                  .format(self.bin_count_name))
        
        if not self.channel:
            raise util.CytoflowOpError("channel is not set")
        
        if self.channel not in experiment.data.columns:
            raise util.CytoflowOpError("channel {0} isn't in the experiment"
                                  .format(self.channel))
              
        if not self.num_bins and not self.bin_width:
            raise util.CytoflowOpError("must set either bin number or width")
        
        if self.bin_width \
           and not (self.scale == "linear" or self.scale == "log"):
            raise util.CytoflowOpError("Can only use bin_width with linear or log scale") 
        
        scale = util.scale_factory(self.scale, experiment, channel = self.channel)
        scaled_data = scale(experiment.data[self.channel])
            
        scaled_min = bn.nanmin(scaled_data)
        scaled_max = bn.nanmax(scaled_data)
        
        num_bins = self.num_bins if self.num_bins else \
                   (scaled_max - scaled_min) / self.bin_width
                   
        if num_bins > self._max_num_bins:
            raise util.CytoflowOpError("Too many bins! To increase this limit, "
                                       "change _max_num_bins (currently {})"
                                       .format(self._max_num_bins))

        scaled_bins = np.linspace(start = scaled_min, stop = scaled_max,
                                  num = num_bins)
        
        if len(scaled_bins) < 2:
            raise util.CytoflowOpError("Must have more than one bin")
        
        # put the data in bins
        bin_idx = np.digitize(scaled_data, scaled_bins[1:-1])
        
        # now, back into data space
        bins = scale.inverse(scaled_bins)
            
        new_experiment = experiment.clone()
        new_experiment.add_condition(self.name, "float", bins[bin_idx])
        
        # if we're log-scaled (for example), don't label data that isn't
        # showable on a log scale!
#         new_experiment.data.ix[np.isnan(scaled_data), self.name] = np.nan
#         new_experiment.data.dropna(inplace = True)
        
        # keep track of the bins we used, for prettier plotting later.
        new_experiment.metadata[self.name]["bin_scale"] = self.scale
        new_experiment.metadata[self.name]["bins"] = bins
        
        if self.bin_count_name:
            # TODO - this is a HUGE memory hog?!
            # TODO - fix this, then turn it on by default
            agg_count = new_experiment.data.groupby(self.name).count()
            agg_count = agg_count[agg_count.columns[0]]
            
            # have to make the condition a float64, because if we're in log
            # space there may be events that have NaN as the bin number.
            
            new_experiment.add_condition(
                self.bin_count_name,
                "float64",
                new_experiment[self.name].map(agg_count))
        
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment
    
    def default_view(self, **kwargs):
        return BinningView(op = self, **kwargs)
    
@provides(cytoflow.views.IView)
class BinningView(cytoflow.views.HistogramView):
    """Plots a histogram of the current binning op, with the bins set to
       the hue facet.
       
    Attributes
    ----------
    op: Instance(BinningOp)
        the BinningOp we're viewing
       
    subset : Str
        The string passed to `Experiment.query()` to subset the data before
        plotting
        
    Examples
    --------
    >>> b = BinningOp(name = "Y2-A-Bin",
    ...               channel = "Y2-A",
    ...               num_bins = 10,
    ...               scale = "linear")
    >>> b.default_view().plot(ex2)
    """
     
    id = Constant('edu.mit.synbio.cytoflow.views.binning')
    friendly_id = Constant('Binning Setup')
    
    op = Instance(IOperation)   
    name = DelegatesTo('op')
    channel = DelegatesTo('op')
    scale = DelegatesTo('op')
    huefacet = DelegatesTo('op', 'name')
    
    def plot(self, experiment, **kwargs):
                
        experiment = self.op.apply(experiment)
        cytoflow.HistogramView.plot(self, experiment, **kwargs)

