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
cytoflow.operations.som
-----------------------

Use self-organizing maps to cluster events in any number of dimensions.
`som` has one classes:

`SOMOp` -- the `IOperation` to perform the clustering.

"""

from warnings import warn
from traits.api import (HasStrictTraits, Str, Dict, Any, Instance, 
                        Constant, List, Int, Float, Enum, Bool,
                        provides)

import numpy as np
import pandas as pd
import sklearn.cluster

from cytoflow.views import IView, HistogramView, ScatterplotView
import cytoflow.utility as util

from .i_operation import IOperation
from .base_op_views import By1DView, By2DView, AnnotatingView

@provides(IOperation)
class SOMOp(HasStrictTraits):
    """
    Use a self-organizing map to cluster events.  
    
    Calling `estimate` creates the map, often using a random subset of the
    events that will eventually be clustered.
      
    Calling `apply` creates a new categorical metadata variable 
    named `name_Cluster`, with possible values ``Cluster_1`` .... ``Cluster_n`` where 
    ``n`` is the product of the height and width of the map (or the number of consensus
    clusters, if consensus clustering is used).

    The same model may not be appropriate for different subsets of the data set.
    If this is the case, you can use the `by` attribute to specify 
    metadata by which to aggregate the data before estimating (and applying) a 
    model.  The  number of clusters (and other clustering parameters) is the 
    same across each subset, though.

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
           
    consensus_cluster : Bool (default = True)
        Should we use consensus clustering to find the "natural" number of
        clusters? Defauls to ``True``.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting `by` to ``["Time", "Dox"]`` will 
        fit the model separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    sample : Float (default = 0.01)
        What proportion of the data set to use for training? Defaults to 1%
        of the dataset to help with runtime.
        
    *SOM parameters*

    width : Int (default = 10)
        What is the width of the map? The number of clusters used is the product
        of `width` and `height`.
        
    height : Int (default = 10)
        What is the height of the map? The number of clusters used is the product
        of `width` and `height`.
        
    distance : Enum (default = "euclidean")
        The distance measure that activates the map. Defaults to ``euclidean``.
        ``cosine`` is recommended for >3 channels. Possible values are "euclidean", 
        ``cosine``, ``manhattan``, and ``chebyshev``
        
    learning_rate : Float (default = 0.5)
        The initial step size for updating SOM weights. Changes as the map is
        learned.
        
    sigma : Float (default = 1.0)
        The magnitude of each update. Fixed over the course of the run -- 
        higher values mean more aggressive updates.
        
    num_iterations : Int (default = 20)
        How many times to update the neuron weights?
        
    *Consensus clustering parameters*
    
    min_clusters : Int (default = 2)
        The minimum number of consensus clusters to form.
        
    max_clusters : Int (default = 20)
        The maximum number of consensus clusters to form
        
    n_resamples : Int (default = 100)
        The number of times to attempt making consensus clusters, sampling 
        randomly a `resample_frac` proportion of the map nodes.
        
    resample_frac : Float (default = 0.8)
        The fraction of points to resample.
        
    Statistics
    ----------
    
    This operation adds a statistic whose features are the channel names used in
    the clustering and whose values are the centroids of the clusters. Useful
    for hierarchical clustering, minimum spanning tree visualization, etc.
    The index has levels from `by`, plus a new level called ``Cluster``.
    
    
    Notes
    -----
    
    Uses SOM code from https://github.com/rileypsmith/sklearn-som -- thanks!
    
    If you'd like to learn more about self-organizing maps and how to use
    them effectively, check out https://rubikscode.net/2018/08/20/introduction-to-self-organizing-maps/
      
    
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
        
        >>> som_op = flow.SOMOp(name = 'SOM',
        ...                     channels = ['V2-A', 'Y2-A'],
        ...                     scale = {'V2-A' : 'log',
        ...                              'Y2-A' : 'log'})
        
    Estimate the clusters
    
    .. plot::
        :context: close-figs
        
        >>> som_op.estimate(ex)
        
    Plot a diagnostic view
    
    .. plot::
        :context: close-figs
        
        >>> som_op.default_view().plot(ex)

    Apply the gate
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = som_op.apply(ex)

    Plot a diagnostic view with the event assignments
    
    .. plot::
        :context: close-figs
        
        >>> som_op.default_view().plot(ex2)
    """
    
    id = Constant('cytoflow.operations.som')
    friendly_id = Constant("Self Organizing Maps Clustering")
    
    name = Str
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    by = List(Str)

    # SOM parameters
    width = Int(10)
    height = Int(10)
    distance = Enum("euclidean", "cosine", "chebyshev", "manhattan")
    learning_rate = Float(0.5)
    sigma = Float(1.0)
    num_iterations = Int(20)
    sample = util.UnitFloat(0.1)
    
    # consensus clustering parameters
    consensus_cluster = Bool(True)
    min_clusters = Int(2)
    max_clusters = Int(10)
    n_resamples = Int(100)
    resample_frac = Float(0.8)
    
    _som = Dict(Any, Instance("cytoflow.utility.minisom.MiniSom"), transient = True)
    _cc = Dict(Any, Any)
    _centers = Dict(Any, Any)
    _scale = Dict(Str, Instance(util.IScale), transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the self-organized map
        
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
        
        if self.width < 1:
            raise util.CytoflowOpError('width',
                                       "width must be >= 1")
            
        if self.height < 1:
            raise util.CytoflowOpError('height',
                                       "height must be >= 1")
            
        if self.learning_rate <= 0:
            raise util.CytoflowOpError('learning_rate',
                                       "learning_rate must be > 0")
            
        if self.sigma < 0:
            raise util.CytoflowOpError('sigma',
                                       "sigma must be >= 0")
            
        if self.learning_rate <= 0:
            raise util.CytoflowOpError('learning_rate',
                                       "learning_rate must be > 0")
            
        if self.num_iterations <= 0:
            raise util.CytoflowOpError('num_iterations',
                                       "num_iterations must be > 0")
            
        if self.sample <= 0:
            raise util.CytoflowOpError('sample',
                                       "sample must be > 0")
        
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
                                           "in `channels`"
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
                    
                    
        soms = {}
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data".format(group), 
                     util.CytoflowOpWarning)
                continue
            
            x = data_subset.sample(frac = self.sample).loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
            
            # drop data that isn't in the scale range
            for c in self.channels:
                x = x[~(np.isnan(x[c]))]
            x = x.values
            
            soms[group] = util.MiniSom(x = self.width,
                                       y = self.height,
                                       input_len = len(self.channels),
                                       learning_rate = self.learning_rate,
                                       sigma = self.sigma,
                                       activation_distance = self.distance)
            
            soms[group].train(x, self.num_iterations, use_epochs = True)
            
            if self.consensus_cluster:
                centers = soms[group].get_weights().reshape(self.width * self.height, len(self.channels))
                cc = util.ConsensusClustering(sklearn.cluster.KMeans(),
                                              min_clusters = self.min_clusters,
                                              max_clusters = self.max_clusters,
                                              n_resamples = self.n_resamples,
                                              resample_frac = self.resample_frac)       
                cc.fit(centers, n_jobs = 8)
                best_k = cc.best_k()
                self._cc[group] = sklearn.cluster.KMeans(n_clusters = best_k)
                self._cc[group].fit(centers)
                
            
        # do this so the UI can pick up that the estimate changed
        self._som = soms                    
         
    def apply(self, experiment):
        """
        Apply the self-organizing maps clustering to the data.
        
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
            
        if not self._som:
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
        
        # make the statistic
        if self.consensus_cluster:
            num_clusters = self.max_clusters
        else:
            num_clusters = self.width * self.height
            
        clusters = [x + 1 for x in range(num_clusters)]
          
        idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [clusters], 
                                         names = list(self.by) + ["{}_Cluster".format(self.name)])
        centers_stat = pd.DataFrame(index = idx,
                                    columns = list(self.channels), 
                                    dtype = 'float').sort_index()
                 
        if self.by:
            groupby = experiment.data.groupby(self.by, observed = False)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True, observed = False)
                 
        event_assignments = pd.Series(["Cluster_None"] * len(experiment), dtype = "object")
                     
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data".format(group), 
                     util.CytoflowOpWarning)
                continue
            
            if group not in self._som:
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
            
            som = self._som[group]
  
            predicted = np.full(len(x), -1, "int")
            centers = som.get_weights().reshape(self.width * self.height, len(self.channels))
            
            if self.consensus_cluster:
                cc = self._cc[group]
                def winner_idx(x, cc = cc):
                    w = som.winner(x)
                    return cc.predict(centers[[w[0] * self.width + w[1]]])[0]
            else:
                def winner_idx(x):
                    w = som.winner(x)
                    return w[0] * self.width + w[1]

            predicted[~x_na] = np.apply_along_axis(winner_idx, 1, x[~x_na])
                 
            predicted_str = pd.Series(["(none)"] * len(predicted))
            for c in np.unique(predicted):
                predicted_str[predicted == c] = "Cluster_{}".format(c + 1)
            predicted_str[predicted == -1] = "Cluster_None"
            predicted_str.index = group_idx
      
            event_assignments.iloc[group_idx] = predicted_str

            if self.consensus_cluster:
                cc = self._cc[group]
                for ci, channel in enumerate(self.channels):
                    scale = self._scale[channel]
                    for cluster in range(cc.cluster_centers_.shape[0]):
                        if len(self.by) == 0:
                            g = tuple(["Cluster_{}".format(cluster + 1)])
                        elif not util.is_list_like(group):
                            g = tuple(list([group]) + ["Cluster_{}".format(cluster + 1)])
                        else:
                            g = tuple(list(group) + ["Cluster_{}".format(cluster + 1)])

                        centers_stat.at[g, channel] = scale.inverse(cc.cluster_centers_[cluster][ci])
                    
            else:            
                for ci, channel in enumerate(self.channels):
                    scale = self._scale[channel]
                    for cluster in range(num_clusters):
                        if len(self.by) == 0:
                            g = tuple([cluster + 1])
                        else:
                            g = tuple(list([group]) + [cluster + 1])
                            
                        centers_stat.at[g, channel] = scale.inverse(centers[cluster][ci])
         
        new_experiment = experiment.clone(deep = False)          
        new_experiment.add_condition("{}_Cluster".format(self.name), "category", event_assignments)
        new_experiment.statistics[self.name] = centers_stat.dropna() 
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
            v = SOM1DView(op = self)
            v.trait_set(channel = channels[0], 
                        scale = scale[channels[0]], 
                        **kwargs)
            return v
        
        elif len(channels) == 2:
            v = SOM2DView(op = self)
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
class SOM1DView(By1DView, AnnotatingView, HistogramView):
    """
    A diagnostic view for `SOMOp` (1D, using a histogram)
    
    Attributes
    ----------    
    op : Instance(SOMOp)
        The op whose parameters we're viewing.
    """
    
    id = Constant('cytoflow.views.som1dview')
    friendly_id = Constant("1D SOM Diagnostic Plot")
    
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
    
        super(SOM1DView, view).plot(experiment,
                                    annotation_facet = "{}_Cluster".format(self.op.name),
                                    annotation_trait = trait_name,
                                    annotations = self.op._som,
                                    scale = scale,
                                    **kwargs)
 
    def _annotation_plot(self, axes, annotation, annotation_facet, 
                         annotation_value, annotation_color, **kwargs):
                                                        
        # plot the cluster centers
            
        som = annotation
        
        kwargs.setdefault('orientation', 'vertical')
        
        centers = som.get_weights().reshape(self.op.width * self.op.height, len(self.op.channels))
        
        if kwargs['orientation'] == 'horizontal':
            scale = kwargs['yscale']
            cidx = self.op.channels.index(self.channel)
            for k in range(centers.shape[0]):
                c = scale.inverse(centers[k][cidx])
                axes.axhline(c, linewidth=3, color='blue')         
        else:
            scale = kwargs['xscale']
            cidx = self.op.channels.index(self.channel)
            for k in range(centers.shape[0]):
                c = scale.inverse(centers[k][cidx])
                axes.axvline(c, linewidth=3, color='blue')                      

     
