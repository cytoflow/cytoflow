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
                        Constant, List, provides, Property)

import numpy as np
import sklearn.mixture
import scipy.stats

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
        channel is in `channels` but not in `scale`, the current package-wide
        default (set with `set_default_scale`) is used.

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
        
    Statistics
    ----------
    mean : Float
        the mean of the fitted gaussian in each channel for each component.
        
    sigma : (Float, Float)
        the locations the mean +/- one standard deviation in each channel
        for each component.
        
    correlation : Float
        the correlation coefficient between each pair of channels for each
        component.
        
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
    
    # the key is either a single value or a tuple
    _gmms = Dict(Any, Instance(sklearn.mixture.GaussianMixture), transient = True)
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
            
            gmm = sklearn.mixture.GaussianMixture(n_components = self.num_components,
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

        # make the statistics       
        components = [x + 1 for x in range(self.num_components)]
         
        prop_idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [components], 
                                         names = list(self.by) + ["Component"])
        prop_stat = pd.Series(index = prop_idx, dtype = np.dtype(object)).sort_index()
                  
        mean_idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [components] + [self.channels], 
                                              names = list(self.by) + ["Component"] + ["Channel"])
        mean_stat = pd.Series(index = mean_idx, dtype = np.dtype(object)).sort_index()
        sigma_stat = pd.Series(index = mean_idx, dtype = np.dtype(object)).sort_index()

        corr_idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [components] + [self.channels] + [self.channels], 
                                              names = list(self.by) + ["Component"] + ["Channel_1"] + ["Channel_2"])
        corr_stat = pd.Series(index = corr_idx, dtype = np.dtype(object)).sort_index()  
                 
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
                x_na[np.isnan(x[c]).values] = True
                        
            x = x.values
            x_na = x_na.values
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
                    
                    # compute the Mahalanobis distance

                    f = lambda x, mu, s: np.dot(np.dot((x - mu).T, s), (x - mu))
                    dist = np.apply_along_axis(f, 1, x, mu, s)

                    # come up with a threshold based on sigma.  you'll note we
                    # didn't sqrt dist: that's because for a multivariate 
                    # Gaussian, the square of the Mahalanobis distance is
                    # chi-square distributed
                    
                    p = (scipy.stats.norm.cdf(self.sigma) - 0.5) * 2
                    thresh = scipy.stats.chi2.ppf(p, 1)
                    
                    event_gate[c].iloc[group_idx] = np.less_equal(dist, thresh)
                    
            if self.posteriors:
                p = gmm.predict(x)
                for c in range(self.num_components):
                    event_posteriors[c].iloc[group_idx] = p[c]
                    
            for c in range(self.num_components):
                if len(self.by) == 0:
                    g = [c + 1]
                elif hasattr(group, '__iter__'):
                    g = tuple(list(group) + [c + 1])
                else:
                    g = tuple([group] + [c + 1])

                prop_stat.loc[g] = gmm.weights_[c]
                
                for cidx1, channel1 in enumerate(self.channels):
                    g2 = tuple(list(g) + [channel1])
                    mean_stat.loc[g2] = self._scale[channel1].inverse(gmm.means_[c, cidx1])
                    
                    s, corr = util.cov2corr(gmm.covariances_[c])
                    sigma_stat.loc[g2] = (self._scale[channel1].inverse(gmm.means_[c, cidx1] - s[cidx1]),
                                          self._scale[channel1].inverse(gmm.means_[c, cidx1] + s[cidx1]))
            
                    for cidx2, channel2 in enumerate(self.channels):
                        g3 = tuple(list(g2) + [channel2])
                        corr_stat[g3] = corr[cidx1, cidx2]
                        
                    corr_stat.drop(tuple(list(g2) + [channel1]), inplace = True)

        new_experiment = experiment.clone()
          
        if self.num_components > 1:
            new_experiment.add_condition(self.name, "category", event_assignments)
            
        if self.sigma > 0:
            for c in range(self.num_components):
                gate_name = "{}_{}".format(self.name, c + 1)
                new_experiment.add_condition(gate_name, "bool", event_gate[c])
                
        if self.posteriors:
            for c in range(self.num_components):
                post_name = "{}_{}_posterior".format(self.name, c + 1)
                new_experiment.add_condition(post_name, "double", event_posteriors[c])
                
        new_experiment.statistics[(self.name, "mean")] = pd.to_numeric(mean_stat)
        new_experiment.statistics[(self.name, "sigma")] = sigma_stat
        if len(corr_stat) > 0:
            new_experiment.statistics[(self.name, "correlation")] = pd.to_numeric(corr_stat)
        if self.num_components > 1:
            new_experiment.statistics[(self.name, "proportion")] = pd.to_numeric(prop_stat)

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
            return GaussianMixture1DView(op = self, 
                                         channel = channels[0], 
                                         scale = scale[channels[0]], 
                                         **kwargs)
        elif len(channels) == 2:
            return GaussianMixture2DView(op = self, 
                                         xchannel = channels[0], 
                                         ychannel = channels[1],
                                         xscale = scale[channels[0]],
                                         yscale = scale[channels[1]], 
                                         **kwargs)
        else:
            raise util.CytoflowViewError("Can't specify more than two channels for a default view")
        
