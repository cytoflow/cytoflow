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
                        Constant, List, provides, Property, Enum)

import numpy as np
import numpy.linalg
import sklearn.cluster
import sklearn.mixture
import scipy.stats
import scipy.optimize

import pandas as pd
import seaborn as sns

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class FlowPeaksOp(HasStrictTraits):
    """
    This module uses the flowPeaks algorithm to assign events to clusters in
    an unsupervised manner.
    
    Call `estimate()` to compute the cluster centroids and smoothed density.
      
    Calling `apply()` creates a new categorical metadata variable 
    named `name`, with possible values `{name}_1` .... `name_n` where `n` is 
    the number of clusters, specified with `n_clusters`.
    
    The same model may not be appropriate for different subsets of the data set.
    If this is the case, you can use the `by` attribute to specify metadata by 
    which to aggregate the data before estimating (and applying) a model.  The 
    number of clusters is the same across each subset, though.

    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    channels : List(Str)
        The channels to apply the clustering algorithm to.

    scale : Dict(Str : Enum("linear", "logicle", "log"))
        Re-scale the data in the specified channels before fitting.  If a 
        channel is in `channels` but not in `scale`, the current package-wide
        default (set with `set_default_scale`) is used.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will fit the model 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
        
    tol : Float (default = 0.5)
        How readily should clusters be merged?  Must be between 0 and 1.
        
    find_outliers : Bool (default = False)
        Should the algorithm use an extra step to identify outliers?
        
    Notes
    -----
    
    This algorithm uses kmeans to find a large number of clusters, then 
    hierarchically merges those clusters.  Thus, the user does not need to
    specify the number of clusters in advance; and it can find non-convex
    clusters.  It also operates in an arbitrary number of dimensions.
    
    For details and a theoretical justification, see
    
    flowPeaks: a fast unsupervised clustering for flow cytometry data via
    K-means and density peak finding 
    
    Yongchao Ge  Stuart C. Sealfon
    Bioinformatics (2012) 28 (15): 2052-2058.         
  
    Examples
    --------
    
    >>> clust_op = KMeansOp(name = "Clust",
    ...                         channels = ["V2-A", "Y2-A"],
    ...                         scale = {"V2-A" : "log"},
    ...                         num_clusters = 2)
    >>> clust_op.estimate(ex2)
    >>> clust_op.default_view(channels = ["V2-A"], ["Y2-A"]).plot(ex2)
    >>> ex3 = clust_op.apply(ex2)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.flowpeaks')
    friendly_id = Constant("FlowPeaks Clustering")
    
    name = CStr()
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    by = List(Str)
    find_outliers = Bool(False)
    tol = util.PositiveFloat(0.1, allow_zero = False)
    
    _kmeans = Dict(Any, Instance(sklearn.cluster.MiniBatchKMeans), transient = True)
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
            groupby = experiment.data.groupby(lambda _: True)
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        for c in self.channels:
            if c in self.scale:
                self._scale[c] = util.scale_factory(self.scale[c], experiment, channel = c)
            else:
                self._scale[c] = util.scale_factory(util.get_default_scale(), experiment, channel = c)
                    
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
            
            #### choose the number of clusters and fit the kmeans
            num_clusters = [util.num_hist_bins(x[:, c]) for c in range(len(self.channels))]
            num_clusters = np.ceil(np.median(num_clusters))
            num_clusters = int(num_clusters)
            
            self._kmeans[group] = kmeans = \
                sklearn.cluster.MiniBatchKMeans(n_clusters = num_clusters)
            
            kmeans.fit(x)
            x_labels = kmeans.predict(x)
            d = len(self.channels)

            
            #### use the kmeans centroids to parameterize a finite gaussian
            #### mixture model which estimates the density function
 
            gmm = sklearn.mixture.GaussianMixture(n_components = num_clusters, 
                                                  covariance_type='full')
            gmm.weights_ = np.ndarray((0,))
            gmm.means_ = np.ndarray((0, d))
            gmm.covariances_ = np.ndarray((0, d, d))
            gmm.precisions_ = np.ndarray((0, d, d))
            gmm.precisions_cholesky_ = np.ndarray((0, d, d))
            
            d = len(self.channels)
            s0 = np.zeros([d, d])
            for j in range(d):
                r = x[d].max() - x[d].min()
                s0[j, j] = (r / (num_clusters ** (1. / d))) ** 0.5 
            
            for k in range(num_clusters):
                xk = x[x_labels == k]
                num_k = np.sum(x_labels == k)
                weight_k = num_k / len(x_labels)
                mu = xk.mean(axis = 0)
                s = np.cov(xk, rowvar = False)

                # TODO - make these magic numbers adjustable
                h0 = 1
                h = 1.5
                
                el = num_k / (num_clusters + num_k)
                s_smooth = el * h * s + (1.0 - el) * h0 * s0
                s_precision = numpy.linalg.inv(s_smooth)
                s_cholesky = numpy.linalg.cholesky(s_precision)
                
                gmm.weights_ = np.append(gmm.weights_, [weight_k], axis = 0)
                gmm.means_ = np.append(gmm.means_, mu[np.newaxis, :], axis = 0)
                gmm.covariances_ = np.append(gmm.covariances_, s_smooth[np.newaxis, :, :], axis = 0)
                gmm.precisions_ = np.append(gmm.precisions_, s_precision[np.newaxis, :, :], axis = 0)
                gmm.precisions_cholesky_ = np.append(gmm.precisions_cholesky_, s_cholesky[np.newaxis, :, :], axis = 0)
                
            ### use optimization on the gmm to find local peaks for each 
            ### mixture component
            clust_peaks = []
            for k in range(num_clusters):
                mu = gmm.means_[k]
                f = lambda x: -1.0 * gmm.score(x[np.newaxis, :])
                res = scipy.optimize.minimize(f, mu)
                if res.status != 0:
                    raise util.CytoflowOpError("Peak finding failed for cluster {}: {}"
                                               .format(k, res.message))
                clust_peaks.append(res.x)
                
            print clust_peaks
                                                 
         
    def apply(self, experiment):
        """
        Apply the KMeans clustering to the data
        """
 
        if experiment is None:
            raise util.CytoflowOpError("No experiment specified")
         
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")
         
        if self.name in experiment.data.columns:
            raise util.CytoflowOpError("Experiment already has a column named {0}"
                                  .format(self.name))
         
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
                 
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True)
                 
        event_assignments = pd.Series(["{}_None".format(self.name)] * len(experiment), dtype = "object")
         
        # make the statistics       
        clusters = [x + 1 for x in range(self.num_clusters)]
          
        idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [clusters] + [self.channels], 
                                         names = list(self.by) + ["Cluster"] + ["Channel"])
        centers_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
                     
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError("Group {} had no data"
                                           .format(group))
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
                 
            # which values are missing?
 
            x_na = pd.Series([False] * len(x))
            for c in self.channels:
                x_na[np.isnan(x[c]).values] = True
                         
            x = x.values
            group_idx = groupby.groups[group]
            
            kmeans = self._kmeans[group]
  
            predicted = np.full(len(x), -1, "int")
            predicted[~x_na] = kmeans.predict(x[~x_na])
                 
            predicted_str = pd.Series(["(none)"] * len(predicted))
            for c in range(0, self.num_clusters):
                predicted_str[predicted == c] = "{0}_{1}".format(self.name, c + 1)
            predicted_str[predicted == -1] = "{0}_None".format(self.name)
            predicted_str.index = group_idx
      
            event_assignments.iloc[group_idx] = predicted_str
            
            for c in range(self.num_clusters):
                if len(self.by) == 0:
                    g = [c + 1]
                elif hasattr(group, '__iter__'):
                    g = tuple(list(group) + [c + 1])
                else:
                    g = tuple([group] + [c + 1])
                
                for cidx1, channel1 in enumerate(self.channels):
                    g2 = tuple(list(g) + [channel1])
                    centers_stat.loc[g2] = self._scale[channel1].inverse(kmeans.cluster_centers_[c, cidx1])
         
        new_experiment = experiment.clone()          
        new_experiment.add_condition(self.name, "category", event_assignments)
        
        new_experiment.statistics[(self.name, "centers")] = pd.to_numeric(centers_stat)
 
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the Gaussian mixture model.
         
        Returns
        -------
            IView : an IView, call plot() to see the diagnostic plot.
        """
        channels = kwargs.pop('channels', self.channels)
        scale = kwargs.pop('scale', self.scale)
        
        for c in channels:
            if c not in self.channels:
                raise util.CytoflowViewError("Channel {} isn't in the operation's channels"
                                             .format(c))
                
        for s in scale:
            if s not in self.channels:
                raise util.CytoflowViewError("Channel {} isn't in the operation's channels"
                                             .format(s))

        for c in channels:
            if c not in scale:
                scale[c] = util.get_default_scale()
            
        if len(channels) == 0:
            raise util.CytoflowViewError("Must specify at least one channel for a default view")
        elif len(channels) == 1:
            return FlowPeaks1DView(op = self, 
                                channel = channels[0], 
                                scale = scale[channels[0]], 
                                **kwargs)
        elif len(channels) == 2:
            return FlowPeaks2DView(op = self, 
                                xchannel = channels[0], 
                                ychannel = channels[1],
                                xscale = scale[channels[0]],
                                yscale = scale[channels[1]], 
                                **kwargs)
        else:
            raise util.CytoflowViewError("Can't specify more than two channels for a default view")
        
    