@provides(IView)
class SOM2DView(By2DView, AnnotatingView, ScatterplotView):
    """
    A diagnostic view for `SOMOp` (2D, using a scatterplot).
    
    Attributes
    ----------
    op : Instance(SOMOp)
        The op whose parameters we're viewing.        
    """
     
    id = Constant('cytoflow.view.som2dview')
    friendly_id = Constant("2D SOM Diagnostic Plot")
    
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
    
        super(SOM2DView, view).plot(experiment,
                                    annotation_facet = "{}_Cluster".format(self.op.name),
                                    annotation_trait = trait_name,
                                    annotations = self.op._som,
                                    xscale = xscale,
                                    yscale = yscale,
                                    **kwargs)
 
    def _annotation_plot(self, axes, annotation, annotation_facet, 
                         annotation_value, annotation_color, **kwargs):
                                                        
        # plot the cluster centers
            
        som = annotation
        xscale = kwargs['xscale']
        yscale = kwargs['yscale']
        
        ix = self.op.channels.index(self.xchannel)
        iy = self.op.channels.index(self.ychannel)
        
        centers = som.get_weights().reshape(self.op.width * self.op.height, len(self.op.channels))
        
        for k in range(centers.shape[0]):
            x = xscale.inverse(centers[k][ix])
            y = yscale.inverse(centers[k][iy])
            
            axes.plot(x, y, '*', color = 'blue')

util.expand_class_attributes(SOM1DView)
util.expand_method_parameters(SOM1DView, SOM1DView.plot)

util.expand_class_attributes(SOM2DView)
util.expand_method_parameters(SOM2DView, SOM2DView.plot)