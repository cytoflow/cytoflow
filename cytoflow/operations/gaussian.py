#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
cytoflow.operations.gaussian
----------------------------
'''

import re
from warnings import warn

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from traits.api import (HasStrictTraits, Str, Dict, Any, Instance, Bool, 
                        Constant, List, provides)

import sklearn.mixture
import scipy.stats
import scipy.linalg

import pandas as pd
import numpy as np

from cytoflow.views import IView, HistogramView, ScatterplotView
import cytoflow.utility as util

from .i_operation import IOperation
from .base_op_views import By1DView, By2DView, AnnotatingView

@provides(IOperation)
class GaussianMixtureOp(HasStrictTraits):
    """
    This module fits a Gaussian mixture model with a specified number of
    components to one or more channels.
    
    If :attr:`num_components` ``> 1``, :meth:`apply` creates a new categorical 
    metadata variable named  ``name``, with possible values ``{name}_1`` .... 
    ``name_n`` where ``n`` is the number of components.  An event is assigned to 
    ``name_i`` category if it has the highest posterior probability of having been 
    produced by component ``i``.  If an event has a value that is outside the
    range of one of the channels' scales, then it is assigned to ``{name}_None``.
    
    Optionally, if :attr:`sigma` is greater than 0, :meth:`apply` creates new  
    ``boolean`` metadata variables named ``{name}_1`` ... ``{name}_n`` where 
    ``n`` is the number of components.  The column ``{name}_i`` is ``True`` if 
    the event is less than :attr:`sigma` standard deviations from the mean of 
    component ``i``.  If :attr:`num_components` is ``1``, :attr:`sigma` must be 
    greater than 0.
    
    Optionally, if :attr:`posteriors` is ``True``, :meth:`apply` creates a new 
    ``double`` metadata variables named ``{name}_1_posterior`` ... 
    ``{name}_n_posterior`` where ``n`` is the number of components.  The column 
    ``{name}_i_posterior`` contains the posterior probability that this event is 
    a member of component ``i``.
    
    Finally, the same mixture model (mean and standard deviation) may not
    be appropriate for every subset of the data.  If this is the case, you
    can use the :attr:`by` attribute to specify metadata by which to aggregate
    the data before estimating (and applying) a mixture model.  The number of 
    components must be the same across each subset, though.
    
    
    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    channels : List(Str)
        The channels to apply the mixture model to.

    scale : Dict(Str : {"linear", "logicle", "log"})
        Re-scale the data in the specified channels before fitting.  If a 
        channel is in :attr:`channels` but not in :attr:`scale`, the current 
        package-wide default (set with :func:`~.set_default_scale`) is used.

    num_components : Int (default = 1)
        How many components to fit to the data?  Must be a positive integer.

    sigma : Float
        If set, use this operation as a "gate": for each component, create 
        a new boolean variable ``{name}_i`` and if the event is within
        :attr:`sigma` standard deviations, set that variable to ``True``.
        If :attr:`num_components` is ``1``, must be ``> 0``.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting :attr:`by` to ``["Time", "Dox"]`` will fit 
        the model separately to each subset of the data with a unique combination of
        ``Time`` and ``Dox``.

    posteriors : Bool (default = False)
        If ``True``, add columns named ``{name}_{i}_posterior`` giving the 
        posterior probability that the event is in component ``i``.  Useful for 
        filtering out low-probability events.
        
    Notes
    -----
    
    We use the Mahalnobis distance as a multivariate generalization of the 
    number of standard deviations an event is from the mean of the multivariate
    gaussian.  If :math:`\\vec{x}` is an observation from a distribution with 
    mean :math:`\\vec{\\mu}` and :math:`S` is the covariance matrix, then the 
    Mahalanobis distance is :math:`\\sqrt{(x - \\mu)^T \\cdot S^{-1} \\cdot (x - \\mu)}`.
    
    Examples
    --------
    
    .. plot::
        :context: close-figs
        
        Make a little data set.
    
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
        
        >>> gm_op = flow.GaussianMixtureOp(name = 'Gauss',
        ...                                channels = ['Y2-A'],
        ...                                scale = {'Y2-A' : 'log'},
        ...                                num_components = 2)
        
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
        
    And with two channels:
    
    .. plot::
        :context: close-figs
        
        >>> gm_op = flow.GaussianMixtureOp(name = 'Gauss',
        ...                                channels = ['V2-A', 'Y2-A'],
        ...                                scale = {'V2-A' : 'log',
        ...                                         'Y2-A' : 'log'},
        ...                                num_components = 2)
        >>> gm_op.estimate(ex)   
        >>> ex2 = gm_op.apply(ex)
        >>> gm_op.default_view().plot(ex2)
        
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.gaussian')
    friendly_id = Constant("Gaussian Mixture Model")
    
    name = Str
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    num_components = util.PositiveInt(1, allow_zero = False)
    sigma = util.PositiveFloat(None, allow_zero = False, allow_none = True)
    by = List(Str)
    
    posteriors = Bool(False)
    
    # the key is either a single value or a tuple
    _gmms = Dict(Any, Instance(sklearn.mixture.GaussianMixture), transient = True)
    _scale = Dict(Str, Instance(util.IScale), transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the Gaussian mixture model parameters
        
        Parameters
        ----------
        experiment : Experiment
            The data to use to estimate the mixture parameters
            
        subset : str (default = None)
            If set, a Python expression to determine the subset of the data
            to use to in the estimation.
        """

        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
        if len(self.channels) == 0:
            raise util.CytoflowOpError('channels',
                                       "Must set at least one channel")

        for c in self.channels:
            if c not in experiment.data:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not found in the experiment"
                                      .format(c))
                
        for c in self.scale:
            if c not in self.channels:
                raise util.CytoflowOpError('channels',
                                           "Scale set for channel {0}, but it isn't "
                                           "in the experiment"
                                           .format(c))
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                
        if subset:
            try:
                experiment = experiment.query(subset)
            except:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(subset))
                
            if len(experiment) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no events"
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
                raise util.CytoflowOpError(None,
                                           "Group {} had no data"
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
                raise util.CytoflowOpError(None,
                                           "Estimator didn't converge"
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
            gmm.precisions_ = gmm.precisions_[sort_idx]
            gmm.precisions_cholesky_ = gmm.precisions_cholesky_[sort_idx]

            
            gmms[group] = gmm
            
        self._gmms = gmms
     
    def apply(self, experiment):
        """
        Assigns new metadata to events using the mixture model estimated
        in :meth:`estimate`.
        
        Returns
        -------
        Experiment
            A new :class:`.Experiment` with the new condition variables as
            described in the class documentation.  Also adds the following
            new statistics:
            
            - **mean** : Float
                the mean of the fitted gaussian in each channel for each component.
                
            - **sigma** : (Float, Float)
                the locations the mean +/- one standard deviation in each channel
                for each component.
                
            - **correlation** : Float
                the correlation coefficient between each pair of channels for each
                component.
                
            - **proportion** : Float
                the proportion of events in each component of the mixture model.  only
                added if :attr:`num_components` ``> 1``.
        """
             
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
         
        if len(self.channels) == 0:
            raise util.CytoflowOpError('channels',
                                       "Must set at least one channel")
         
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the gate's name "
                                       "before applying it!")
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name)) 
        
        if self.num_components > 1 and self.name in experiment.data.columns:
            raise util.CytoflowOpError('name',
                                       "Experiment already has a column named {0}"
                                       .format(self.name))
            
        if self.sigma is not None:
            for i in range(1, self.num_components + 1):
                cname = "{}_{}".format(self.name, i)
                if cname in experiment.data.columns:
                    raise util.CytoflowOpError('name',
                                               "Experiment already has a column named {}"
                                               .format(cname))
 
        if self.posteriors:
            for i in range(1, self.num_components + 1):
                cname = "{}_{}_posterior".format(self.name, i)
                if cname in experiment.data.columns:
                    raise util.CytoflowOpError('name',
                                               "Experiment already has a column named {}"
                                               .format(cname))               
         
        if not self._gmms:
            raise util.CytoflowOpError(None, 
                                       "No components found.  Did you forget to "
                                       "call estimate()?")
            
        for c in self.channels:
            if c not in self._scale:
                raise util.CytoflowOpError(None,
                                           "Model scale not set.  Did you forget "
                                           "to call estimate()?")
 
        for c in self.channels:
            if c not in experiment.channels:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not found in the experiment"
                                           .format(c))
        
        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
#                             
#         if self.num_components == 1 and self.sigma == 0.0:
#             raise util.CytoflowOpError('sigma',
#                                        "if num_components is 1, sigma must be > 0.0")
        
                
        if self.num_components == 1 and self.posteriors:
            warn("If num_components == 1, all posteriors will be 1",
                 util.CytoflowOpWarning)
#             raise util.CytoflowOpError('posteriors',
#                                        "If num_components == 1, all posteriors will be 1.")
         
        if self.num_components > 1:
            event_assignments = pd.Series(["{}_None".format(self.name)] * len(experiment), dtype = "object")
 
        if self.sigma is not None:
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
        prop_stat = pd.Series(name = "{} : {}".format(self.name, "proportion"),
                              index = prop_idx, 
                              dtype = np.dtype(object)).sort_index()
                  
        mean_idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [components] + [self.channels], 
                                              names = list(self.by) + ["Component"] + ["Channel"])
        mean_stat = pd.Series(name = "{} : {}".format(self.name, "mean"),
                              index = mean_idx, 
                              dtype = np.dtype(object)).sort_index()
        sigma_stat = pd.Series(name = "{} : {}".format(self.name, "sigma"),
                               index = mean_idx,
                               dtype = np.dtype(object)).sort_index()
        interval_stat = pd.Series(name = "{} : {}".format(self.name, "interval"),
                                  index = mean_idx, 
                                  dtype = np.dtype(object)).sort_index()

        corr_idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [components] + [self.channels] + [self.channels], 
                                              names = list(self.by) + ["Component"] + ["Channel_1"] + ["Channel_2"])
        corr_stat = pd.Series(name = "{} : {}".format(self.name, "correlation"),
                              index = corr_idx, 
                              dtype = np.dtype(object)).sort_index()  
                 
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
            if self.sigma is not None:
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
                p = np.full((len(x), self.num_components), 0.0)
                p[~x_na] = gmm.predict_proba(x[~x_na])
                for c in range(self.num_components):
                    event_posteriors[c].iloc[group_idx] = p[:, c]
                    
            for c in range(self.num_components):
                if len(self.by) == 0:
                    g = tuple([c + 1])
                elif hasattr(group, '__iter__') and not isinstance(group, (str, bytes)):
                    g = tuple(list(group) + [c + 1])
                else:
                    g = tuple([group] + [c + 1])

                prop_stat.at[g] = gmm.weights_[c]
                
                for cidx1, channel1 in enumerate(self.channels):
                    g2 = tuple(list(g) + [channel1])
                    mean_stat.at[g2] = self._scale[channel1].inverse(gmm.means_[c, cidx1])
                    
                    s, corr = util.cov2corr(gmm.covariances_[c])
                    sigma_stat[g2] = (self._scale[channel1].inverse(s[cidx1]))
                    interval_stat.at[g2] = (self._scale[channel1].inverse(gmm.means_[c, cidx1] - s[cidx1]),
                                             self._scale[channel1].inverse(gmm.means_[c, cidx1] + s[cidx1]))
            
                    for cidx2, channel2 in enumerate(self.channels):
                        g3 = tuple(list(g2) + [channel2])
                        corr_stat[g3] = corr[cidx1, cidx2]
                        
                    corr_stat.drop(tuple(list(g2) + [channel1]), inplace = True)

        new_experiment = experiment.clone()
          
        if self.num_components > 1:
            new_experiment.add_condition(self.name, "category", event_assignments)
            
        if self.sigma is not None:
            for c in range(self.num_components):
                gate_name = "{}_{}".format(self.name, c + 1)
                new_experiment.add_condition(gate_name, "bool", event_gate[c])              
                
        if self.posteriors:
            for c in range(self.num_components):
                post_name = "{}_{}_posterior".format(self.name, c + 1)
                new_experiment.add_condition(post_name, "double", event_posteriors[c])
                
        new_experiment.statistics[(self.name, "mean")] = pd.to_numeric(mean_stat)
        new_experiment.statistics[(self.name, "sigma")] = sigma_stat
        new_experiment.statistics[(self.name, "interval")] = interval_stat
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
                raise util.CytoflowViewError('channels',
                                             "Channel {} isn't in the operation's channels"
                                             .format(c))
                
        for s in scale:
            if s not in self.channels:
                raise util.CytoflowViewError('scale',
                                             "Channel {} isn't in the operation's channels"
                                             .format(s))
            
        for c in channels:
            if c not in scale:
                scale[c] = util.get_default_scale()
            
        if len(channels) == 0:
            raise util.CytoflowViewError('channels',
                                         "Must specify at least one channel for a default view")
        elif len(channels) == 1:
            v = GaussianMixture1DView(op = self)
            v.trait_set(channel = channels[0], 
                        scale = scale[channels[0]], 
                        **kwargs)
            return v
        
        elif len(channels) == 2:
            v = GaussianMixture2DView(op = self)
            v.trait_set(xchannel = channels[0], 
                        ychannel = channels[1],
                        xscale = scale[channels[0]],
                        yscale = scale[channels[1]], 
                        **kwargs)
            return v
        
        else:
            raise util.CytoflowViewError('channels',
                                         "Can't specify more than two channels for a default view")

@provides(IView)
class GaussianMixture1DView(By1DView, AnnotatingView, HistogramView):
    """
    A default view for :class:`GaussianMixtureOp` that plots the histogram
    of a single channel, then the estimated Gaussian distributions on top of it.
    
    Attributes
    ----------    

    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.gaussianmixture1dview')
    friendly_id = Constant("1D Gaussian Mixture Diagnostic Plot")
    
    channel = Str
    scale = util.ScaleEnum
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        
        Parameters
        ----------
        """

        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if self.op.num_components == 1:
            annotation_facet = self.op.name + "_1"
        else:
            annotation_facet = self.op.name
            
        view, trait_name = self._strip_trait(annotation_facet)
        
        if self.channel in self.op._scale:
            scale = self.op._scale[self.channel]
        else:
            scale = util.scale_factory(self.scale, experiment, channel = self.channel)
    
        super(GaussianMixture1DView, view).plot(experiment,
                                                annotation_facet = annotation_facet,
                                                annotation_trait = trait_name,
                                                annotations = self.op._gmms,
                                                scale = scale,
                                                **kwargs)
        
        
    def _annotation_plot(self, axes, annotation, annotation_facet, 
                         annotation_value, annotation_color, **kwargs):

        # annotation is an instance of mixture.GaussianMixture
        gmm = annotation
        
        if annotation_value is None:
            for i in range(len(gmm.means_)):
                self._annotation_plot(axes, annotation, annotation_facet, 
                                      i, annotation_color, **kwargs)
            return
        elif type(annotation_value) is str:
            try:
                idx_re = re.compile(annotation_facet + '_(\d+)')
                idx = idx_re.match(annotation_value).group(1)
                idx = int(idx) - 1            
            except:
                return 
        elif isinstance(annotation_value, np.bool_):
            if annotation_value:
                idx = 0
            else:
                return
        else:
            idx = annotation_value
              
        kwargs.setdefault('orientation', 'vertical')
            
        if kwargs['orientation'] == 'horizontal':
            scale = kwargs['yscale']
            patch_area = 0.0
                                     
            for k in range(0, len(axes.patches)):
                patch = axes.patches[k]
                if isinstance(patch, Polygon):
                    xy = patch.get_xy()
                    patch_area += poly_area([scale(p[1]) for p in xy], [p[0] for p in xy])
                elif isinstance(patch, Rectangle):
                    for xy in patch.get_path().to_polygons():
                        patch_area += poly_area([p[1] for p in xy], [p[0] for p in xy])
            
            plt_min, plt_max = plt.gca().get_ylim()
            y = scale.inverse(np.linspace(scale(scale.clip(plt_min)), 
                                          scale(scale.clip(plt_max)), 500))   
            pdf_scale = patch_area * gmm.weights_[idx]
            mean = gmm.means_[idx][0]
            stdev = np.sqrt(gmm.covariances_[idx][0])
            x = scipy.stats.norm.pdf(scale(y), mean, stdev) * pdf_scale
            axes.plot(x, y, color = annotation_color)
        else:
            scale = kwargs['xscale']
            patch_area = 0.0
                                     
            for k in range(0, len(axes.patches)):
                patch = axes.patches[k]
                if isinstance(patch, Polygon):
                    xy = patch.get_xy()
                    patch_area += poly_area([scale(p[0]) for p in xy], [p[1] for p in xy])
                elif isinstance(patch, Rectangle):
                    for xy in patch.get_path().to_polygons():
                        patch_area += poly_area([p[0] for p in xy], [p[1] for p in xy])
            
            plt_min, plt_max = plt.gca().get_xlim()
            x = scale.inverse(np.linspace(scale(scale.clip(plt_min)), 
                                          scale(scale.clip(plt_max)), 500))   
            pdf_scale = patch_area * gmm.weights_[idx]
            mean = gmm.means_[idx][0]
            stdev = np.sqrt(gmm.covariances_[idx][0])
            y = scipy.stats.norm.pdf(scale(x), mean, stdev) * pdf_scale
            axes.plot(x, y, color = annotation_color)
                
# from http://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
def poly_area(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

# a few more imports for drawing scaled ellipses
        
import matplotlib.path as path
import matplotlib.patches as patches
import matplotlib.transforms as transforms
    
@provides(IView)
class GaussianMixture2DView(By2DView, AnnotatingView, ScatterplotView):
    """
    A default view for :class:`GaussianMixtureOp` that plots the scatter plot
    of a two channels, then the estimated 2D Gaussian distributions on top of it.
    
    Attributes
    ----------
   
    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.gaussianmixture2dview')
    friendly_id = Constant("2D Gaussian Mixture Diagnostic Plot")
        
    xchannel = Str
    xscale = util.ScaleEnum
    ychannel = Str
    yscale = util.ScaleEnum
        
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        
        Parameters
        ----------
        """

        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if self.op.num_components == 1:
            annotation_facet = self.op.name + "_1"
        else:
            annotation_facet = self.op.name
        
        view, trait_name = self._strip_trait(annotation_facet)
        
        if self.xchannel in self.op._scale:
            xscale = self.op._scale[self.xchannel]
        else:
            xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)

        if self.ychannel in self.op._scale:
            yscale = self.op._scale[self.ychannel]
        else:
            yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
    
        super(GaussianMixture2DView, view).plot(experiment,
                                                annotation_facet = annotation_facet,
                                                annotation_trait = trait_name,
                                                annotations = self.op._gmms,
                                                xscale = xscale,
                                                yscale = yscale,
                                                **kwargs)

    def _annotation_plot(self, axes, annotation, annotation_facet, 
                         annotation_value, annotation_color, **kwargs):

        # annotation is an instance of mixture.GaussianMixture
        gmm = annotation
        
        if annotation_value is None:
            for i in range(len(gmm.means_)):
                self._annotation_plot(axes, annotation, annotation_facet, i, 
                                      annotation_color, **kwargs)
            return
        elif isinstance(annotation_value, str):
            try:
                idx_re = re.compile(annotation_facet + '_(\d+)')
                idx = idx_re.match(annotation_value).group(1)
                idx = int(idx) - 1             
            except:
                return
        elif isinstance(annotation_value, np.bool_):
            if annotation_value:
                idx = 0
            else:
                return
        else:
            idx = annotation_value
            
        xscale = kwargs['xscale']
        yscale = kwargs['yscale']
        
        mean = gmm.means_[idx]
        covar = gmm.covariances_[idx]
        
        v, w = scipy.linalg.eigh(covar)
        u = w[0] / scipy.linalg.norm(w[0])
        
        #rotation angle (in degrees)
        t = np.arctan(u[1] / u[0])
        t = 180 * t / np.pi
        
        # in order to scale the ellipses correctly, we have to make them
        # ourselves out of an affine-scaled unit circle.  The interface
        # is the same as matplotlib.patches.Ellipse
        
        _plot_ellipse(axes,
                      xscale,
                      yscale,
                      mean,
                      np.sqrt(v[0]),
                      np.sqrt(v[1]),
                      180 + t,
                      color = annotation_color,
                      fill = False,
                      linewidth = 2)

        _plot_ellipse(axes,
                      xscale,
                      yscale, 
                      mean,
                      np.sqrt(v[0]) * 2,
                      np.sqrt(v[1]) * 2,
                      180 + t,
                      color = annotation_color,
                      fill = False,
                      linewidth = 2,
                      alpha = 0.66)
        
        _plot_ellipse(axes,
                      xscale,
                      yscale, 
                      mean,
                      np.sqrt(v[0]) * 3,
                      np.sqrt(v[1]) * 3,
                      180 + t,
                      color = annotation_color,
                      fill = False,
                      linewidth = 2,
                      alpha = 0.33)
                    
def _plot_ellipse(ax, xscale, yscale, center, width, height, angle, **kwargs):
    tf = transforms.Affine2D() \
         .scale(width, height) \
         .rotate_deg(angle) \
         .translate(*center)
         
    tf_path = tf.transform_path(path.Path.unit_circle())
    v = tf_path.vertices
    v = np.vstack((xscale.inverse(v[:, 0]),
                   yscale.inverse(v[:, 1]))).T

    scaled_path = path.Path(v, tf_path.codes)
    scaled_patch = patches.PathPatch(scaled_path, **kwargs)
    ax.add_patch(scaled_patch)
            
            
util.expand_class_attributes(GaussianMixture1DView)
util.expand_method_parameters(GaussianMixture1DView, GaussianMixture1DView.plot)

util.expand_class_attributes(GaussianMixture2DView)
util.expand_method_parameters(GaussianMixture2DView, GaussianMixture2DView.plot)