@provides(cytoflow.views.IView)
class FlowPeaks1DView(cytoflow.views.HistogramView):
    """
    Attributes
    ----------    
    op : Instance(GaussianMixture1DOp)
        The op whose parameters we're viewing.
    """
    
    id = 'edu.mit.synbio.cytoflow.view.gaussianmixture1dview'
    friendly_id = "1D Gaussian Mixture Diagnostic Plot"
    
    # TODO - why can't I use GaussianMixture1DOp here?
    op = Instance(IOperation)
    
    _by = Property(List)
    
    def _get__by(self):
        facets = filter(lambda x: x, [self.xfacet, self.yfacet])
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
            
            def next(self):
                if self._iter:
                    return self._iter.next()[0]
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
              
        if not self.channel:
            raise util.CytoflowViewError("No channel specified")
              
        experiment = experiment.clone()
        
        # try to apply the current operation
        try:
            experiment = self.op.apply(experiment)
        except util.CytoflowOpError:
            # could have failed because no GMMs have been estimated, or because
            # op has already been applied
            pass  

        # if apply() succeeded (or wasn't needed), set up the hue facet
        if self.op.name and self.op.name in experiment.conditions:
            if self.huefacet and self.huefacet != self.op.name:
                warn("Resetting huefacet to the model component (was {}, now {})."
                     .format(self.huefacet, self.op.name))
            self.huefacet = self.op.name
        else:
            self.huefacet = ""
        
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
        
        # figure out common x limits for multiple plots
        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 1.0) 
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (experiment.data[self.channel].quantile(min_quantile),
                    experiment.data[self.channel].quantile(max_quantile))
              
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

        # get the parameterized scale object back from the op
        if self.channel in self.op.scale and self.scale == self.op.scale[self.channel]:
            scale = self.op._scale[self.channel]
        else:
            scale = util.scale_factory(self.scale, experiment, channel = self.channel)

        # plot the histogram, whether or not we're plotting distributions on top

        g = super(FlowPeaks1DView, self).plot(experiment, 
                                                    scale = scale, 
                                                    xlim = xlim,
                                                    **kwargs)
                
        if self._by and plot_name is not None:
            plt.title("{0} = {1}".format(self._by, plot_name))

        # plot the actual distribution on top of it.    
        
        row_names = g.row_names if g.row_names else [False]
        col_names = g.col_names if g.col_names else [False]
                
        for (i, row), (j, col) in product(enumerate(row_names),
                                          enumerate(col_names)):
            
            facets = filter(lambda x: x, [row, col])
            if plot_name is not None:
                try:
                    km_name = tuple(list(plot_name) + facets)
                except TypeError: # plot_name isn't a list
                    km_name = tuple(list([plot_name]) + facets) 
            else:      
                km_name = tuple(facets)
                
            if len(km_name) == 0:
                km_name = None
            elif len(km_name) == 1:
                km_name = km_name[0]
                        
            if km_name is not None:
                if km_name in self.op._kms:
                    km = self.op._kmeans[km_name]
                else:
                    # there weren't any events in this subset to estimate a km from
                    warn("No clusters for plot {}".format(km_name),
                          util.CytoflowViewWarning)
                    return g
            else:
                if True in self.op._kmeans:
                    km = self.op._kmeans[True]
                else:
                    return g           
                
            ax = g.facet_axis(i, j)
            plt.sca(ax)
                                                
            # plot the cluster centers
                
            cidx = self.op.channels.index(self.channel)
            for k in range(0, self.op.num_clusters):
                c = km.cluster_centers_[k][cidx]
                
                plt.axvline(c, linewidth=3, color='blue')                      
        return g

     
