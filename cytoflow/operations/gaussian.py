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
import numpy.linalg
from sklearn import mixture
from scipy import linalg
import pandas as pd
import seaborn as sns

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class GaussianMixtureOp(HasStrictTraits):
    """
    This module fits a Gaussian mixture model with a specified number of
    components to one or more channels.
    
    If `num_components > 1`, `apply()` creates a new categorical metadata 
    variable named  `name`, with possible values `{name}_1` .... `name_n` 
    where `n` is the number of components.  An event is assigned to `name_i` 
    category if it has the highest posterior probability of having been 
    produced by component `i`.  If an event has a value that is outside the
    range of one of the channels' scales, then it is assigned to `{name}_None`.
    
    Optionally, if `sigma` is greater than 0, `apply()` creates new  `boolean` 
    metadata variables named `{name}_1` ... `{name}_n` where `n` is the number 
    of components.  The column `{name}_i` is `True` if the event is less than 
    `sigma` standard deviations from the mean of component `i`.  If 
    `num_components == 1`, `sigma` must be greater than 0.
    
    Optionally, if `posteriors` is `True`, `apply()` creates a new `double`
    metadata variables named `{name}_1_posterior` ... `{name}_n_posterior` 
    where `n` is the number of components.  The column `{name}_i_posterior`
    contains the posterior probability that this event is a member of 
    component `i`.
    
    Finally, the same mixture model (mean and standard deviation) may not
    be appropriate for every subset of the data.  If this is the case, you
    can use the `by` attribute to specify metadata by which to aggregate
    the data before estimating (and applying) a mixture model.  The number of 
    components must be the same across each subset, though.
    
    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    channels : List(Str)
        The channels to apply the mixture model to.

    scale : Dict(Str : Enum("linear", "logicle", "log"))
        Re-scale the data in the specified channels before fitting.  If a 
        channel is in `channels` but not in `scale`, it defaults to `linear`.

    num_components : Int (default = 1)
        How many components to fit to the data?  Must be a positive integer.

    sigma : Float (default = 0.0)
        How many standard deviations on either side of the mean to include
        in the boolean variable `{name}_i`?  Must be >= 0.0.  If 
        `num_components == 1`, must be > 0.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will fit the model 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.

    posteriors : Bool (default = False)
        If `True`, add columns named `{Name}_{i}_Posterior` giving the posterior
        probability that the event is in component `i`.  Useful for filtering 
        out low-probability events.
        
    variance : Bool (default = False)
        If `True`, add variance and covariance statistics to the resulting
        Experiment.
        
    Statistics
    ----------
    {name}_{channel}_{component}_mean : Float
        the mean of the fitted gaussian in the channel.
        
    {name}_variance : Float
        the variance of the fitted gaussian in this channel.
        
    {name}_{name}_covariance : Float
        the co-variance of the fitted gaussian in these two channels.
        
    proportion : Float
        the proportion of events in each component of the mixture model.  only
        added if `num_components` > 1.
        
    Notes
    -----
    
    We use the Mahalnobis distance as a multivariate generalization of 
    the number of standard deviations an event is from the mean of the
    multivariate gaussian.  If \vec{x} is an observation from a distribution
    with mean \vec{mu} and S is the covariance matrix, then the Mahalanobis
    distance is sqrt((x - mu)^T * S^-1 *(x - mu)).
    
    Examples
    --------
    
    >>> gauss_op = GaussianMixtureOp(name = "Gaussian",
    ...                              channels = ["V2-A", "Y2-A"],
    ...                              scale = {"V2-A" : "log"},
    ...                              num_components = 2)
    >>> gauss_op.estimate(ex2)
    >>> gauss_op.default_view(channels = ["V2-A"], ["Y2-A"]).plot(ex2)
    >>> ex3 = gauss_op.apply(ex2)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.gaussian')
    friendly_id = Constant("Gaussian Mixture")
    
    name = CStr()
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    num_components = util.PositiveInt(allow_zero = False)
    sigma = util.PositiveFloat(allow_zero = True)
    by = List(Str)
    
    posteriors = Bool(False)
    variance = Bool(False)
    
    # the key is either a single value or a tuple
    _gmms = Dict(Any, Instance(mixture.GaussianMixture), transient = True)
    _scale = Dict(Str, Instance(util.IScale), transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the Gaussian mixture model parameters
        """

        if experiment is None:
            raise util.CytoflowOpError("No experiment specified")
        
        if len(self.channels) == 0:
            raise util.CytoflowOpError("Must set at least one channel")

        for c in self.channels:
            if c not in experiment.data:
                raise util.CytoflowOpError("Channel {0} not found in the experiment"
                                      .format(c))
                
        for c in self.scale:
            if c not in self.channels:
                raise util.CytoflowOpError("Scale set for channel {0}, but it isn't "
                                           "in the experiment"
                                           .format(c))
       
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
        for c in self.channels:
            if c in self.scale:
                self._scale[c] = util.scale_factory(self.scale[c], experiment, channel = c)
            else:
                self._scale[c] = util.scale_factory("linear", experiment, channel = c)
        
        gmms = {}
            
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError("Group {} had no data"
                                           .format(group))
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
            
            # drop data that isn't in the scale range
            for c in self.channels:
                x = x[~(np.isnan(x[c]))]
            x = x.values
            
            gmm = mixture.GaussianMixture(n_components = self.num_components,
                                          covariance_type = "full",
                                          random_state = 1)
            gmm.fit(x)
            
            if not gmm.converged_:
                raise util.CytoflowOpError("Estimator didn't converge"
                                      " for group {0}"
                                      .format(group))
                
            # in the 1D version, we sorted the components by the means -- so
            # the first component has the lowest mean, the second component
            # has the next-lowest mean, etc.
            
            # that doesn't work in the general case.  instead, we assume that 
            # the clusters are likely (?) to be arranged along *one* of the 
            # axes, so we take the |norm| of the mean of each cluster and 
            # sort that way.
            
            norms = np.sum(gmm.means_ ** 2, axis = 1) ** 0.5
            sort_idx = np.argsort(norms)
            gmm.means_ = gmm.means_[sort_idx]
            gmm.weights_ = gmm.weights_[sort_idx]
            gmm.covariances_ = gmm.covariances_[sort_idx]
            
            gmms[group] = gmm
            
        self._gmms = gmms
     
    def apply(self, experiment):
        """
        Assigns new metadata to events using the mixture model estimated
        in `estimate`.
        """
             
        if experiment is None:
            raise util.CytoflowOpError("No experiment specified")
         
        if len(self.channels) == 0:
            raise util.CytoflowOpError("Must set at least one channel")
         
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")
        
        if self.num_components > 1 and self.name in experiment.data.columns:
            raise util.CytoflowOpError("Experiment already has a column named {0}"
                                  .format(self.name))
            
        if self.sigma > 0:
            for i in range(1, self.num_components + 1):
                cname = "{}_{}".format(self.name, i)
                if cname in experiment.data.columns:
                    raise util.CytoflowOpError("Experiment already has a column named {}"
                                  .format(cname))
 
        if self.posteriors:
            for i in range(1, self.num_components + 1):
                cname = "{}_{}_posterior".format(self.name, i)
                if cname in experiment.data.columns:
                    raise util.CytoflowOpError("Experiment already has a column named {}"
                                  .format(cname))               
         
        if not self._gmms:
            raise util.CytoflowOpError("No components found.  Did you forget to "
                                  "call estimate()?")
 
        for c in self.channels:
            if c not in experiment.channels:
                raise util.CytoflowOpError("Channel {0} not found in the experiment"
                                      .format(c))
             
        if self.posteriors:
            col_name = "{0}_Posterior".format(self.name)
            if col_name in experiment.data:
                raise util.CytoflowOpError("Column {0} already found in the experiment"
                              .format(col_name))
        
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
                            
        if self.num_components == 1 and self.sigma == 0.0:
            raise util.CytoflowOpError("if num_components is 1, sigma must be > 0.0")
        
                
        if self.num_components == 1 and self.posteriors:
            raise util.CytoflowOpError("If num_components == 1, all posteriors will be 1.")
         
        if self.num_components > 1:
            event_assignments = pd.Series(["{}_None".format(self.name)] * len(experiment), dtype = "object")
 
        if self.sigma > 0:
            event_gate = {i : pd.Series([False] * len(experiment), dtype = "double")
                           for i in range(self.num_components)}
 
        if self.posteriors:
            event_posteriors = {i : pd.Series([0.0] * len(experiment), dtype = "double")
                                for i in range(self.num_components)}
         
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that
            # contains all the events
            groupby = experiment.data.groupby(lambda _: True)            
         
        for group, data_subset in groupby:
            if group not in self._gmms:
                # there weren't any events in this group, so we didn't get
                # a gmm.
                continue
             
            gmm = self._gmms[group]
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
                
            # which values are missing?
            x_na = pd.Series([False] * len(x))
            for c in self.channels:
                x_na[np.isnan(x[c])] = True
                        
            x = x.values
            group_idx = groupby.groups[group]
 
            if self.num_components > 1:
                predicted = np.full(len(x), -1, "int")
                predicted[~x_na] = gmm.predict(x[~x_na])
                
                predicted_str = pd.Series(["(none)"] * len(predicted))
                for c in range(0, self.num_components):
                    predicted_str[predicted == c] = "{0}_{1}".format(self.name, c + 1)
                predicted_str[predicted == -1] = "{0}_None".format(self.name)
                predicted_str.index = group_idx
     
                event_assignments.iloc[group_idx] = predicted_str
                
            # if we're doing sigma-based gating, for each component check
            # to see if the event is in the sigma gate.
            if self.sigma > 0.0:
                for c in range(self.num_components):
                    s = np.linalg.pinv(gmm.covariances_[c])
                    mu = gmm.means_[c]
                    
                    f = lambda x, mu, s: np.dot(np.dot((x - mu).T, s), (x - mu))
                    dist = np.apply_along_axis(f, 1, x, mu, s)
                    
                    
                    # compute the Mahalanobis distance
                    
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
# 
#                      
#             if self.posteriors:
#                 probability = np.full((len(x), self.num_components), 0.0, "float")
#                 probability[~x_na, :] = gmm.predict_proba(x[~x_na, :])
#                 posteriors = pd.Series([0.0] * len(predicted))
#                 for c in range(0, self.num_components):
#                     posteriors[predicted == c] = probability[predicted == c, c]
#                 posteriors.index = group_idx
#                 event_posteriors.iloc[group_idx] = posteriors
#                      
        
        new_experiment = experiment.clone()
          
        if self.num_components > 1:
            new_experiment.add_condition(self.name, "category", event_assignments)
