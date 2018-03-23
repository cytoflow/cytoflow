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
cytoflow.operations.kmeans
--------------------------
'''


from traits.api import (HasStrictTraits, Str, CStr, Dict, Any, Instance, 
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
    
    Call :meth:`estimate` to compute the cluster centroids.
      
    Calling :meth:`apply` creates a new categorical metadata variable 
    named :attr:`name`, with possible values ``{name}_1`` .... ``name_n`` where 
    ``n`` is the number of clusters, specified with :attr:`num_clusters`.
    
    The same model may not be appropriate for different subsets of the data set.
    If this is the case, you can use the :attr:`by` attribute to specify 
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
        channel is in :attr:`channels` but not in :attr:`scale`, the current 
        package-wide default (set with :func:`.set_default_scale`) is used.

    num_clusters : Int (default = 2)
        How many components to fit to the data?  Must be a positive integer.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting :attr:`by` to ``["Time", "Dox"]`` will 
        fit the model separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
  
    
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
    
    id = Constant('edu.mit.synbio.cytoflow.operations.kmeans')
    friendly_id = Constant("KMeans Clustering")
    
    name = CStr()
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
            The :class:`.Experiment` to use to estimate the k-means clusters
            
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
                raise util.CytoflowOpError('by',
                                           "Group {} had no data"
                                           .format(group))
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
            
            # drop data that isn't in the scale range
            for c in self.channels:
                x = x[~(np.isnan(x[c]))]
            x = x.values
            
            self._kmeans[group] = kmeans = \
                sklearn.cluster.MiniBatchKMeans(n_clusters = self.num_clusters,
                                                random_state = 0)
            
            kmeans.fit(x)
                                                 
         
    def apply(self, experiment):
        """
        Apply the KMeans clustering to the data.
        
        Returns
        -------
        Experiment
            a new Experiment with one additional :attr:`~Experiment.condition` 
            named :attr:`name`, of type ``category``.  The new category has 
            values  ``name_1, name_2, etc`` to indicate which k-means cluster 
            an event is a member of.
            
            The new :class:`.Experiment` also has one new statistic called
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
                raise util.CytoflowOpError('by',
                                           "Group {} had no data"
                                           .format(group))
            
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
        Returns a diagnostic plot of the k-means clustering.
         
        Returns
        -------
            IView : an IView, call :meth:`KMeans1DView.plot` to see the diagnostic plot.
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
    Attributes
    ----------    
    op : Instance(KMeansOp)
        The op whose parameters we're viewing.
    """
    
    id = Constant('edu.mit.synbio.cytoflow.views.kmeans1dview')
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
    Attributes
    ----------
    op : Instance(KMeansOp)
        The op whose parameters we're viewing.        
    """
     
    id = Constant('edu.mit.synbio.cytoflow.view.kmeans2dview')
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