@provides(cytoflow.views.IView)
class FlowPeaks2DView(cytoflow.views.ScatterplotView):
    """
    Attributes
    ----------
    op : Instance(GaussianMixture2DOp)
        The op whose parameters we're viewing.        
    """
     
    id = 'edu.mit.synbio.cytoflow.view.gaussianmixture2dview'
    friendly_id = "Gaussian Mixture Diagnostic Plot"
     
    # TODO - why can't I use GaussianMixture2DOp here?
    op = Instance(IOperation)
     
    _by = Property(List)
     
    def _get__by(self):
        facets = filter(lambda x: x, [self.xfacet, self.yfacet])
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
            raise util.CytoflowViewError("X facet {} must be in GaussianMixtureOp.by, which is {}"
                                    .format(self.xfacet, self.op.by))
         
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment"
                                    .format(self.yfacet))
             
        if self.yfacet and self.yfacet not in self.op.by:
            raise util.CytoflowViewError("Y facet {} must be in GaussianMixtureOp.by, which is {}"
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
             
            def next(self):
                if self._iter:
                    return self._iter.next()[0]
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
        
        if not self.xchannel:
            raise util.CytoflowViewError("No X channel specified")
        
        if not self.ychannel:
            raise util.CytoflowViewError("No Y channel specified")

        experiment = experiment.clone()
        
        # try to apply the current op
        try:
            experiment = self.op.apply(experiment)
        except util.CytoflowOpError:
            pass
        
        # if apply() succeeded (or wasn't needed), set up the hue facet
        if self.op.name and self.op.name in experiment.conditions:
            if self.huefacet and self.huefacet != self.op.name:
                warn("Resetting huefacet to the model component (was {}, now {})."
                     .format(self.huefacet, self.op.name))
            self.huefacet = self.op.name
        
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
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 1.0) 
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (experiment.data[self.xchannel].quantile(min_quantile),
                    experiment.data[self.xchannel].quantile(max_quantile))

        ylim = kwargs.pop("ylim", None)
        if ylim is None:
            ylim = (experiment.data[self.ychannel].quantile(min_quantile),
                    experiment.data[self.ychannel].quantile(max_quantile))
              
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
            
        if self.xchannel in self.op.scale and self.xscale == self.op.scale[self.xchannel]:
            xscale = self.op._scale[self.xchannel]
        else:
            xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)
           
        if self.ychannel in self.op.scale and self.yscale == self.op.scale[self.ychannel]:
            yscale = self.op._scale[self.ychannel]
        else:
            yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
            
        # plot the scatterplot, whether or not we're plotting isolines on top
        
        g = super(FlowPeaks2DView, self).plot(experiment, 
                                           xscale = xscale,
                                           yscale = yscale,
                                           xlim = xlim, 
                                           ylim = ylim,
                                           **kwargs)
         
        if self._by and plot_name is not None:
            plt.title("{0} = {1}".format(self._by, plot_name))
 
        # plot the actual distribution on top of it.  display as a "contour"
        # plot with ellipses at 68, 95, and 99 percentiles of the CDF of the 
        # multivariate gaussian 
        # cf. http://scikit-learn.org/stable/auto_examples/mixture/plot_gmm.html
         
        row_names = g.row_names if g.row_names else [False]
        col_names = g.col_names if g.col_names else [False]
         
        for (i, row), (j, col) in product(enumerate(row_names),
                                          enumerate(col_names)):
             
            facets = filter(lambda x: x, [row, col])
            if plot_name is not None:
                try:
                    km_name = list(plot_name) + facets
                except TypeError: # plot_name isn't a list
                    km_name = list([plot_name]) + facets  
            else:      
                km_name = facets
                 
            if len(km_name) == 0:
                km_name = None
            elif len(km_name) == 1:
                km_name = km_name[0]   
 
            if km_name is not None:
                if km_name in self.op._kmeans:
                    km = self.op._kmeans[km_name]
                else:
                    # there weren't any events in this subset to estimate a km from
                    warn("No estimated km for plot {}".format(km_name),
                          util.CytoflowViewWarning)
                    return g
            else:
                if True in self.op._kmeans:
                    km = self.op._kmeans[True]
                else:
                    return g           
                 
            ax = g.facet_axis(i, j)
            plt.sca(ax)
         
            ix = self.op.channels.index(self.xchannel)
            iy = self.op.channels.index(self.ychannel)
            
            for k in range(0, self.op.num_clusters):
                x = km.cluster_centers_[k][ix]
                y = km.cluster_centers_[k][iy]
                
                plt.plot(x, y, '*', color = 'blue')
