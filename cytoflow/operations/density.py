#!/usr/bin/env python2.7
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

from __future__ import division, absolute_import

from warnings import warn
from itertools import product

import matplotlib.pyplot as plt

from traits.api import (HasStrictTraits, Str, CStr, Dict, Any, Instance, Bool, 
                        Constant, List, provides, DelegatesTo, Property)

import numpy as np
import scipy.stats
# from sklearn import mixture
# from scipy import linalg
# from scipy import stats
import pandas as pd
import seaborn as sns

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation

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
    
    _xbins = Dict(Any, Instance(np.ndarray), transient = True)
    _keep_xbins = Dict(Any, Instance(np.ndarray), transient = True)
    _ybins = Dict(Any, Instance(np.ndarray), transient = True)
    _keep_ybins = Dict(Any, Instance(np.ndarray), transient = True)
    
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
                    
        for group, group_data in groupby:
            if len(group_data) == 0:
                raise util.CytoflowOpError("Group {} had no data"
                                           .format(group))
                
            group_data = group_data.loc[:, [self.xchannel, self.ychannel]]

            group_data[self.xchannel] = self._xscale(group_data[self.xchannel])
            group_data[self.ychannel] = self._yscale(group_data[self.ychannel])
            
            # drop data that isn't in the scale range
            group_data = group_data[~(np.isnan(group_data[self.xchannel]) | np.isnan(group_data[self.ychannel]))]

            xlim = (xscale.clip(group_data[self.xchannel].quantile(self.min_quantile)),
                    xscale.clip(group_data[self.xchannel].quantile(self.max_quantile)))
                      
            ylim = (yscale.clip(group_data[self.ychannel].quantile(self.min_quantile)),
                    yscale.clip(group_data[self.ychannel].quantile(self.max_quantile)))
            
            xbins = xscale.inverse(np.linspace(xscale(xlim[0]), xscale(xlim[1]), self.bins))
            ybins = yscale.inverse(np.linspace(yscale(ylim[0]), yscale(ylim[1]), self.bins))
            
            h, x, y = np.histogram2d(group_data[self.xchannel], 
                                     group_data[self.ychannel], 
                                     bins=[xbins, ybins])
            

            i = scipy.stats.rankdata(h, method = "ordinal") - 1
            i = np.unravel_index(np.argsort(-i), (len(x), len(y)))

            goal_count = self.keep * len(group_data)
            curr_count = 0
            num_bins = 0
            
            while(curr_count < goal_count and num_bins < (xbins * ybins)):
                goal_count += h[i[0][num_bins], i[1][num_bins]]
                num_bins += 1
            
            self._xbins[group] = x
            self._keep_xbins[group] = i[0][0:num_bins]
            self._ybins[group] = y
            self._key_ybins[group] = i[1][0:num_bins]
            
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
        
        if not (self._xbins and self._ybins and self._keep_xbins and self._keep_ybins):
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
                           
        if self.sigma < 0.0:
            raise util.CytoflowOpError("sigma must be >= 0.0") 
        
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that
            # contains all the events
            groupby = experiment.data.groupby(lambda x: True)
            
        event_assignments = pd.Series([None] * len(experiment), dtype = "bool")
        
        for group, group_data in groupby:
            if group not in self._histogram:
                # there weren't any events in this group, so we didn't get
                # a gmm.
                continue
            
            group_idx = groupby.groups[group]
            
            xbins = self._xbins[group]
            keep_x = self._keep_xbins[group]
            ybins = self._ybins[group]
            keep_y = self._keep_ybins[group]
            
