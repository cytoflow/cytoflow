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
import matplotlib.pyplot as plt

from cytoflow.views import IView
import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class SOMOp(HasStrictTraits):
    """
    Use a self-organizing map to cluster events.  
    
    Calling `estimate` creates the map, often using a random subset of the
    events that will eventually be clustered.
      
    Calling `apply` creates a new integer metadata variable 
    named ``{name}`, with possible values ``0`` .... ``n-1`` where 
    ``n`` is the product of the height and width of the map (or the number of consensus
    clusters, if consensus clustering is used). Events with ``NA`` as a channel
    value are assigned the flag value ``-1``.

    The same model may not be appropriate for different subsets of the data set.
    If this is the case, you can use the `by` attribute to specify 
    metadata by which to aggregate the data before estimating (and applying) a 
    model.  The  number of clusters (and other clustering parameters) is the 
    same across each subset, though.

    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column and
        the new locations statistic.
        
    channels : List(Str)
        The channels to apply the clustering algorithm to.

    scale : Dict(Str : {"linear", "logicle", "log"})
        Re-scale the data in the specified channels before fitting.  If a 
        channel is in `channels` but not in `scale`, the current 
        package-wide default (set with `set_default_scale`) is used.
    
        .. note::
           Sometimes you may see events labeled ``-1`` -- this results 
           from events for which the selected scale is invalid. For example, if
           an event has a negative measurement in a channel and that channel's
           scale is set to "log", this event will be set to ``-1``.
           
    consensus_cluster : Bool (default = True)
        Should we use consensus clustering to find the "natural" number of
        clusters? Defauls to ``True``.
        
    num_iterations : Int (default = 50)
        How many times to update the neuron weights?
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting `by` to ``["Time", "Dox"]`` will 
        fit the model separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    sample : Float (default = 0.05)
        What proportion of the data set to use for training? Defaults to 5%
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
        ``cosine``, and ``manhattan``
        
    learning_rate : Float (default = 0.5)
        The initial step size for updating SOM weights. Changes as the map is
        learned.
        
    learning_decay_function = Enum (default = "asymptotic_decay")
        How fast does the learning rate decay? Possible values are 
        ``inverse_decay_to_zero``, ``linear_decay_to_zero``, and 
        ``asymptotic_decay``.
        
    sigma : Float (default = 1.0)
        The magnitude of each update. Fixed over the course of the run -- 
        higher values mean more aggressive updates.
        
    sigma_decay_function = Enum (default = "asymptotic_decay")
        How fast does sigma decay? Possible values are 
        ``inverse_decay_to_zero``, ``linear_decay_to_zero``, and 
        ``asymptotic_decay``.

    neighborhood_function = Enum (default = "gaussian")
        What function should be used to determine how nearby neurons are
        updated? Possible values are ``gaussian``, ``mexican_hat``, ``bubble``, 
        and ``triangle``
        
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
    and https://www.datacamp.com/tutorial/self-organizing-maps. The "Tuning the 
    SOM Model" section in that second link is particularly helpful!
      
    
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
    width = Int(7)
    height = Int(7)
    distance = Enum("euclidean", "cosine", "manhattan")
    learning_rate = Float(0.5)
    learning_decay_function = Enum('asymptotic_decay', 'inverse_decay_to_zero', 'linear_decay_to_zero')
    sigma = Float(1.0)
    sigma_decay_function = Enum('asymptotic_decay', 'inverse_decay_to_zero', 'linear_decay_to_zero')
    neighborhood_function = Enum('gaussian', 'mexican_hat', 'bubble', 'triangle')
    num_iterations = Int(50)
    sample = util.UnitFloat(0.05)
    
    # consensus clustering parameters
    consensus_cluster = Bool(True)
    min_clusters = Int(2)
    max_clusters = Int(20)
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
                                       decay_function = self.learning_decay_function,
                                       sigma = self.sigma,
                                       sigma_decay_function = self.sigma_decay_function,
                                       neighborhood_function = self.neighborhood_function,
                                       activation_distance = self.distance)
            
            soms[group].random_weights_init(x)
            soms[group].train(x, self.num_iterations, use_epochs = True, save_quant_history = True)
            
            if self.consensus_cluster:
                if self.min_clusters > self.max_clusters:
                    raise util.CytoflowOpError('max_clusters',
                                               "'max_clusters' must be larger than 'min_clusters'!")

                centers = soms[group].get_weights().reshape(self.width * self.height, len(self.channels))
                    
                if self.min_clusters < self.max_clusters:
                    cc = util.ConsensusClustering(sklearn.cluster.AgglomerativeClustering(linkage = "average", metric = self.distance),
                                                  min_clusters = self.min_clusters,
                                                  max_clusters = self.max_clusters,
                                                  n_resamples = self.n_resamples,
                                                  resample_frac = self.resample_frac)       
                    cc.fit(centers, n_jobs = 8)
                    best_k = cc.best_k()
                else:
                    best_k = self.min_clusters
                    
                self._cc[group] = sklearn.cluster.AgglomerativeClustering(n_clusters = best_k, linkage = "average", metric = self.distance)
                self._cc[group].fit(centers)
                
            
        # do this so the UI can pick up that the estimate changed
        self._som = soms        
        
    def update_consensus_clusters(self):
        
        if not self._som:
            raise util.CytoflowViewError('op', "No maps found! Did you call estimate()?")
        
        for group, som in self._som.items():
            
            if self.consensus_cluster:
                if self.min_clusters > self.max_clusters:
                    raise util.CytoflowOpError('max_clusters',
                                               "'max_clusters' must be larger than 'min_clusters'!")

                centers = som.get_weights().reshape(self.width * self.height, len(self.channels))
                    
                if self.min_clusters < self.max_clusters:
                    cc = util.ConsensusClustering(sklearn.cluster.AgglomerativeClustering(linkage = "average", metric = self.distance),
                                                  min_clusters = self.min_clusters,
                                                  max_clusters = self.max_clusters,
                                                  n_resamples = self.n_resamples,
                                                  resample_frac = self.resample_frac)       
                    cc.fit(centers, n_jobs = 8)
                    best_k = cc.best_k()
                else:
                    best_k = self.min_clusters
                    
                self._cc[group] = sklearn.cluster.AgglomerativeClustering(n_clusters = best_k, linkage = "average", metric = self.distance)
                self._cc[group].fit(centers)
            
                    
         
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
            
        clusters = [x for x in range(num_clusters)]
          
        idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [clusters], 
                                         names = list(self.by) + [self.name])
        centers_stat = pd.DataFrame(index = idx,
                                    columns = list(self.channels), 
                                    dtype = 'float').sort_index()
                 
        if self.by:
            groupby = experiment.data.groupby(self.by, observed = False)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True, observed = False)
                 
        event_assignments = pd.Series([-1] * len(experiment))
                     
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
                    return cc.labels_[w[0] * self.width + w[1]]
            else:
                def winner_idx(x):
                    w = som.winner(x)
                    return w[0] * self.width + w[1]

            predicted[~x_na] = np.apply_along_axis(winner_idx, 1, x[~x_na])    
            event_assignments.iloc[group_idx] = predicted

            if self.consensus_cluster:
                cc = self._cc[group]
                for ci, channel in enumerate(self.channels):
                    scale = self._scale[channel]
                    for cluster in range(cc.n_clusters_):
                        if len(self.by) == 0:
                            g = tuple([cluster])
                        elif not util.is_list_like(group):
                            g = tuple([group] + [cluster])
                        else:
                            g = tuple(list(group) + [cluster])
                
                        centers_stat.at[g, channel] = scale(data_subset[predicted == cluster][channel].median())
                    
            else:            
                for ci, channel in enumerate(self.channels):
                    scale = self._scale[channel]
                    for cluster in range(num_clusters):
                        if len(self.by) == 0:
                            g = tuple([cluster])
                        elif not util.is_list_like(group):
                            g = tuple([group] + [cluster])
                        else:
                            g = tuple(list(group) + [cluster])
                            
                        centers_stat.at[g, channel] = centers[cluster][ci]
         
        new_experiment = experiment.clone(deep = False)          
        new_experiment.add_condition(self.name, "int", event_assignments)
        new_experiment.statistics[self.name] = centers_stat.dropna() 
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment
    

    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to evaluate the performance of the self-organized
        map.
        
        Returns
        -------
        IView
            An diagnostic view, call `AutofluorescenceDiagnosticView.plot` 
            to see the diagnostic plots
        """
        v = SOMDiagnosticView(op = self)
        v.trait_set(**kwargs)
        return v
        