#              
#         if self.posteriors and self.num_components > 1:
#             col_name = "{0}_Posterior".format(self.name)
#             new_experiment.add_condition(col_name, "float", event_posteriors)
#                      
#         # add the statistics
#         levels = list(self.by)
#         if self.num_components > 1:
#             levels.append(self.name)
#                      
#         if levels:     
#             idx = pd.MultiIndex.from_product([new_experiment[x].unique() for x in levels], 
#                                              names = levels)
#      
#             xmean_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
#             ymean_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
#             prop_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()     
#                                     
#             for group, _ in groupby:
#                 gmm = self._gmms[group]
#                 for c in range(self.num_components):
#                     if self.num_components > 1:
#                         component_name = "{}_{}".format(self.name, c + 1)
#  
#                         if group is True:
#                             g = [component_name]
#                         elif isinstance(group, tuple):
#                             g = list(group)
#                             g.append(component_name)
#                         else:
#                             g = list([group])
#                             g.append(component_name)
#                          
#                         if len(g) > 1:
#                             g = tuple(g)
#                         else:
#                             g = g[0]
#                     else:
#                         g = group
#                                                                               
#                     xmean_stat.loc[g] = self._xscale.inverse(gmm.means_[c][0])
#                     ymean_stat.loc[g] = self._yscale.inverse(gmm.means_[c][0])
#                     prop_stat.loc[g] = gmm.weights_[c]
#                       
#             new_experiment.statistics[(self.name, "xmean")] = pd.to_numeric(xmean_stat)
#             new_experiment.statistics[(self.name, "ymean")] = pd.to_numeric(ymean_stat)
#             if self.num_components > 1:
#                 new_experiment.statistics[(self.name, "proportion")] = pd.to_numeric(prop_stat)
#              
#                      
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
    
# a few more imports for drawing scaled ellipses
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
