#!/usr/bin/env python3.4
# coding: latin-1

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
Created on Dec 16, 2015

@author: brian
'''

from warnings import warn
from itertools import product

import matplotlib.pyplot as plt

from traits.api import (HasStrictTraits, Str, CStr, Dict, Any, Instance, Bool, 
                        Constant, List, provides, DelegatesTo, Property, Array)

import matplotlib as mpl
import matplotlib.colors as colors
import numpy as np
import scipy.stats
import scipy.ndimage.filters
# from sklearn import mixture
# from scipy import linalg
# from scipy import stats
import pandas as pd
import seaborn as sns

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation
from .base_op_views import By2DView

@provides(IOperation)
class DensityGateOp(HasStrictTraits):
    """
    This module computes a gate based on a 2D density plot.  The user chooses
    what proportion of cells to keep, and the module creates a gate that selects
    that proportion of cells in the highest-density bins of the 2D density
    histogram.
    
    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    xchannel : Str
        The X channel to apply the mixture model to.
        
    ychannel : Str
        The Y channel to apply the mixture model to.

    xscale : Enum("linear", "logicle", "log") (default = "linear")
        Re-scale the data on the X acis before fitting the data?  

    yscale : Enum("linear", "logicle", "log") (default = "linear")
        Re-scale the data on the Y axis before fitting the data?  
        
    keep : Float (default = 0.9)
        What proportion of events to keep?  Must be positive.
        
    bins : Int (default = 100)
        How many bins should there be on each axis?  Must be positive.
        
    min_quantile : Float (default = 0.001)
        Clip values below this quantile
        
    max_quantile : Float (default = 1.0)
        Clip values above this quantile

    sigma : Float (default = 1.0)
        What standard deviation to use for the gaussian blur?
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will fit the model 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
        
    Notes
    -----
    This gating method was developed by John Sexton, in Jeff Tabor's lab at
    Rice University.  
    
    From http://taborlab.github.io/FlowCal/fundamentals/density_gate.html,
    the method is as follows:
    
    1. Determines the number of events to keep, based on the user specified 
       gating fraction and the total number of events of the input sample.
       
    2. Divides the 2D channel space into a rectangular grid, and counts the 
       number of events falling within each bin of the grid. The number of 
       counts per bin across all bins comprises a 2D histogram, which is a 
       coarse approximation of the underlying probability density function.
       
    3. Smoothes the histogram generated in Step 2 by applying a Gaussian Blur. 
       Theoretically, the proper amount of smoothing results in a better 
       estimate of the probability density function. Practically, smoothing 
       eliminates isolated bins with high counts, most likely corresponding to 
       noise, and smoothes the contour of the gated region.
       
    4. Selects the bins with the greatest number of events in the smoothed 
       histogram, starting with the highest and proceeding downward until the 
       desired number of events to keep, calculated in step 1, is achieved.
    
    Examples
    --------
    
    >>> density_op = DensityGateOp(name = "Density",
    ...                            xchannel = "V2-A",
    ...                            ychannel = "Y2-A",
    ...                            keep = 0.7)
    >>> density_op.estimate(ex2)
    >>> density_op.default_view().plot(ex2)
    >>> ex3 = density_op.apply(ex2)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.density')
    friendly_id = Constant("Density Gate")
    
    name = CStr()
    xchannel = Str()
    ychannel = Str()
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    keep = util.PositiveFloat(0.9, allow_zero = False)
    bins = util.PositiveInt(100, allow_zero = False)
    min_quantile = util.PositiveFloat(0.001, allow_zero = True)
    max_quantile = util.PositiveFloat(1.0, allow_zero = False)
    sigma = util.PositiveFloat(1.0, allow_zero = False)
    by = List(Str)
        
    _xscale = Instance(util.IScale, transient = True)
    _yscale = Instance(util.IScale, transient = True)
    
    _xbins = Array(transient = True)
    _keep_xbins = Dict(Any, Array, transient = True)
    _ybins = Array(transient = True)
    _keep_ybins = Dict(Any, Array, transient = True)
    _histogram = Dict(Any, Array, transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the Gaussian mixture model parameters
        """
        
        if experiment is None:
            raise util.CytoflowOpError("No experiment specified")

        if self.xchannel not in experiment.data:
            raise util.CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.xchannel))
            
        if self.ychannel not in experiment.data:
            raise util.CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.ychannel))
            
        if self.max_quantile > 1.0 or self.min_quantile > 1.0:
            raise util.CytoflowOpError("min_quantile and max_quantile must be <= 1.0")
               
        if not (self.max_quantile > self.min_quantile):
            raise util.CytoflowOpError("max_quantile must be > min_quantile")
        
        if self.sigma < 0.0:
            raise util.CytoflowOpError("sigma must be >= 0.0")
        
        if self.keep > 1.0:
            raise util.CytoflowOpError("keep must be <= 1.0")

        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))
            if len(experiment.data[b].unique()) > 100: #WARNING - magic number
                raise util.CytoflowOpError("More than 100 unique values found for"
                                      " aggregation metadata {0}.  Did you"
                                      " accidentally specify a data channel?"
                                      .format(b))
                
        if subset:
            try:
                experiment = experiment.query(subset)
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(subset))
                
            if len(experiment) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(subset))
                
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda x: True)
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        self._xscale = xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)
        self._yscale = yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
        

        xlim = (xscale.clip(experiment[self.xchannel].quantile(self.min_quantile)),
                xscale.clip(experiment[self.xchannel].quantile(self.max_quantile)))
                  
        ylim = (yscale.clip(experiment[self.ychannel].quantile(self.min_quantile)),
                yscale.clip(experiment[self.ychannel].quantile(self.max_quantile)))
        
        self._xbins = xbins = xscale.inverse(np.linspace(xscale(xlim[0]), 
                                                         xscale(xlim[1]), 
                                                         self.bins))
        self._ybins = ybins = yscale.inverse(np.linspace(yscale(ylim[0]), 
                                                         yscale(ylim[1]), 
                                                         self.bins))
                    
        for group, group_data in groupby:
            if len(group_data) == 0:
                raise util.CytoflowOpError("Group {} had no data"
                                           .format(group))

            h, _, _ = np.histogram2d(group_data[self.xchannel], 
                                     group_data[self.ychannel], 
                                     bins=[xbins, ybins])
            
            h = scipy.ndimage.filters.gaussian_filter(h, sigma = self.sigma)
            self._histogram[group] = h
            
            i = scipy.stats.rankdata(h, method = "ordinal") - 1
            i = np.unravel_index(np.argsort(-i), h.shape)
            
            goal_count = self.keep * len(group_data)
            curr_count = 0
            num_bins = 0

            while(curr_count < goal_count and num_bins < i[0].size):
                curr_count += h[i[0][num_bins], i[1][num_bins]]
                num_bins += 1
            
            self._keep_xbins[group] = i[0][0:num_bins]
            self._keep_ybins[group] = i[1][0:num_bins]
            
    def apply(self, experiment):
        """
        Assigns new metadata to events using the mixture model estimated
        in `estimate`.
        """
            
        if experiment is None:
            raise util.CytoflowOpError("No experiment specified")
        
        if not self.xchannel:
            raise util.CytoflowOpError("Must set X channel")

        if not self.ychannel:
            raise util.CytoflowOpError("Must set Y channel")
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError("Experiment already has a column named {0}"
                                  .format(self.name))
        
        if not (self._xbins.size and self._ybins.size and self._keep_xbins and self._keep_ybins):
            raise util.CytoflowOpError("No gate estimate found.  Did you forget to "
                                  "call estimate()?")

        if not self._xscale:
            raise util.CytoflowOpError("Couldn't find _xscale.  What happened??")
        
        if not self._yscale:
            raise util.CytoflowOpError("Couldn't find _yscale.  What happened??")

        if self.xchannel not in experiment.data:
            raise util.CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.xchannel))

        if self.ychannel not in experiment.data:
            raise util.CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.ychannel))
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))

            if len(experiment.data[b].unique()) > 100: #WARNING - magic number
                raise util.CytoflowOpError("More than 100 unique values found for"
                                      " aggregation metadata {0}.  Did you"
                                      " accidentally specify a data channel?"
                                      .format(b))
        
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that
            # contains all the events
            groupby = experiment.data.groupby(lambda _: True)
            
        event_assignments = pd.Series([False] * len(experiment), dtype = "bool")
        
        for group, group_data in groupby:
            if group not in self._keep_xbins:
                # there weren't any events in this group, so we didn't get
                # an estimate
                continue
            
            group_idx = groupby.groups[group]
            
            cX = pd.cut(group_data[self.xchannel], self._xbins, include_lowest = True, labels = False)
            cY = pd.cut(group_data[self.ychannel], self._ybins, include_lowest = True, labels = False)

            group_keep = pd.Series([False] * len(group_data))
            
            for (xbin, ybin) in zip(self._keep_xbins[group],
                                    self._keep_ybins[group]):
                group_keep[(cX == xbin) & (cY == ybin)] = True
            
            event_assignments.iloc[group_idx] = group_keep
                    
        new_experiment = experiment.clone()
        
        new_experiment.add_condition(self.name, "bool", event_assignments)

        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment
     
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the Gaussian mixture model.
         
        Returns
        -------
            IView : an IView, call plot() to see the diagnostic plot.
        """
        return DensityGateView(op = self, **kwargs)
     
#     
# # a few more imports for drawing scaled ellipses
#         
# import matplotlib.path as path
# import matplotlib.patches as patches
# import matplotlib.transforms as transforms
#     
@provides(cytoflow.views.IView)
class DensityGateView(By2DView):
    """
    Attributes
    ----------
    op : Instance(GaussianMixture2DOp)
        The op whose parameters we're viewing.        
    """
     
    id = 'edu.mit.synbio.cytoflow.view.densitygateview'
    friendly_id = "Density Gate Diagnostic Plot"
     
    _by = Property(List)
     
    def _get__by(self):
        facets = [x for x in [self.xfacet, self.yfacet] if x]
        return list(set(self.op.by) - set(facets))
         
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce.  The values returned can be passed to "plot".
        """
     
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {} not in the experiment"
                                    .format(self.xfacet))
             
        if self.xfacet and self.xfacet not in self.op.by:
            raise util.CytoflowViewError("X facet {} must be in GaussianMixture1DOp.by, which is {}"
                                    .format(self.xfacet, self.op.by))
         
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment"
                                    .format(self.yfacet))
             
        if self.yfacet and self.yfacet not in self.op.by:
            raise util.CytoflowViewError("Y facet {} must be in GaussianMixture1DOp.by, which is {}"
                                    .format(self.yfacet, self.op.by))
             
        for b in self.op.by:
            if b not in experiment.data:
                raise util.CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))    
     
        class plot_enum(object):
             
            def __init__(self, view, experiment):
                self._iter = None
                self._returned = False
                 
                if view._by:
                    self._iter = experiment.data.groupby(view._by).__iter__()
                 
            def __iter__(self):
                return self
             
            def __next__(self):
                if self._iter:
                    return next(self._iter)[0]
                else:
                    if self._returned:
                        raise StopIteration
                    else:
                        self._returned = True
                        return None
             
        return plot_enum(self, experiment)
     
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot the plots.
        """
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
         
        if not self.op.xchannel:
            raise util.CytoflowViewError("No X channel specified")
         
        if not self.op.ychannel:
            raise util.CytoflowViewError("No Y channel specified")
 
        experiment = experiment.clone()
         
        # try to apply the current op
        try:
            experiment = self.op.apply(experiment)
        except util.CytoflowOpError:
            pass
         
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
                experiment.data.reset_index(drop = True, inplace = True)
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                 
            if len(experiment) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset)) 
         
        # figure out common limits
        # adjust the limits to clip extreme values
        min_quantile = self.op.min_quantile
        max_quantile = self.op.max_quantile
        
        legend = kwargs.pop('legend', True)
        kwargs.setdefault('cmap', plt.get_cmap('viridis'))
                 
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (experiment.data[self.op.xchannel].quantile(min_quantile),
                    experiment.data[self.op.xchannel].quantile(max_quantile))
 
        ylim = kwargs.pop("ylim", None)
        if ylim is None:
            ylim = (experiment.data[self.op.ychannel].quantile(min_quantile),
                    experiment.data[self.op.ychannel].quantile(max_quantile))
               
        # see if we're making subplots
        if self._by and plot_name is None:
            raise util.CytoflowViewError("You must use facets {} in either the "
                                         "plot variables or the plt name. "
                                         "Possible plot names: {}"
                                         .format(self._by, [x for x in self.enum_plots(experiment)]))
                 
        if plot_name is not None:
            if plot_name is not None and not self._by:
                raise util.CytoflowViewError("Plot {} not from plot_enum"
                                             .format(plot_name))
                 
            groupby = experiment.data.groupby(self._by)
             
            if plot_name not in set(groupby.groups.keys()):
                raise util.CytoflowViewError("Plot {} not from plot_enum"
                                             .format(plot_name))
             
            experiment.data = groupby.get_group(plot_name)
            experiment.data.reset_index(drop = True, inplace = True)
             
        # plot the density plot, whether or not we're plotting isolines on top
         
        g = super(DensityGateView, self).plot(experiment, 
                                              xscale = self.op._xscale, 
                                              yscale = self.op._yscale,
                                              xlim = xlim, 
                                              ylim = ylim,
                                              smoothed = True,
                                              legend = (legend and self.op._xbins.size == 0),
                                              **kwargs)
         
        if self._by and plot_name is not None:
            plt.title("{0} = {1}".format(self._by, plot_name))

        # plot a countour around the bins that got kept
        if self.op._xbins.size and self.op._ybins.size:
            group = plot_name if plot_name is not None else True

            keep_x = self.op._keep_xbins[group]
            keep_y = self.op._keep_ybins[group]
            h = self.op._histogram[group]
            last_level = h[keep_x[-1], keep_y[-1]]
            g.map(_contourplot, 
                  xbins = self.op._xbins[0:-1], 
                  ybins = self.op._ybins[0:-1],
                  histogram = h,
                  last_level = last_level)
            
            # set up the range of the color map
            if legend and 'norm' not in kwargs:
                data_max = 0
                for _, data_ijk in g.facet_data():
                    x = data_ijk[self.xchannel]
                    y = data_ijk[self.ychannel]
                    h, _, _ = np.histogram2d(x, y, bins=[self.op._xbins, self.op._ybins])
                    data_max = max(data_max, h.max())
                    
                hue_scale = util.scale_factory(self.huescale, 
                                               experiment, 
                                               data = np.array([1, data_max]))
                kwargs['norm'] = hue_scale.color_norm()
            
            if legend:
                plot_ax = plt.gca()
                cmap = kwargs['cmap']
                norm = kwargs['norm']
                cax, _ = mpl.colorbar.make_axes(plt.gcf().get_axes())
                mpl.colorbar.ColorbarBase(cax, cmap, norm)
                plt.sca(plot_ax)
        
def _contourplot(xbins, ybins, histogram, last_level, **kwargs):

    ax = plt.gca()  
    ax.contour(xbins, ybins, histogram, [last_level], **kwargs)