@provides(IView)
class SOMDiagnosticView(HasStrictTraits):
    """
    Plots a distance map and the quantization error over time.
    
    Attributes
    ----------
    op : Instance(`SOMOp`)
        The `SOMOp` whose parameters we're viewing. Set 
        automatically if you created the instance using 
        `SOMOp.default_view`.

    """
    
    # traits   
    id = Constant('cytoflow.view.somdiagnosticview')
    friendly_id = Constant("Self Organizing Map Diagnostic")

    op = Instance(SOMOp)  
    
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot a faceted histogram view of a channel
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.op._som:
            raise util.CytoflowViewError('op', "No maps found! Did you call estimate()?")
        
        if len(self.op._som) > 1 and not plot_name:
            raise util.CytoflowOpError('plot_name', "Must specify a SOM with 'plot_name'. Possible values: {}"
                                       .format(self.op._som.keys()))
            
        if len(self.op._som) > 1 and plot_name not in self.op._som:
            raise util.CytoflowOpError('plot_name', "'plot_name' {} wasn't a group. Possible values: {}"
                                       .format(plot_name, self.op._som.keys()))
        
        if len(self.op._som) > 1:
            som = self.op._som[plot_name]
        else:
            som = list(self.op._som.values())[0]
            
        plt.figure()
            
        plt.subplot(2, 1, 1)
        plt.pcolor(som.distance_map().T, cmap = 'viridis')
        plt.colorbar()
        plt.xlabel("Neuron Column")
        plt.ylabel("Neuron Row")
        
        plt.subplot(2, 1, 2)
        plt.plot(list(range(self.op.num_iterations)), 
                 som.quantization_history())
        plt.ylabel("Quantization Error")
        plt.xlabel("Iteration")