#                 print (x, y)

                
#                 mu = mean[[ix, iy]]
#                 s = covar[rows, cols]
#                 
#                 v, w = linalg.eigh(s)
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
#                                    mu,
#                                    np.sqrt(v[0]),
#                                    np.sqrt(v[1]),
#                                    180 + t,
#                                    color = color,
#                                    fill = False,
#                                    linewidth = 2)
#       
#                 self._plot_ellipse(ax, 
#                                    mu,
#                                    np.sqrt(v[0]) * 2,
#                                    np.sqrt(v[1]) * 2,
#                                    180 + t,
#                                    color = color,
#                                    fill = False,
#                                    linewidth = 2,
#                                    alpha = 0.66)
#                   
#                 self._plot_ellipse(ax, 
#                                    mu,
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
#              .scale(width, height) \
#              .rotate_deg(angle) \
#              .translate(*center)
#               
#         tf_path = tf.transform_path(path.Path.unit_circle())
#         v = tf_path.vertices
#         v = np.vstack((self.op._scale[self.xchannel].inverse(v[:, 0]),
#                        self.op._scale[self.ychannel].inverse(v[:, 1]))).T
#  
#         scaled_path = path.Path(v, tf_path.codes)
#         scaled_patch = patches.PathPatch(scaled_path, **kwargs)
#         ax.add_patch(scaled_patch)
#              
              
 
     