@provides(cytoflow.views.IView)
class GaussianMixture1DView(cytoflow.views.HistogramView):
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
        if self.channel in self.op.scale and self.scale == self.op.scale[self.xchannel]:
            scale = self.op._scale[self.xchannel]
        else:
            scale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)

        # plot the histogram, whether or not we're plotting distributions on top

        g = super(GaussianMixture1DView, self).plot(experiment, 
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
            
            facets = [x for x in [row, col] if x]
            if plot_name is not None:
                try:
                    gmm_name = tuple(list(plot_name) + facets)
                except TypeError: # plot_name isn't a list
                    gmm_name = tuple(list([plot_name]) + facets) 
            else:      
                gmm_name = tuple(facets)
                
            if len(gmm_name) == 0:
                gmm_name = None
            elif len(gmm_name) == 1:
                gmm_name = gmm_name[0]
                        
            if gmm_name is not None:
                if gmm_name in self.op._gmms:
                    gmm = self.op._gmms[gmm_name]
                else:
                    # there weren't any events in this subset to estimate a GMM from
                    warn("No estimated GMM for plot {}".format(gmm_name),
                          util.CytoflowViewWarning)
                    return g
            else:
                if True in self.op._gmms:
                    gmm = self.op._gmms[True]
                else:
                    return g           
                
            ax = g.facet_axis(i, j)
                                                
            # okay.  we want to scale the gaussian curves to have the same area
            # as the plots they're over.  so, what's the total area on the plot?
            
            patch_area = 0.0
                                    
            for k in range(0, len(ax.patches)):
                
                patch = ax.patches[k]
                xy = patch.get_xy()
                patch_area += poly_area([scale(p[0]) for p in xy], [p[1] for p in xy])
                
            # now, scale the plotted curve by the area of the total plot times
            # the proportion of it that is under that curve.
                
            for k in range(0, len(gmm.weights_)):
                pdf_scale = patch_area * gmm.weights_[k]
                 
                plt_min, plt_max = plt.gca().get_xlim()
                x = scale.inverse(np.linspace(scale(plt_min), scale(plt_max), 500))     
                c = self.op.channels.index(self.channel)
                mean = gmm.means_[k][c]
                stdev, _ = util.cov2corr(gmm.covariances_[k])
                y = scipy.stats.norm.pdf(scale(x), mean, stdev[c]) * pdf_scale
                color_k = k % len(sns.color_palette())
                color = sns.color_palette()[color_k]
                ax.plot(x, y, color = color)
                        
        return g

# from http://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
def poly_area(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))
     
    
# a few more imports for drawing scaled ellipses
         
import matplotlib.path as path
import matplotlib.patches as patches
import matplotlib.transforms as transforms
from scipy import linalg
     
@provides(cytoflow.views.IView)
class GaussianMixture2DView(cytoflow.views.ScatterplotView):
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
        
        g = super(GaussianMixture2DView, self).plot(experiment, 
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
             
            facets = [x for x in [row, col] if x]
            if plot_name is not None:
                try:
                    gmm_name = list(plot_name) + facets
                except TypeError: # plot_name isn't a list
                    gmm_name = list([plot_name]) + facets  
            else:      
                gmm_name = facets
                 
            if len(gmm_name) == 0:
                gmm_name = None
            elif len(gmm_name) == 1:
                gmm_name = gmm_name[0]   
 
            if gmm_name is not None:
                if gmm_name in self.op._gmms:
                    gmm = self.op._gmms[gmm_name]
                else:
                    # there weren't any events in this subset to estimate a GMM from
                    warn("No estimated GMM for plot {}".format(gmm_name),
                          util.CytoflowViewWarning)
                    return g
            else:
                if True in self.op._gmms:
                    gmm = self.op._gmms[True]
                else:
                    return g           
                 
            ax = g.facet_axis(i, j)
         
            ix = self.op.channels.index(self.xchannel)
            iy = self.op.channels.index(self.ychannel)
            rows = np.array([[ix, ix], [iy, iy]], dtype = np.intp)
            cols = np.array([[ix, iy], [ix, iy]], dtype = np.intp)
            for k, (mean, covar) in enumerate(zip(gmm.means_, gmm.covariances_)):    
                
                mu = mean[[ix, iy]]
                s = covar[rows, cols]
                
                v, w = linalg.eigh(s)
                u = w[0] / linalg.norm(w[0])
                  
                #rotation angle (in degrees)
                t = np.arctan(u[1] / u[0])
                t = 180 * t / np.pi
                             
                color_k = k % len(sns.color_palette())
                color = sns.color_palette()[color_k]
                  
                # in order to scale the ellipses correctly, we have to make them
                # ourselves out of an affine-scaled unit circle.  The interface
                # is the same as matplotlib.patches.Ellipse
                  
                self._plot_ellipse(ax,
                                   mu,
                                   np.sqrt(v[0]),
                                   np.sqrt(v[1]),
                                   180 + t,
                                   color = color,
                                   fill = False,
                                   linewidth = 2)
      
                self._plot_ellipse(ax, 
                                   mu,
                                   np.sqrt(v[0]) * 2,
                                   np.sqrt(v[1]) * 2,
                                   180 + t,
                                   color = color,
                                   fill = False,
                                   linewidth = 2,
                                   alpha = 0.66)
                  
                self._plot_ellipse(ax, 
                                   mu,
                                   np.sqrt(v[0]) * 3,
                                   np.sqrt(v[1]) * 3,
                                   180 + t,
                                   color = color,
                                   fill = False,
                                   linewidth = 2,
                                   alpha = 0.33)
                  
        return g
 
    def _plot_ellipse(self, ax, center, width, height, angle, **kwargs):
        tf = transforms.Affine2D() \
             .scale(width, height) \
             .rotate_deg(angle) \
             .translate(*center)
              
        tf_path = tf.transform_path(path.Path.unit_circle())
        v = tf_path.vertices
        v = np.vstack((self.op._scale[self.xchannel].inverse(v[:, 0]),
                       self.op._scale[self.ychannel].inverse(v[:, 1]))).T
 
        scaled_path = path.Path(v, tf_path.codes)
        scaled_patch = patches.PathPatch(scaled_path, **kwargs)
        ax.add_patch(scaled_patch)
             
              
 
     
