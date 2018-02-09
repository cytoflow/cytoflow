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
cytoflow.operations.gaussian_1d
-------------------------------
'''

import re
from warnings import warn

from traits.api import (HasStrictTraits, Str, CStr, Dict, Any, Instance, Bool, 
                        Constant, List, provides)
import numpy as np
import matplotlib.pyplot as plt
import sklearn.mixture as mixture
import scipy.stats as stats
import pandas as pd

from cytoflow.views import IView, HistogramView
from .base_op_views import By1DView, AnnotatingView
import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class GaussianMixture1DOp(HasStrictTraits):
    """
    This module fits a Gaussian mixture model with a specified number of
    components to a channel.
    
    .. warning:: 
    
        :class:`GaussianMixture1DOp` is **DEPRECATED** and will be removed
        in a future release.  It doesn't correctly handle the case where an 
        event is present in more than one component.  Please use
        :class:`GaussianMixtureOp` instead!
    
    Creates a new categorical metadata variable named :attr:`name`, with possible
    values ``name_1`` .... ``name_n`` where ``n`` is the number of components.
    An event is assigned to ``name_i`` category if it falls within :attr:`sigma`
    standard deviations of the component's mean.  If that is true for multiple
    categories (or if :attr:`sigma` is ``0.0``), the event is assigned to the category 
    with the highest posterior probability.  If the event doesn't fall into
    any category, it is assigned to ``name_None``.
    
    As a special case, if :attr:`num_components` is `1` and :attr:`sigma` 
    ``> 0.0``, then the new condition is boolean, ``True`` if the event fell in 
    the gate and ``False`` otherwise.
    
    Optionally, if :attr:`posteriors` is ``True``, this module will also 
    compute the posterior probability of each event in its assigned component, 
    returning it in a new colunm named ``{Name}_Posterior``.
    
    Finally, the same mixture model (mean and standard deviation) may not
    be appropriate for every subset of the data.  If this is the case, you
    can use the :attr:`by` attribute to specify metadata by which to aggregate
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
        
        
    Examples
    --------
    
    Make a little data set.
    
    .. plot::
        :context: close-figs
            
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
    
    Create and parameterize the operation.
    
    .. plot::
        :context: close-figs
        
        >>> gm_op = flow.GaussianMixture1DOp(name = 'GM',
        ...                                  channel = 'Y2-A',
        ...                                  scale = 'log',
        ...                                  num_components = 2)
        
    Estimate the clusters
    
    .. plot::
        :context: close-figs
        
        >>> gm_op.estimate(ex)
        
    Plot a diagnostic view
    
    .. plot::
        :context: close-figs
        
        >>> gm_op.default_view().plot(ex)

    Apply the gate
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = gm_op.apply(ex)

    Plot a diagnostic view with the event assignments
    
    .. plot::
        :context: close-figs
        
        >>> gm_op.default_view().plot(ex2)

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
    
    # the key is a set
    _gmms = Dict(Any, Instance(mixture.GaussianMixture), transient = True)
    _scale = Instance(util.IScale, transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the Gaussian mixture model parameters.
        
        Parameters
        ----------
        experiment : Experiment
            The data to use to estimate the mixture parameters
            
        subset : str (default = None)
            If set, a Python expression to determine the subset of the data
            to use to in the estimation.
        """
        
        warn("GaussianMixture1DOp is DEPRECATED.  Please use GaussianMixtureOp.",
             util.CytoflowOpWarning)
        
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")

        if self.channel not in experiment.data:
            raise util.CytoflowOpError('channel',
                                       "Column {0} not found in the experiment"
                                       .format(self.channel))
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
            
        if self.num_components == 1 and self.posteriors:
            raise util.CytoflowOpError('num_components',
                                       "If num_components == 1, all posteriors are 1.")
        
        if subset:
            try:
                experiment = experiment.query(subset)
            except Exception as e:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' isn't valid"
                                           .format(subset)) from e
                
            if len(experiment) == 0:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' returned no events"
                                           .format(subset))
                
        if self.by:
            by = sorted(self.by)
            groupby = experiment.data.groupby(by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True)
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        self._scale = util.scale_factory(self.scale, experiment, channel = self.channel)
        
        gmms = {}
            
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError(None, 
                                           "Group {} had no data".format(group))
            x = data_subset[self.channel].reset_index(drop = True)
            x = self._scale(x)
            
            # drop data that isn't in the scale range
            #x = pd.Series(self._scale(x)).dropna()
            x = x[~np.isnan(x)]
            
            gmm = mixture.GaussianMixture(n_components = self.num_components,
                                          random_state = 1)
            gmm.fit(x[:, np.newaxis])
            
            if not gmm.converged_:
                raise util.CytoflowOpError(None,
                                           "Estimator didn't converge"
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
        in :meth:`estimate`.
        
        Returns
        -------
        Experiment
            A new :class:`.Experiment`, with a new column named :attr:`name`,
            and possibly one named :attr:`name` _Posterior.  Also the following
            new :attr:`~.Experiment.statistics`:
            
            - **mean** : Float
                the mean of the fitted gaussian
            
            - **stdev** : Float
                the inverse-scaled standard deviation of the fitted gaussian.  on a 
                linear scale, this is in the same units as the mean; on a log scale,
                this is a scalar multiple; and on a logicle scale, this is probably
                meaningless!
            
            - **interval** : (Float, Float)
                the inverse-scaled (mean - stdev, mean + stdev) of the fitted gaussian.
                this is likely more meaningful than ``stdev``, especially on the
                ``logicle`` scale.
            
            - **proportion** : Float
                the proportion of events in each component of the mixture model.  only
                set if :attr:`num_components` ``> 1``.
             
        """
        
        warn("GaussianMixture1DOp is DEPRECATED.  Please use GaussianMixtureOp.",
             util.CytoflowOpWarning)
            
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")

        if not self._gmms:
            raise util.CytoflowOpError(None,
                                       "No model found.  Did you forget to "
                                       "call estimate()?")
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the gate's name "
                                       "before applying it!")

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError('name',
                                       "Experiment already has a column named {0}"
                                       .format(self.name))
            
        if not self._gmms:
            raise util.CytoflowOpError(None,
                                       "No components found.  Did you forget to "
                                       "call estimate()?")

        if not self._scale:
            raise util.CytoflowOpError(None,
                                       "Couldn't find _scale.  What happened??")

        if self.channel not in experiment.data:
            raise util.CytoflowOpError('channel',
                                       "Column {0} not found in the experiment"
                                       .format(self.channel))

        if self.posteriors:
            col_name = "{0}_Posterior".format(self.name)
            if col_name in experiment.data:
                raise util.CytoflowOpError('posteriors',
                                           "Column {0} already found in the experiment"
                              .format(col_name))
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                           
        if self.sigma < 0.0:
            raise util.CytoflowOpError('sigma',
                                       "sigma must be >= 0.0")

        if self.by:
            by = sorted(self.by)
            groupby = experiment.data.groupby(by)
        else:
            # use a lambda expression to return a group that
            # contains all the events
            groupby = experiment.data.groupby(lambda _: True)

        event_assignments = pd.Series([None] * len(experiment), dtype = "object")
                                      
        if self.posteriors:
            event_posteriors = pd.Series([0.0] * len(experiment))
            
        # what we DON'T want to do is iterate through event-by-event.
        # the more of this we can push into numpy, sklearn and pandas,
        # the faster it's going to be.
        
        for group, data_subset in groupby:
            
            # if there weren't any events in this group, there's no gmm
            if group not in self._gmms:
                warn("There wasn't a GMM for data subset {}".format(group),
                     util.CytoflowOpWarning)
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
                    # ugh - this breaks indexing in Pandas >= 0.21
#                     interval_stat.loc[g] = (self._scale.inverse(gmm.means_[c][0] - np.sqrt(gmm.covariances_[c][0][0])),
#                                             self._scale.inverse(gmm.means_[c][0] + np.sqrt(gmm.covariances_[c][0][0])))
                    prop_stat.loc[g] = gmm.weights_[c]
                     
            new_experiment.statistics[(self.name, "mean")] = pd.to_numeric(mean_stat)
            new_experiment.statistics[(self.name, "stdev")] = pd.to_numeric(stdev_stat)
#             new_experiment.statistics[(self.name, "interval")] = interval_stat
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
        warn("GaussianMixture1DOp is DEPRECATED.  Please use GaussianMixtureOp.",
             util.CytoflowOpWarning)
        
        return GaussianMixture1DView(op = self, **kwargs)
    
@provides(IView)
class GaussianMixture1DView(By1DView, AnnotatingView, HistogramView):
    """
    A diagnostic view for a GaussianMixture1DOp.
    
    Attributes
    ----------    
    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.gaussianmixture1dview')
    friendly_id = Constant("1D Gaussian Mixture Diagnostic Plot")
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        
        Parameters
        ----------
        """
        
        view, trait_name = self._strip_trait(self.op.name)
    
        super(GaussianMixture1DView, view).plot(experiment,
                                                annotation_facet = self.op.name,
                                                annotation_trait = trait_name,
                                                annotations = self.op._gmms,
                                                scale = self.op._scale,
                                                **kwargs)
        
        
    def _annotation_plot(self, axes, xlim, ylim, xscale, yscale, annotation, annotation_facet, annotation_value, annotation_color):

        # annotation is an instance of mixture.GaussianMixture
        gmm = annotation
        
        if annotation_value is None:
            for i in range(len(gmm.means_)):
                self._annotation_plot(axes, xlim, ylim, xscale, yscale, annotation, annotation_facet, i, annotation_color)
            return
        elif type(annotation_value) is str:
            try:
                idx_re = re.compile(annotation_facet + '_(\d+)')
                idx = idx_re.match(annotation_value).group(1)
                idx = int(idx) - 1     
            except:
                return        
        else:
            idx = annotation_value
              
        patch_area = 0.0
                                 
        for k in range(0, len(axes.patches)):
            patch = axes.patches[k]
            xy = patch.get_xy()
            patch_area += poly_area([xscale(p[0]) for p in xy], [p[1] for p in xy])
        
        plt_min, plt_max = plt.gca().get_xlim()
        x = xscale.inverse(np.linspace(xscale(plt_min), xscale(plt_max), 500))   
        pdf_scale = patch_area * gmm.weights_[idx]
        mean = gmm.means_[idx][0]
        stdev = np.sqrt(gmm.covariances_[idx][0])
        y = stats.norm.pdf(xscale(x), mean, stdev) * pdf_scale
        axes.plot(x, y, color = annotation_color)
                
# from http://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
def poly_area(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

util.expand_class_attributes(GaussianMixture1DView)
util.expand_method_parameters(GaussianMixture1DView, GaussianMixture1DView.plot)