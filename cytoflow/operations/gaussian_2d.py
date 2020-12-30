#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
cytoflow.operations.gaussian_2d
-------------------------------
'''
import re
from warnings import warn

from traits.api import (HasStrictTraits, Str, CStr, Dict, Any, Instance, Bool, 
                        Constant, List, provides)

import numpy as np
from sklearn import mixture
from scipy import linalg
import pandas as pd

from cytoflow.views import IView, ScatterplotView
import cytoflow.utility as util

from .i_operation import IOperation
from .base_op_views import By2DView, AnnotatingView

@provides(IOperation)
class GaussianMixture2DOp(HasStrictTraits):
    """
    This module fits a 2D Gaussian mixture model with a specified number of
    components to a pair of channels.
    
    .. warning:: 
    
        :class:`GaussianMixture2DOp` is **DEPRECATED** and will be removed
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
    
    As a special case, if :attr:`num_components` is ``1`` and :attr:`sigma` 
    ``> 0.0``, then the new condition is boolean, ``True`` if the event fell 
    in the gate and ``False`` otherwise.
    
    Optionally, if :attr:`posteriors` is ``True``, this module will also compute the 
    posterior probability of each event in its assigned component, returning
    it in a new colunm named ``{Name}_Posterior``.
    
    Finally, the same mixture model (mean and standard deviation) may not
    be appropriate for every subset of the data.  If this is the case, you
    can use the :attr:`by` attribute to specify metadata by which to aggregate
    the data before estimating (and applying) a mixture model.  The number of 
    components is the same across each subset, though.
    
    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    xchannel : Str
        The X channel to apply the mixture model to.
        
    ychannel : Str
        The Y channel to apply the mixture model to.

    xscale : {"linear", "logicle", "log"} (default = "linear")
        Re-scale the data on the X acis before fitting the data?  

    yscale : {"linear", "logicle", "log"} (default = "linear")
        Re-scale the data on the Y axis before fitting the data?  
        
    num_components : Int (default = 1)
        How many components to fit to the data?  Must be positive.

    sigma : Float (default = 0.0)
        How many standard deviations on either side of the mean to include
        in each category?  If an event is in multiple components, assign it
        to the component with the highest posterior probability.  If 
        :attr:`sigma` is ``0.0``, categorize *all* the data by assigning each event to
        the component with the highest posterior probability.  Must be ``>= 0.0``.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting :attr:`by` to ``["Time", "Dox"]`` will fit
        the model separately to each subset of the data with a unique combination of
        ``Time`` and ``Dox``.

    posteriors : Bool (default = False)
        If ``True``, add a column named ``{Name}_Posterior`` giving the posterior
        probability that the event is in the component to which it was
        assigned.  Useful for filtering out low-probability events.

    
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
        
        >>> gm_op = flow.GaussianMixture2DOp(name = 'Flow',
        ...                          xchannel = 'V2-A',
        ...                          xscale = 'log',
        ...                          ychannel = 'Y2-A',
        ...                          yscale = 'log',
        ...                          num_components = 2)
        
    Estimate the clusters
    
    .. plot::
        :context: close-figs
        
        >>> gm_op.estimate(ex)
        
    Plot a diagnostic view with the distributions
    
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
    
    id = Constant('edu.mit.synbio.cytoflow.operations.gaussian_2d')
    friendly_id = Constant("2D Gaussian Mixture")
    
    name = CStr()
    xchannel = Str()
    ychannel = Str()
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    num_components = util.PositiveInt
    sigma = util.PositiveFloat(0.0, allow_zero = True)
    by = List(Str)
    
    posteriors = Bool(False)
    
    # the key is either a single value or a tuple
    _gmms = Dict(Any, Instance(mixture.GaussianMixture), transient = True)
    _xscale = Instance(util.IScale, transient = True)
    _yscale = Instance(util.IScale, transient = True)
    
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
        
        warn("GaussianMixture2DOp is DEPRECATED.  Please use GaussianMixtureOp.",
             util.CytoflowOpWarning)
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")

        if self.xchannel not in experiment.data:
            raise util.CytoflowOpError('xchannel',
                                       "Column {0} not found in the experiment"
                                       .format(self.xchannel))
            
        if self.ychannel not in experiment.data:
            raise util.CytoflowOpError('ychannel',
                                       "Column {0} not found in the experiment"
                                       .format(self.ychannel))
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                
        if self.num_components == 1 and self.posteriors:
            raise util.CytoflowOpError('posteriors',
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
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True)
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        self._xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)
        self._yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
        
        gmms = {}
            
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError(None,
                                           "Group {} had no data"
                                           .format(group))
            x = data_subset.loc[:, [self.xchannel, self.ychannel]]
            x[self.xchannel] = self._xscale(x[self.xchannel])
            x[self.ychannel] = self._yscale(x[self.ychannel])
            
            # drop data that isn't in the scale range
            x = x[~(np.isnan(x[self.xchannel]) | np.isnan(x[self.ychannel]))]
            x = x.values
            
            gmm = mixture.GaussianMixture(n_components = self.num_components,
                                          covariance_type = "full",
                                          random_state = 1)
            gmm.fit(x)
            
            if not gmm.converged_:
                raise util.CytoflowOpError(None,
                                           "Estimator didn't converge"
                                           " for group {0}"
                                           .format(group))
                
            # in the 1D version, we sort the components by the means -- so
            # the first component has the lowest mean, the second component
            # has the next-lowest mean, etc.  that doesn't work in a 2D area,
            # obviously.
            
            # instead, we assume that the clusters are likely (?) to be
            # arranged along *one* of the axes, so we take the |norm| of the
            # x,y mean of each cluster and sort that way.
            
            norms = (gmm.means_[:, 0] ** 2 + gmm.means_[:, 1] ** 2) ** 0.5
            sort_idx = np.argsort(norms)
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
            A new :class:`.Experiment` with a column named :attr:`name` and
            optionally one named :attr:`name` ``_Posterior``.  Also includes
            the following new statistics:

            - **xmean** : Float
                the mean of the fitted gaussian in the x dimension.
                
            - **ymean** : Float
                the mean of the fitted gaussian in the y dimension.
                
            - **proportion** : Float
                the proportion of events in each component of the mixture model.  only
                set if :attr:`num_components` ``> 1``.
        
            PS -- if someone has good ideas for summarizing spread in a 2D (non-isotropic)
            Gaussian, or other useful statistics, let me know!

        """
           
        warn("GaussianMixture2DOp is DEPRECATED.  Please use GaussianMixtureOp.",
             util.CytoflowOpWarning)
            
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
        if not self.xchannel:
            raise util.CytoflowOpError('xchannel',
                                       "Must set X channel")

        if not self.ychannel:
            raise util.CytoflowOpError('ychannel',
                                       "Must set Y channel")
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the gate's name "
                                       "before applying it!")
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name))  

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError('name',
                                       "Experiment already has a column named {0}"
                                       .format(self.name))
        
        if not self._gmms:
            raise util.CytoflowOpError(None,
                                       "No components found.  Did you forget to "
                                       "call estimate()?")
            
        if not self._xscale:
            raise util.CytoflowOpError(None,
                                       "Couldn't find _xscale.  What happened??")
        
        if not self._yscale:
            raise util.CytoflowOpError(None,
                                       "Couldn't find _yscale.  What happened??")

        if self.xchannel not in experiment.data:
            raise util.CytoflowOpError('xchannel',
                                       "Column {0} not found in the experiment"
                                       .format(self.xchannel))

        if self.ychannel not in experiment.data:
            raise util.CytoflowOpError('ychannel',
                                       "Column {0} not found in the experiment"
                                       .format(self.ychannel))
            
        if self.posteriors:
            col_name = "{0}_Posterior".format(self.name)
            if col_name in experiment.data:
                raise util.CytoflowOpError('channels',
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
        
        event_assignments = pd.Series([None] * len(experiment), dtype = "object")

        if self.posteriors:
            event_posteriors = pd.Series([0.0] * len(experiment))
            
        # what we DON'T want to do is iterate through event-by-event.
        # the more of this we can push into numpy, sklearn and pandas,
        # the faster it's going to be.  for example, this is why
        # we don't use Ellipse.contains().  
        
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
            x = data_subset.loc[:, [self.xchannel, self.ychannel]]
            x[self.xchannel] = self._xscale(x[self.xchannel])
            x[self.ychannel] = self._yscale(x[self.ychannel])
            
            # which values are missing?
            x_na = np.isnan(x[self.xchannel]) | np.isnan(x[self.ychannel])
            x_na = x_na.values
            
            x = x.values
            group_idx = groupby.groups[group]

            # make a preliminary assignment
            predicted = np.full(len(x), -1, "int")
            predicted[~x_na] = gmm.predict(x[~x_na])
            
            # if we're doing sigma-based gating, for each component check
            # to see if the event is in the sigma gate.
            if self.sigma > 0.0:
                
                # make a quick dataframe with the value and the predicted
                # component
                gate_df = pd.DataFrame({"x" : x[:, 0], 
                                        "y" : x[:, 1],
                                        "p" : predicted})

                # for each component, get the ellipse that follows the isoline
                # around the mixture component
                # cf. http://scikit-learn.org/stable/auto_examples/mixture/plot_gmm.html
                # and http://www.mathworks.com/matlabcentral/newsreader/view_thread/298389
                # and http://stackoverflow.com/questions/7946187/point-and-ellipse-rotated-position-test-algorithm
                # i am not proud of how many tries this took me to get right.

                for c in range(0, self.num_components):
                    mean = gmm.means_[c]
                    covar = gmm.covariances_[c]
                    
                    # xc is the center on the x axis
                    # yc is the center on the y axis
                    xc = mean[0]  # @UnusedVariable
                    yc = mean[1]  # @UnusedVariable
                    
                    v, w = linalg.eigh(covar)
                    u = w[0] / linalg.norm(w[0])
                    
                    # xl is the length along the x axis
                    # yl is the length along the y axis
                    xl = np.sqrt(v[0]) * self.sigma  # @UnusedVariable
                    yl = np.sqrt(v[1]) * self.sigma  # @UnusedVariable
                    
                    # t is the rotation in radians (counter-clockwise)
                    t = 2 * np.pi - np.arctan(u[1] / u[0])
                    
                    sin_t = np.sin(t)  # @UnusedVariable
                    cos_t = np.cos(t)  # @UnusedVariable
                                        
                    # and build an expression with numexpr so it evaluates fast!

                    gate_bool = gate_df.eval("p == @c and "
                                             "((x - @xc) * @cos_t - (y - @yc) * @sin_t) ** 2 / ((@xl / 2) ** 2) + "
                                             "((x - @xc) * @sin_t + (y - @yc) * @cos_t) ** 2 / ((@yl / 2) ** 2) <= 1").values

                    predicted[np.logical_and(predicted == c, gate_bool == False)] = -1
            
            predicted_str = pd.Series(["(none)"] * len(predicted))
            for c in range(0, self.num_components):
                predicted_str[predicted == c] = "{0}_{1}".format(self.name, c + 1)
            predicted_str[predicted == -1] = "{0}_None".format(self.name)
            predicted_str.index = group_idx

            event_assignments.iloc[group_idx] = predicted_str
                    
            if self.posteriors:
                probability = np.full((len(x), self.num_components), 0.0, "float")
                probability[~x_na, :] = gmm.predict_proba(x[~x_na, :])
                posteriors = pd.Series([0.0] * len(predicted))
                for c in range(0, self.num_components):
                    posteriors[predicted == c] = probability[predicted == c, c]
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
    
            xmean_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
            ymean_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
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
                            g = (g[0],)
                    else:
                        g = group
                                                                             
                    xmean_stat.at[g] = self._xscale.inverse(gmm.means_[c][0])
                    ymean_stat.at[g] = self._yscale.inverse(gmm.means_[c][0])
                    prop_stat.at[g] = gmm.weights_[c]
                     
            new_experiment.statistics[(self.name, "xmean")] = pd.to_numeric(xmean_stat)
            new_experiment.statistics[(self.name, "ymean")] = pd.to_numeric(ymean_stat)
            if self.num_components > 1:
                new_experiment.statistics[(self.name, "proportion")] = pd.to_numeric(prop_stat)
            
                    
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the Gaussian mixture model.
        
        Returns
        -------
            IView : an IView, call :meth:`~GaussianMixture2DView.plot` to see 
            the diagnostic plot.
        
        """
        
        warn("GaussianMixture1DOp is DEPRECATED.  Please use GaussianMixtureOp.",
             util.CytoflowOpWarning)
        
        v = GaussianMixture2DView(op = self)
        v.trait_set(**kwargs)
        return v
    
    
# a few more imports for drawing scaled ellipses
        
import matplotlib.path as path
import matplotlib.patches as patches
import matplotlib.transforms as transforms
    
@provides(IView)
class GaussianMixture2DView(By2DView, AnnotatingView, ScatterplotView):
    """
    A diagnostic plot for a :class:`GaussianMixture2DOp`.

    Attributes
    ----------
      
    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.gaussianmixture2dview')
    friendly_id = Constant("2D Gaussian Mixture Diagnostic Plot")
        
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
        
        view, trait_name = self._strip_trait(self.op.name)
        
        if self.xscale:
            xscale = self.op._xscale
        else:
            xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)

        if self.yscale:
            yscale = self.op._yscale
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
            
        xscale = kwargs['xscale']
        yscale = kwargs['yscale']
        
        mean = gmm.means_[idx]
        covar = gmm.covariances_[idx]
        
        v, w = linalg.eigh(covar)
        u = w[0] / linalg.norm(w[0])
        
        #rotation angle (in degrees)
        t = np.arctan(u[1] / u[0])
        t = 180 * t / np.pi
        
        # in order to scale the ellipses correctly, we have to make them
        # ourselves out of an affine-scaled unit circle.  The interface
        # is the same as matplotlib.patches.Ellipse
        
        self._plot_ellipse(axes,
                           xscale,
                           yscale,
                           mean,
                           np.sqrt(v[0]),
                           np.sqrt(v[1]),
                           180 + t,
                           color = annotation_color,
                           fill = False,
                           linewidth = 2)

        self._plot_ellipse(axes, 
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
        
        self._plot_ellipse(axes, 
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
                    
    def _plot_ellipse(self, ax, xscale, yscale, center, width, height, angle, **kwargs):
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
            
util.expand_class_attributes(GaussianMixture2DView)
util.expand_method_parameters(GaussianMixture2DView, GaussianMixture2DView.plot)
    
