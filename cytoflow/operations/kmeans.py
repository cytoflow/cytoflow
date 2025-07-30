#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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

"""
cytoflow.operations.kmeans
--------------------------

Use k-means clustering to cluster events in any number of dimensions.
`kmeans` has three classes:

`KMeansOp` -- the `IOperation` to perform the clustering.

`KMeans1DView` -- a diagnostic view of the clustering (1D, using a histogram)

`KMeans2DView` -- a diagnostic view of the clustering (2D, using a scatterplot)
"""

from warnings import warn
from traits.api import (HasStrictTraits, Str, Dict, Any, Instance, 
                        Constant, List, provides)

import numpy as np
import sklearn.cluster

import pandas as pd

from cytoflow.views import IView, HistogramView, ScatterplotView
import cytoflow.utility as util

from .i_operation import IOperation
from .base_op_views import By1DView, By2DView, AnnotatingView

@provides(IOperation)
class KMeansOp(HasStrictTraits):
    """
    Use a K-means clustering algorithm to cluster events.  
    
    Call `estimate` to compute the cluster centroids.
      
    Calling `apply` creates a new categorical metadata variable 
    named ``{name}_Cluster``, with possible values ``Cluster_1`` .... ``Cluster_n`` 
    where ``n`` is the number of clusters, specified with `num_clusters`.

    The same model may not be appropriate for different subsets of the data set.
    If this is the case, you can use the `by` attribute to specify 
    metadata by which to aggregate the data before estimating (and applying) a 
    model.  The  number of clusters is the same across each subset, though.

    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    channels : List(Str)
        The channels to apply the clustering algorithm to.

    scale : Dict(Str : {"linear", "logicle", "log"})
        Re-scale the data in the specified channels before fitting.  If a 
        channel is in `channels` but not in `scale`, the current 
        package-wide default (set with `set_default_scale`) is used.
    
        .. note::
           Sometimes you may see events labeled ``{name}_None`` -- this results 
           from events for which the selected scale is invalid. For example, if
           an event has a negative measurement in a channel and that channel's
           scale is set to "log", this event will be set to ``{name}_None``.

    num_clusters : Int 
        How many components to fit to the data?  Must be greater or equal to 2.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting `by` to ``["Time", "Dox"]`` will 
        fit the model separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    Statistics
    ----------
    
    Adds a statistic whose name is the name of the operation, whose columns are 
    the channels used for clustering, and whose values are the centroids for 
    each cluster in that channel. Useful for hierarchical clustering, minimum 
    spanning tree visualizations, etc. The index has levels from `by`, plus a 
    new level called ``Cluster``.
    
    The new statistic also has a feature named ``Proportion``, which has the 
    proportion of events in each cluster.
    
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
        
        >>> km_op = flow.KMeansOp(name = 'KMeans',
        ...                       channels = ['V2-A', 'Y2-A'],
        ...                       scale = {'V2-A' : 'log',
        ...                                'Y2-A' : 'log'},
        ...                       num_clusters = 2)
        
    Estimate the clusters
    
    .. plot::
        :context: close-figs
        
        >>> km_op.estimate(ex)
        
    Plot a diagnostic view
    
    .. plot::
        :context: close-figs
        
        >>> km_op.default_view().plot(ex)

    Apply the gate
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = km_op.apply(ex)

    Plot a diagnostic view with the event assignments
    
    .. plot::
        :context: close-figs
        
        >>> km_op.default_view().plot(ex2)
    """
    
    id = Constant('cytoflow.operations.kmeans')
    friendly_id = Constant("KMeans Clustering")
    
    name = Str
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    num_clusters = util.PositiveInt(allow_zero = False)
    by = List(Str)
    
    _kmeans = Dict(Any, Instance(sklearn.cluster.MiniBatchKMeans), transient = True)
    _scale = Dict(Str, Instance(util.IScale), transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the k-means clusters
        
        Parameters
        ----------
        experiment : Experiment
            The `Experiment` to use to estimate the k-means clusters
            
        subset : str (default = None)
            A Python expression that specifies a subset of the data in 
            ``experiment`` to use to parameterize the operation.
        """

        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
        if self.num_clusters < 2:
            raise util.CytoflowOpError('num_clusters',
                                       "num_clusters must be >= 2")
        
        if len(self.channels) == 0:
            raise util.CytoflowOpError('channels',
                                       "Must set at least one channel")
            
        if len(self.channels) != len(set(self.channels)):
            raise util.CytoflowOpError('channels', 
                                       "Must not duplicate channels")

        for c in self.channels:
            if c not in experiment.data:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not found in the experiment"
                                      .format(c))
                
        for c in self.scale:
            if c not in self.channels:
                raise util.CytoflowOpError('scale',
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
                raise util.CytoflowOpError('subset',
                                            "Subset string '{0}' isn't valid"
                                            .format(subset))
                
            if len(experiment) == 0:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' returned no events"
                                           .format(subset))
                
        if self.by:
            groupby = experiment.data.groupby(self.by, observed = False)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True, observed = False)
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        self._scale = {}
        for c in self.channels:
            if c in self.scale:
                self._scale[c] = util.scale_factory(self.scale[c], experiment, channel = c)
            else:
                self._scale[c] = util.scale_factory(util.get_default_scale(), experiment, channel = c)
                    
                    
        kmeans = {}
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data".format(group), 
                     util.CytoflowOpWarning)
                continue
            
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
            
            # drop data that isn't in the scale range
            for c in self.channels:
                x = x[~(np.isnan(x[c]))]
            x = x.values
            
            kmeans[group] = k = \
                sklearn.cluster.MiniBatchKMeans(n_clusters = self.num_clusters,
                                                random_state = 0)
            
            k.fit(x)
            
        # TODO - add optional consensus clustering
            
        # do this so the UI can pick up that the estimate changed
        self._kmeans = kmeans                       
         
    def apply(self, experiment):
        """
        Apply the KMeans clustering to the data.
        
        Returns
        -------
        Experiment
            a new Experiment with one additional entry in `Experiment.conditions` 
            named `name`, of type ``category``.  The new category has 
            values  ``name_1``, ``name_2``, etc to indicate which k-means cluster 
            an event is a member of.
            
            The new `Experiment` also has one new statistic called
            ``centers``, which is a list of tuples encoding the centroids of each
            k-means cluster.
        """
 
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
         
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
            
        if not self._kmeans:
            raise util.CytoflowOpError(None, 
                                       "No components found.  Did you forget to "
                                       "call estimate()?")
         
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
                raise util.CytoflowOpError('scale',
                                           "Scale set for channel {0}, but it isn't "
                                           "in the experiment"
                                           .format(c))
        
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                
        if "{}_Clusters".format(self.name) in self.by:
            raise util.CytoflowOpError('by',
                                       "'{}_Clusters' is going to be added as an "
                                       "index level to the new statistic, so you "
                                       "can't use it to aggregate events."
                                       .format(self.name))
        
                 
        if self.by:
            groupby = experiment.data.groupby(self.by, observed = False)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True, observed = False)
                 
        event_assignments = pd.Series(["Cluster_None".format(self.name)] * len(experiment), dtype = "object")
         
        # make the statistics       
        clusters = ["Cluster_{}".format(x + 1) for x in range(self.num_clusters)]
          
        idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [clusters], 
                                         names = list(self.by) + ["{}_Cluster".format(self.name)])

        new_stat = pd.DataFrame(index = idx,
                                columns = list(self.channels) + ["Proportion"], 
                                dtype = 'float').sort_index()
                     
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data".format(group), 
                     util.CytoflowOpWarning)
                continue
            
            if group not in self._kmeans:
                raise util.CytoflowOpError('by',
                                           "Group {} not found in the estimated model. "
                                           "Do you need to re-run estimate()?"
                                           .format(group))    
            
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
                 
            # which values are missing?
 
            x_na = pd.Series([False] * len(x))
            for c in self.channels:
                x_na[np.isnan(x[c]).values] = True
                         
            x = x.values
            x_na = x_na.values
            group_idx = data_subset.index
            
            kmeans = self._kmeans[group]
  
            predicted = np.full(len(x), -1, "int")
            predicted[~x_na] = kmeans.predict(x[~x_na])
                 
            predicted_str = pd.Series(["(none)"] * len(predicted))
            for c in range(0, self.num_clusters):
                predicted_str[predicted == c] = "Cluster_{}".format(c + 1)
            predicted_str[predicted == -1] = "Cluster_None"
            predicted_str.index = group_idx
      
            event_assignments.iloc[group_idx] = predicted_str
            
            for c in range(self.num_clusters):
                if len(self.by) == 0:
                    g = tuple(["Cluster_{}".format(c + 1)])
                else:
                    g = group + tuple(["Cluster_{}".format(c + 1)])
                                    
                for cidx1, channel1 in enumerate(self.channels):
                    new_stat.loc[g, channel1] = self._scale[channel1].inverse(kmeans.cluster_centers_[c, cidx1])
                
                new_stat.loc[g, "Proportion"] = sum(predicted == c) / len(predicted)
         
        new_experiment = experiment.clone(deep = False)          
        new_experiment.add_condition("{}_Cluster".format(self.name), "category", event_assignments)
        
        new_experiment.statistics[self.name] = new_stat
 
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the k-means clustering.
         
        Returns
        -------
            IView : an IView, call `KMeans1DView.plot` to see the diagnostic plot.
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
            v = KMeans1DView(op = self)
            v.trait_set(channel = channels[0], 
                        scale = scale[channels[0]], 
                        **kwargs)
            return v
        
        elif len(channels) == 2:
            v = KMeans2DView(op = self)
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
class KMeans1DView(By1DView, AnnotatingView, HistogramView):
    """
    A diagnostic view for `KMeansOp` (1D, using a histogram)
    
    Attributes
    ----------    
    op : Instance(KMeansOp)
        The op whose parameters we're viewing.
    """
    
    id = Constant('cytoflow.views.kmeans1dview')
    friendly_id = Constant("1D KMeans Diagnostic Plot")
    
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
                
        view, trait_name = self._strip_trait(self.op.name)
        
        
        if self.channel in self.op._scale:
            scale = self.op._scale[self.channel]
        else:
            scale = util.scale_factory(self.scale, experiment, channel = self.channel)
    
        super(KMeans1DView, view).plot(experiment,
                                       annotation_facet = self.op.name,
                                       annotation_trait = trait_name,
                                       annotations = self.op._kmeans,
                                       scale = scale,
                                       **kwargs)
 
    def _annotation_plot(self, axes, annotation, annotation_facet, 
                         annotation_value, annotation_color, **kwargs):
                                                        
        # plot the cluster centers
            
        km = annotation
        
        kwargs.setdefault('orientation', 'vertical')
        
        if kwargs['orientation'] == 'horizontal':
            scale = kwargs['yscale']
            cidx = self.op.channels.index(self.channel)
            for k in range(0, self.op.num_clusters):
                c = scale.inverse(km.cluster_centers_[k][cidx])
                axes.axhline(c, linewidth=3, color='blue')         
        else:
            scale = kwargs['xscale']
            cidx = self.op.channels.index(self.channel)
            for k in range(0, self.op.num_clusters):
                c = scale.inverse(km.cluster_centers_[k][cidx])
                axes.axvline(c, linewidth=3, color='blue')                      

     
@provides(IView)
class KMeans2DView(By2DView, AnnotatingView, ScatterplotView):
    """
    A diagnostic view for `KMeansOp` (2D, using a scatterplot).
    
    Attributes
    ----------
    op : Instance(KMeansOp)
        The op whose parameters we're viewing.        
    """
     
    id = Constant('cytoflow.view.kmeans2dview')
    friendly_id = Constant("2D Kmeans Diagnostic Plot")
    
    xchannel = Str
    ychannel = Str
    
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        
        Parameters
        ----------
        """

        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
                
        view, trait_name = self._strip_trait(self.op.name)
        
        if self.xchannel in self.op._scale:
            xscale = self.op._scale[self.xchannel]
        else:
            xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)

        if self.ychannel in self.op._scale:
            yscale = self.op._scale[self.ychannel]
        else:
            yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
    
        super(KMeans2DView, view).plot(experiment,
                                       annotation_facet = self.op.name,
                                       annotation_trait = trait_name,
                                       annotations = self.op._kmeans,
                                       xscale = xscale,
                                       yscale = yscale,
                                       **kwargs)
 
    def _annotation_plot(self, axes, annotation, annotation_facet, 
                         annotation_value, annotation_color, **kwargs):
                                                        
        # plot the cluster centers
            
        km = annotation
        xscale = kwargs['xscale']
        yscale = kwargs['yscale']
        
        ix = self.op.channels.index(self.xchannel)
        iy = self.op.channels.index(self.ychannel)
        
        for k in range(self.op.num_clusters):
            x = xscale.inverse(km.cluster_centers_[k][ix])
            y = yscale.inverse(km.cluster_centers_[k][iy])
            
            axes.plot(x, y, '*', color = 'blue')

util.expand_class_attributes(KMeans1DView)
util.expand_method_parameters(KMeans1DView, KMeans1DView.plot)

util.expand_class_attributes(KMeans2DView)
util.expand_method_parameters(KMeans2DView, KMeans2DView.plot)