#             
#             gmm = self._gmms[group]
#             data = data_subset.loc[:, [self.xchannel, self.ychannel]]
#             x[self.xchannel] = self._xscale(x[self.xchannel])
#             x[self.ychannel] = self._yscale(x[self.ychannel])
#             
#             # which values are missing?
#             x_na = np.isnan(x[self.xchannel]) | np.isnan(x[self.ychannel])
#             x_na = x_na.values
#             
#             x = x.values
#             group_idx = groupby.groups[group]
# 
#             # make a preliminary assignment
#             predicted = np.full(len(x), -1, "int")
#             predicted[~x_na] = gmm.predict(x[~x_na])
#             
#             # if we're doing sigma-based gating, for each component check
#             # to see if the event is in the sigma gate.
#             if self.sigma > 0.0:
#                 
#                 # make a quick dataframe with the value and the predicted
#                 # component
#                 gate_df = pd.DataFrame({"x" : x[:, 0], 
#                                         "y" : x[:, 1],
#                                         "p" : predicted})
# 
#                 # for each component, get the ellipse that follows the isoline
#                 # around the mixture component
#                 # cf. http://scikit-learn.org/stable/auto_examples/mixture/plot_gmm.html
#                 # and http://www.mathworks.com/matlabcentral/newsreader/view_thread/298389
#                 # and http://stackoverflow.com/questions/7946187/point-and-ellipse-rotated-position-test-algorithm
#                 # i am not proud of how many tries this took me to get right.
# 
#                 for c in range(0, self.num_components):
#                     mean = gmm.means_[c]
#                     covar = gmm.covariances_[c]
#                     
#                     # xc is the center on the x axis
#                     # yc is the center on the y axis
#                     xc = mean[0]  # @UnusedVariable
#                     yc = mean[1]  # @UnusedVariable
#                     
#                     v, w = linalg.eigh(covar)
#                     u = w[0] / linalg.norm(w[0])
#                     
#                     # xl is the length along the x axis
#                     # yl is the length along the y axis
#                     xl = np.sqrt(v[0]) * self.sigma  # @UnusedVariable
#                     yl = np.sqrt(v[1]) * self.sigma  # @UnusedVariable
#                     
#                     # t is the rotation in radians (counter-clockwise)
#                     t = 2 * np.pi - np.arctan(u[1] / u[0])
#                     
#                     sin_t = np.sin(t)  # @UnusedVariable
#                     cos_t = np.cos(t)  # @UnusedVariable
#                                         
#                     # and build an expression with numexpr so it evaluates fast!
# 
#                     gate_bool = gate_df.eval("p == @c and "
#                                              "((x - @xc) * @cos_t - (y - @yc) * @sin_t) ** 2 / ((@xl / 2) ** 2) + "
#                                              "((x - @xc) * @sin_t + (y - @yc) * @cos_t) ** 2 / ((@yl / 2) ** 2) <= 1").values
# 
#                     predicted[np.logical_and(predicted == c, gate_bool == False)] = -1
#             
#             predicted_str = pd.Series(["(none)"] * len(predicted))
#             for c in range(0, self.num_components):
#                 predicted_str[predicted == c] = "{0}_{1}".format(self.name, c + 1)
#             predicted_str[predicted == -1] = "{0}_None".format(self.name)
#             predicted_str.index = group_idx
# 
#             event_assignments.iloc[group_idx] = predicted_str
#                     
#             if self.posteriors:
#                 probability = np.full((len(x), self.num_components), 0.0, "float")
#                 probability[~x_na, :] = gmm.predict_proba(x[~x_na, :])
#                 posteriors = pd.Series([0.0] * len(predicted))
#                 for c in range(0, self.num_components):
#                     posteriors[predicted == c] = probability[predicted == c, c]
#                 posteriors.index = group_idx
#                 event_posteriors.iloc[group_idx] = posteriors
                    
        new_experiment = experiment.clone()
        
        new_experiment.add_condition(self.name, "bool", event_assignments)


        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment
#     
#     def default_view(self, **kwargs):
#         """
#         Returns a diagnostic plot of the Gaussian mixture model.
#         
#         Returns
#         -------
#             IView : an IView, call plot() to see the diagnostic plot.
#         """
#         return GaussianMixture2DView(op = self, **kwargs)
#     
#     
# # a few more imports for drawing scaled ellipses
#         
# import matplotlib.path as path
# import matplotlib.patches as patches
# import matplotlib.transforms as transforms
#     
# @provides(cytoflow.views.IView)
# class GaussianMixture2DView(cytoflow.views.ScatterplotView):
#     """
#     Attributes
#     ----------
#     op : Instance(GaussianMixture2DOp)
#         The op whose parameters we're viewing.        
#     """
#     
#     id = 'edu.mit.synbio.cytoflow.view.gaussianmixture2dview'
#     friendly_id = "2D Gaussian Mixture Diagnostic Plot"
#     
#     # TODO - why can't I use GaussianMixture2DOp here?
#     op = Instance(IOperation)
#     xchannel = DelegatesTo('op')
#     ychannel = DelegatesTo('op')
#     xscale = DelegatesTo('op')
#     yscale = DelegatesTo('op')
#     
#     _by = Property(List)
#     
#     def _get__by(self):
#         facets = filter(lambda x: x, [self.xfacet, self.yfacet])
#         return list(set(self.op.by) - set(facets))
#         
#     def enum_plots(self, experiment):
#         """
#         Returns an iterator over the possible plots that this View can
#         produce.  The values returned can be passed to "plot".
#         """
#     
#         if self.xfacet and self.xfacet not in experiment.conditions:
#             raise util.CytoflowViewError("X facet {} not in the experiment"
#                                     .format(self.xfacet))
#             
#         if self.xfacet and self.xfacet not in self.op.by:
#             raise util.CytoflowViewError("X facet {} must be in GaussianMixture1DOp.by, which is {}"
#                                     .format(self.xfacet, self.op.by))
#         
#         if self.yfacet and self.yfacet not in experiment.conditions:
#             raise util.CytoflowViewError("Y facet {0} not in the experiment"
#                                     .format(self.yfacet))
#             
#         if self.yfacet and self.yfacet not in self.op.by:
#             raise util.CytoflowViewError("Y facet {} must be in GaussianMixture1DOp.by, which is {}"
#                                     .format(self.yfacet, self.op.by))
#             
#         for b in self.op.by:
#             if b not in experiment.data:
#                 raise util.CytoflowOpError("Aggregation metadata {0} not found"
#                                       " in the experiment"
#                                       .format(b))    
#     
#         class plot_enum(object):
#             
#             def __init__(self, view, experiment):
#                 self._iter = None
#                 self._returned = False
#                 
#                 if view._by:
#                     self._iter = experiment.data.groupby(view._by).__iter__()
#                 
#             def __iter__(self):
#                 return self
#             
#             def next(self):
#                 if self._iter:
#                     return self._iter.next()[0]
#                 else:
#                     if self._returned:
#                         raise StopIteration
#                     else:
#                         self._returned = True
#                         return None
#             
#         return plot_enum(self, experiment)
#     
#     def plot(self, experiment, plot_name = None, **kwargs):
#         """
#         Plot the plots.
#         """
#         if experiment is None:
#             raise util.CytoflowViewError("No experiment specified")
#         
#         if not self.op.xchannel:
#             raise util.CytoflowViewError("No X channel specified")
#         
#         if not self.op.ychannel:
#             raise util.CytoflowViewError("No Y channel specified")
# 
#         experiment = experiment.clone()
#         
#         # try to apply the current op
#         try:
#             experiment = self.op.apply(experiment)
#         except util.CytoflowOpError:
#             pass
#         
#         # if apply() succeeded (or wasn't needed), set up the hue facet
#         if self.op.name and self.op.name in experiment.conditions:
#             if self.huefacet and self.huefacet != self.op.name:
#                 warn("Resetting huefacet to the model component (was {}, now {})."
#                      .format(self.huefacet, self.op.name))
#             self.huefacet = self.op.name
#         
#         if self.subset:
#             try:
#                 experiment = experiment.query(self.subset)
#                 experiment.data.reset_index(drop = True, inplace = True)
#             except:
#                 raise util.CytoflowViewError("Subset string '{0}' isn't valid"
#                                         .format(self.subset))
#                 
#             if len(experiment) == 0:
#                 raise util.CytoflowViewError("Subset string '{0}' returned no events"
#                                         .format(self.subset)) 
#         
#         # figure out common limits
#         # adjust the limits to clip extreme values
#         min_quantile = kwargs.pop("min_quantile", 0.001)
#         max_quantile = kwargs.pop("max_quantile", 1.0) 
#                 
#         xlim = kwargs.pop("xlim", None)
#         if xlim is None:
#             xlim = (experiment.data[self.op.xchannel].quantile(min_quantile),
#                     experiment.data[self.op.xchannel].quantile(max_quantile))
# 
#         ylim = kwargs.pop("ylim", None)
#         if ylim is None:
#             ylim = (experiment.data[self.op.ychannel].quantile(min_quantile),
#                     experiment.data[self.op.ychannel].quantile(max_quantile))
#               
#         # see if we're making subplots
#         if self._by and plot_name is None:
#             raise util.CytoflowViewError("You must use facets {} in either the "
#                                          "plot variables or the plt name. "
#                                          "Possible plot names: {}"
#                                          .format(self._by, [x for x in self.enum_plots(experiment)]))
#                 
#         if plot_name is not None:
#             if plot_name is not None and not self._by:
#                 raise util.CytoflowViewError("Plot {} not from plot_enum"
#                                              .format(plot_name))
#                 
#             groupby = experiment.data.groupby(self._by)
#             
#             if plot_name not in set(groupby.groups.keys()):
#                 raise util.CytoflowViewError("Plot {} not from plot_enum"
#                                              .format(plot_name))
#             
#             experiment.data = groupby.get_group(plot_name)
#             experiment.data.reset_index(drop = True, inplace = True)
#             
#         # plot the scatterplot, whether or not we're plotting isolines on top
#         
#         g = super(GaussianMixture2DView, self).plot(experiment, 
#                                                     xscale = self.op._xscale, 
#                                                     yscale = self.op._yscale,
#                                                     xlim = xlim, 
#                                                     ylim = ylim,
#                                                     **kwargs)
#         
#         if self._by and plot_name is not None:
#             plt.title("{0} = {1}".format(self._by, plot_name))
# 
#         # plot the actual distribution on top of it.  display as a "contour"
#         # plot with ellipses at 1, 2, and 3 standard deviations
#         # cf. http://scikit-learn.org/stable/auto_examples/mixture/plot_gmm.html
#         
#         row_names = g.row_names if g.row_names else [False]
#         col_names = g.col_names if g.col_names else [False]
#         
#         for (i, row), (j, col) in product(enumerate(row_names),
#                                           enumerate(col_names)):
#             
#             facets = filter(lambda x: x, [row, col])
#             if plot_name is not None:
#                 try:
#                     gmm_name = list(plot_name) + facets
#                 except TypeError: # plot_name isn't a list
#                     gmm_name = list([plot_name]) + facets  
#             else:      
#                 gmm_name = facets
#                 
#             if len(gmm_name) == 0:
#                 gmm_name = None
#             elif len(gmm_name) == 1:
#                 gmm_name = gmm_name[0]   
# 
#             if gmm_name is not None:
#                 if gmm_name in self.op._gmms:
#                     gmm = self.op._gmms[gmm_name]
#                 else:
#                     # there weren't any events in this subset to estimate a GMM from
#                     warn("No estimated GMM for plot {}".format(gmm_name),
#                           util.CytoflowViewWarning)
#                     return g
#             else:
#                 if True in self.op._gmms:
#                     gmm = self.op._gmms[True]
#                 else:
#                     return g           
#                 
#             ax = g.facet_axis(i, j)
#         
#             for k, (mean, covar) in enumerate(zip(gmm.means_, gmm.covariances_)):    
#                 v, w = linalg.eigh(covar)
#                 u = w[0] / linalg.norm(w[0])
#                 
#                 #rotation angle (in degrees)
#                 t = np.arctan(u[1] / u[0])
#                 t = 180 * t / np.pi
#                            
#                 color_k = k % len(sns.color_palette())
#                 color = sns.color_palette()[color_k]
#                 
#                 # in order to scale the ellipses correctly, we have to make them
#                 # ourselves out of an affine-scaled unit circle.  The interface
#                 # is the same as matplotlib.patches.Ellipse
#                 
#                 self._plot_ellipse(ax,
#                                    mean,
#                                    np.sqrt(v[0]),
#                                    np.sqrt(v[1]),
#                                    180 + t,
#                                    color = color,
#                                    fill = False,
#                                    linewidth = 2)
#     
#                 self._plot_ellipse(ax, 
#                                    mean,
#                                    np.sqrt(v[0]) * 2,
#                                    np.sqrt(v[1]) * 2,
#                                    180 + t,
#                                    color = color,
#                                    fill = False,
#                                    linewidth = 2,
#                                    alpha = 0.66)
#                 
#                 self._plot_ellipse(ax, 
#                                    mean,
#                                    np.sqrt(v[0]) * 3,
#                                    np.sqrt(v[1]) * 3,
#                                    180 + t,
#                                    color = color,
#                                    fill = False,
#                                    linewidth = 2,
#                                    alpha = 0.33)
#                 
#         return g
# 
#     def _plot_ellipse(self, ax, center, width, height, angle, **kwargs):
#         tf = transforms.Affine2D() \
#              .scale(width * 0.5, height * 0.5) \
#              .rotate_deg(angle) \
#              .translate(*center)
#              
#         tf_path = tf.transform_path(path.Path.unit_circle())
#         v = tf_path.vertices
#         v = np.vstack((self.op._xscale.inverse(v[:, 0]),
#                        self.op._yscale.inverse(v[:, 1]))).T
# 
#         scaled_path = path.Path(v, tf_path.codes)
#         scaled_patch = patches.PathPatch(scaled_path, **kwargs)
#         ax.add_patch(scaled_patch)
#             
#              
# 
#     
