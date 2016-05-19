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
Created on Dec 16, 2015

@author: brian
'''

from __future__ import division, absolute_import

import warnings, logging

from traits.api import (HasStrictTraits, Str, CStr, Dict, Any, Instance, Bool, 
                        Constant, List, provides, DelegatesTo, CFloat)
import numpy as np
import matplotlib.pyplot as plt
from sklearn import mixture
from scipy import stats
import pandas as pd
import seaborn as sns

import cytoflow.views
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
        Re-scale the data before fitting the data?  
        
    posteriors : Bool (default = False)
        If `True`, add a column named `{Name}_Posterior` giving the posterior
        probability that the event is in the component to which it was
        assigned.  Useful for filtering out low-probability events.
        
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
    sigma = CFloat(0.0)
    by = List(Str)
    scale = util.ScaleEnum
    posteriors = Bool(False)
    
    # the key is either a single value or a tuple
    _gmms = Dict(Any, Instance(mixture.GMM), transient = True)
    _scale = Instance(util.IScale, transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the Gaussian mixture model parameters
        """
        
        if not experiment:
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
                
            
        if self.num_components == 1 and self.sigma == 0.0:
            raise util.CytoflowOpError("If num_components == 1, sigma must be > 0")
                
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda x: True)
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        self._scale = util.scale_factory(self.scale, experiment, self.channel)
            
        for group, data_subset in groupby:
            x = data_subset[self.channel].reset_index(drop = True)
            x = self._scale(x)
            
            # drop data that isn't in the scale range
            #x = pd.Series(self._scale(x)).dropna()
            x = x[~np.isnan(x)]
            
            gmm = mixture.GMM(n_components = self.num_components,
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
            gmm.covars_ = gmm.covars_[sort_idx]
           
            self._gmms[group] = gmm
    
    def apply(self, experiment):
        """
        Assigns new metadata to events using the mixture model estimated
        in `estimate`.
        """
            
        if not experiment:
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

        if not self._scale:
            raise util.CytoflowOpError("Couldn't find _scale.  What happened??")

        if self.channel not in experiment.data:
            raise util.CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.channel))

            
        if (self.name + "_Posterior") in experiment.data:
            raise util.CytoflowOpError("Column {0} already found in the experiment"
                                  .format(self.name + "_Posterior"))

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
            gmm = self._gmms[group]
            x = data_subset[self.channel]
            x = self._scale(x)
            
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
                          - self.sigma * np.sqrt(gmm.covars_[c][0]))
                    hi = (gmm.means_[c][0]    # @UnusedVariable
                          + self.sigma * np.sqrt(gmm.covars_[c][0]))
                    
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
        
        if self.num_components == 1:
            new_experiment.add_condition(self.name, "bool", event_assignments == "{0}_1".format(self.name))
        else:
            new_experiment.add_condition(self.name, "category", event_assignments)
            
        if self.posteriors:
            col_name = "{0}_Posterior".format(self.name)
            new_experiment.add_condition(col_name, "float", event_posteriors)
            
        new_experiment.history.append(self.clone_traits())
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the Gaussian mixture model.
        
        Returns
        -------
            IView : an IView, call plot() to see the diagnostic plot.
        """
        return GaussianMixture1DView(op = self, **kwargs)
    
@provides(cytoflow.views.IView)
class GaussianMixture1DView(cytoflow.views.HistogramView):
    """
    Attributes
    ----------
    name : Str
        The instance name (for serialization, UI etc.)
        
    op : Instance(GaussianMixture1DOp)
        The op whose parameters we're viewing.
        
    num_plots: Property(Int)
        A read-only property that computes the number of plots from the 
        
        
    plot_idx : Python (default: None)
        The subset of data to display.  Must match one of the keys of 
        `op._gmms`.  If `None` (the default), display a plot for each subset.
    """
    
    id = 'edu.mit.synbio.cytoflow.view.gaussianmixture1dview'
    friendly_id = "1D Gaussian Mixture Diagnostic Plot"
    
    # TODO - why can't I use GaussianMixture1DOp here?
    op = Instance(IOperation)
    name = DelegatesTo('op', transient = True)
    channel = DelegatesTo('op', transient = True)
    scale = DelegatesTo('op', transient = True)
    huefacet = DelegatesTo('op', 'name', transient = True)
    
        
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce.  The values returned can be passed to "plot".
        """
        
        class plot_enum(object):
            
            def __init__(self, op, experiment):
                self._iter = None
                self._returned = False
                if op.by:
                    self._iter = experiment.data.groupby(op.by).__iter__()
                
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
            
        return plot_enum(self.op, experiment)
    
    
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot the plots.
        """
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if self.xfacet:
            raise util.CytoflowViewError("ThresholdSelection.xfacet must be empty")
        
        if self.yfacet:
            raise util.CytoflowViewError("ThresholdSelection.yfacet must be empty")  
              
        if self.op.by and not plot_name:
            for plot in self.enum_plots(experiment):
                self.plot(experiment, plot, **kwargs)
                plt.title("{0} = {1}".format(self.op.by, plot_name))
            return
                
        temp_experiment = experiment.clone()
        
        if plot_name:
            groupby = experiment.data.groupby(self.op.by)
            temp_experiment.data = groupby.get_group(plot_name)
            temp_experiment.data.reset_index(drop = True, inplace = True)
        
        try:
            temp_experiment = self.op.apply(temp_experiment)
            cytoflow.HistogramView.plot(self, temp_experiment, **kwargs)
        except util.CytoflowOpError as e:
            warnings.warn(e.__str__(), util.CytoflowViewWarning)
            cytoflow.HistogramView(channel = self.channel,
                                   scale = self.scale).plot(temp_experiment, **kwargs)
            return
        
        # get the scale back from the op
        scale = self.op._scale
        
        # plot the actual distribution on top of it.
        
        # we want to scale the plots so they have the same area under the
        # curve as the histograms.  it used to be that we got the area from
        # repeating the assignments, then calculating bin widths, etc.  but
        # really, if we just plotted the damn thing already, we can get the
        # area of the plot from the Polygon patch that we just plotted!

        gmm = self.op._gmms[plot_name] if plot_name else self.op._gmms[True]
                              
        for i in range(0, len(gmm.means_)):
            patch = plt.gca().patches[i]
            xy = patch.get_xy()
            pdf_scale = poly_area([scale(p[0]) for p in xy], [p[1] for p in xy])
            
            # cheat a little
            pdf_scale *= 1.2
            
            plt_min, plt_max = plt.gca().get_xlim()
            x = scale.inverse(np.linspace(scale(plt_min), scale(plt_max), 500))     
                   
            mean = gmm.means_[i][0]
            stdev = np.sqrt(gmm.covars_[i][0])
            y = stats.norm.pdf(scale(x), mean, stdev) * pdf_scale
            color_i = i % len(sns.color_palette())
            color = sns.color_palette()[color_i]
            plt.plot(x, y, color = color)      

# from http://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
def poly_area(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))