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

'''
Created on Dec 16, 2015

@author: brian
'''

from warnings import warn
from itertools import product

from traits.api import (HasStrictTraits, Str, CStr, Dict, Any, Instance, Bool, 
                        Constant, List, provides, Property, DelegatesTo)
import numpy as np
import matplotlib.pyplot as plt
import sklearn.mixture as mixture
import scipy.stats as stats
import pandas as pd
import seaborn as sns

from cytoflow.views import IView, HistogramView
from .base_op_views import BaseOp1DView
import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class GaussianMixture1DOp(HasStrictTraits):
    """
    This module fits a Gaussian mixture model with a specified number of
    components to a channel.
    
    Creates a new categorical metadata variable named `name`, with possible
    values `name_1` .... `name_n` where `n` is the number of components.
    An event is assigned to `name_i` category if it falls within `sigma`
    standard deviations of the component's mean.  If that is true for multiple
    categories (or if `sigma == 0.0`), the event is assigned to the category 
    with the highest posterior probability.  If the event doesn't fall into
    any category, it is assigned to `name_None`.
    
    As a special case, if `num_components` is `1` and `sigma` > 0.0, then
    the new condition is boolean, `True` if the event fell in the gate and
    `False` otherwise.
    
    Optionally, if `posteriors` is `True`, this module will also compute the 
    posterior probability of each event in its assigned component, returning
    it in a new colunm named `{Name}_Posterior`.
    
    Finally, the same mixture model (mean and standard deviation) may not
    be appropriate for every subset of the data.  If this is the case, you
    can use the `by` attribute to specify metadata by which to aggregate
    the data before estimating (and applying) a mixture.  The number of 
    components is the same across each subset, though.
    
    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    channel : Str
        Which channel to apply the mixture model to.
        
    num_components : Int (default = 1)
        How many components to fit to the data?  Must be positive.

    sigma : Float (default = 0.0)
        How many standard deviations on either side of the mean to include
        in each category?  If an event is in multiple components, assign it
        to the component with the highest posterior probability.  If 
        `sigma == 0.0`, categorize *all* the data by assigning each event to
        the component with the highest posterior probability.  Must be >= 0.0.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will fit the model 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
        
    scale : Enum("linear", "log", "logicle") (default = "linear")
        Re-scale the data before fitting the model?  
        
    posteriors : Bool (default = False)
        If `True`, add a column named `{Name}_Posterior` giving the posterior
        probability that the event is in the component to which it was
        assigned.  Useful for filtering out low-probability events.

    Statistics
    ----------
    mean : Float
        the mean of the fitted gaussian
        
    stdev : Float
        the inverse-scaled standard deviation of the fitted gaussian.  on a 
        linear scale, this is in the same units as the mean; on a log scale,
        this is a scalar multiple; and on a logicle scale, this is probably
        meaningless!
        
    interval : (Float, Float)
        the inverse-scaled (mean - stdev, mean + stdev) of the fitted gaussian.
        this is likely more meaningful than `stdev`, especially on the
        `logicle` scale.
        
    proportion : Float
        the proportion of events in each component of the mixture model.  only
        set if `num_components` > 1.
        
    Examples
    --------
    
    >>> gauss_op = GaussianMixture1DOp(name = "Gaussian",
    ...                                channel = "Y2-A",
    ...                                num_components = 2)
    >>> gauss_op.estimate(ex2)
    >>> gauss_op.default_view().plot(ex2)
    >>> ex3 = gauss_op.apply(ex2)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.gaussian_1d')
    friendly_id = Constant("1D Gaussian Mixture")
    
    name = CStr()
    channel = Str()
    num_components = util.PositiveInt(1)
    sigma = util.PositiveFloat(0.0, allow_zero = True)
    by = List(Str)
    scale = util.ScaleEnum
    posteriors = Bool(False)
    
    # the key is either a single value or a tuple
    _gmms = Dict(Any, Instance(mixture.GaussianMixture), transient = True)
    _scale = Instance(util.IScale, transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the Gaussian mixture model parameters
        """
        
        if experiment is None:
            raise util.CytoflowOpError("No experiment specified")

        if self.channel not in experiment.data:
            raise util.CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.channel))
       
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
                
            
        if self.num_components == 1 and self.posteriors:
            raise util.CytoflowOpError("If num_components == 1, all posteriors are 1.")
        
        if subset:
            try:
                experiment = experiment.query(subset)
            except Exception as e:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(subset)) from e
                
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
        self._scale = util.scale_factory(self.scale, experiment, channel = self.channel)
        
        gmms = {}
            
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError("Group {} had no data"
                                           .format(group))
            x = data_subset[self.channel].reset_index(drop = True)
            x = self._scale(x)
            
            # drop data that isn't in the scale range
            #x = pd.Series(self._scale(x)).dropna()
            x = x[~np.isnan(x)]
            
            gmm = mixture.GaussianMixture(n_components = self.num_components,
                                          random_state = 1)
            gmm.fit(x[:, np.newaxis])
            
            if not gmm.converged_:
                raise util.CytoflowOpError("Estimator didn't converge"
                                      " for group {0}"
                                      .format(group))
                
            # to make sure we have a stable ordering, sort the components
            # by the means (so the first component has the lowest mean, 
            # the next component has the next-lowest, etc.)
            
            sort_idx = np.argsort(gmm.means_[:, 0])
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

        if not self._gmms:
            raise util.CytoflowOpError("No model found.  Did you forget to "
                                       "call estimate()?")
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError("Experiment already has a column named {0}"
                                  .format(self.name))
            
        if not self._gmms:
            raise util.CytoflowOpError("No components found.  Did you forget to "
                                  "call estimate()?")

        if not self._scale:
            raise util.CytoflowOpError("Couldn't find _scale.  What happened??")

        if self.channel not in experiment.data:
            raise util.CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.channel))

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
                           
        if self.sigma < 0.0:
            raise util.CytoflowOpError("sigma must be >= 0.0")

        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that
            # contains all the events
            groupby = experiment.data.groupby(lambda x: True)

        for group, data_subset in groupby:
            if group not in self._gmms:
                raise util.CytoflowOpError("Can't find group in model. "
                                           "Did you call estimate()?")

        event_assignments = pd.Series([None] * len(experiment), dtype = "object")
                                      
        if self.posteriors:
            event_posteriors = pd.Series([0.0] * len(experiment))
            
        # what we DON'T want to do is iterate through event-by-event.
        # the more of this we can push into numpy, sklearn and pandas,
        # the faster it's going to be.
        
        for group, data_subset in groupby:
            if group not in self._gmms:
                # there weren't any events in this group, so we didn't get
                # a gmm.
                continue
            
            gmm = self._gmms[group]
            x = data_subset[self.channel]
            x = self._scale(x).values
                        
            # which values are missing?
            x_na = np.isnan(x)
            
            group_idx = groupby.groups[group]
            
            # make a preliminary assignment
            predicted = np.full(len(x), -1, "int")
            predicted[~x_na] = gmm.predict(x[~x_na, np.newaxis])
            
            # if we're doing sigma-based gating, for each component check
            # to see if the event is in the sigma gate.
            if self.sigma > 0.0:
                
                # make a quick dataframe with the value and the predicted
                # component
                gate_df = pd.DataFrame({"x" : x, "p" : predicted})

                # for each component, get the low and the high threshold
                for c in range(0, self.num_components):
                    lo = (gmm.means_[c][0]    # @UnusedVariable
                          - self.sigma * np.sqrt(gmm.covariances_[c][0]))
                    hi = (gmm.means_[c][0]    # @UnusedVariable
                          + self.sigma * np.sqrt(gmm.covariances_[c][0]))
                    
                    # and build an expression with numexpr so it evaluates fast!
                    gate_bool = gate_df.eval("p == @c and x >= @lo and x <= @hi").values
                    predicted[np.logical_and(predicted == c, gate_bool == False)] = -1
        
            predicted_str = pd.Series(["(none)"] * len(predicted))
            for c in range(0, self.num_components):
                predicted_str[predicted == c] = "{0}_{1}".format(self.name, c + 1)
            predicted_str[predicted == -1] = "{0}_None".format(self.name)
            predicted_str.index = group_idx

            event_assignments.iloc[group_idx] = predicted_str
                                
            if self.posteriors:
                probability = np.full((len(x), self.num_components), 0.0, "float")
                probability[~x_na, :] = gmm.predict_proba(x[~x_na, np.newaxis])
                posteriors = pd.Series([0.0] * len(predicted))
                for i in range(0, self.num_components):
                    posteriors[predicted == i] = probability[predicted == i, i]
                posteriors.index = group_idx
                event_posteriors.iloc[group_idx] = posteriors
                    
        new_experiment = experiment.clone()
        
        if self.num_components == 1 and self.sigma > 0:
            new_experiment.add_condition(self.name, "bool", event_assignments == "{0}_1".format(self.name))
        elif self.num_components > 1:
            new_experiment.add_condition(self.name, "category", event_assignments)
            
        if self.posteriors and self.num_components > 1:
            col_name = "{0}_Posterior".format(self.name)
            new_experiment.add_condition(col_name, "float", event_posteriors)

        # add the statistics
        levels = list(self.by)
        if self.num_components > 1:
            levels.append(self.name)
        
        if levels:     
            idx = pd.MultiIndex.from_product([new_experiment[x].unique() for x in levels], 
                                             names = levels)
    
            mean_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
            stdev_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
            interval_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
            prop_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()     
                                   
            for group, _ in groupby:
                gmm = self._gmms[group]
                for c in range(self.num_components):
                    if self.num_components > 1:
                        component_name = "{}_{}".format(self.name, c + 1)

                        if group is True:
                            g = [component_name]
                        elif isinstance(group, tuple):
                            g = list(group)
                            g.append(component_name)
                        else:
                            g = list([group])
                            g.append(component_name)
                        
                        if len(g) > 1:
                            g = tuple(g)
                        else:
                            g = g[0]
                    else:
                        g = group
                               
                    mean_stat.loc[g] = self._scale.inverse(gmm.means_[c][0])
                    stdev_stat.loc[g] = self._scale.inverse(np.sqrt(gmm.covariances_[c][0]))[0]
                    interval_stat.loc[g] = (self._scale.inverse(gmm.means_[c][0] - np.sqrt(gmm.covariances_[c][0][0])),
                                            self._scale.inverse(gmm.means_[c][0] + np.sqrt(gmm.covariances_[c][0][0])))
                    prop_stat.loc[g] = gmm.weights_[c]
                     
            new_experiment.statistics[(self.name, "mean")] = pd.to_numeric(mean_stat)
            new_experiment.statistics[(self.name, "stdev")] = pd.to_numeric(stdev_stat)
            new_experiment.statistics[(self.name, "interval")] = interval_stat
            if self.num_components > 1:
                new_experiment.statistics[(self.name, "proportion")] = pd.to_numeric(prop_stat)
            
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the Gaussian mixture model.
        
        Returns
        -------
            IView : an IView, call plot() to see the diagnostic plot.
        """
        return GaussianMixture1DView(op = self, **kwargs)
    
@provides(IView)
class GaussianMixture1DView(BaseOp1DView, HistogramView):
    """
    Attributes
    ----------    
    op : Instance(GaussianMixture1DOp)
        The op whose parameters we're viewing.
    """
    
    id = 'edu.mit.synbio.cytoflow.view.gaussianmixture1dview'
    friendly_id = "1D Gaussian Mixture Diagnostic Plot"
    
    def _get_facets(self):
        return [self.xfacet, self.yfacet]    
    
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot the plots.
        """

        super().plot(experiment = experiment, 
                     plot_name = plot_name, 
                     scale = self.op._scale, 
                     **kwargs)


    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):

        plot_name = kwargs.pop('plot_name', None)

        # plot the histograms
        super()._grid_plot(experiment, grid, xlim, ylim, xscale, yscale, **kwargs)

        # plot the actual distributions on top of them.
        
        row_names = grid.row_names if grid.row_names else [False]
        col_names = grid.col_names if grid.col_names else [False]
                
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
                    return {}
            else:
                if True in self.op._gmms:
                    gmm = self.op._gmms[True]
                else:
                    return {}          
                
            ax = grid.facet_axis(i, j)
                                                
            # okay.  we want to scale the gaussian curves to have the same area
            # as the plots they're over.  so, what's the total area on the plot?
            
            patch_area = 0.0
                                    
            for k in range(0, len(ax.patches)):
                
                patch = ax.patches[k]
                xy = patch.get_xy()
                patch_area += poly_area([xscale(p[0]) for p in xy], [p[1] for p in xy])
                
            # now, scale the plotted curve by the area of the total plot times
            # the proportion of it that is under that curve.
                
            for k in range(0, len(gmm.weights_)):
                pdf_scale = patch_area * gmm.weights_[k]
                
                # cheat a little
#                 pdf_scale *= 1.1
                 
                plt_min, plt_max = plt.gca().get_xlim()
                x = xscale.inverse(np.linspace(xscale(plt_min), xscale(plt_max), 500))     
                         
                mean = gmm.means_[k][0]
                stdev = np.sqrt(gmm.covariances_[k][0])
                y = stats.norm.pdf(xscale(x), mean, stdev) * pdf_scale
                color_k = k % len(sns.color_palette())
                color = sns.color_palette()[color_k]
                ax.plot(x, y, color = color)
                        
        return {}

# from http://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
def poly_area(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))