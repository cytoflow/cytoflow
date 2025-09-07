#!/usr/bin/env python3.11
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2025
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
cytoflow.operations.tsne
-----------------------

Apply t-Distributed Stochastic Neighbor Embedding (tSNE) to flow data. This is 
similar to principle component analysis, in that it is a dimensionality
reduction algorithm. Unlike PCA, it is non-linear and (supposedly) retains
internal structure better than PCA. `tsne` has one class:

`tSNEOp` -- the `IOperation` that applies tSNE to an `Experiment`.
"""

from warnings import warn
from traits.api import (HasStrictTraits, Str, Dict, Any, Instance, 
                        Constant, List, Enum, provides)

import numpy as np
import pandas as pd
from openTSNE import TSNE

import cytoflow.utility as util
from .i_operation import IOperation

@provides(IOperation)
class tSNEOp(HasStrictTraits):
    """
    Use t-Distributed Stochastic Neighbor Embedding to reduce the
    dimensionality of the data set.
    
    Call `estimate` to compute the embedding.
      
    Calling `apply` creates new "channels" named ``{name}_1`` and ``{name}_2``,
    where ``name`` is the `name` attribute. (Unlike PCA, tSNE only decomposes to
    two components.)

    The same decomposition may not be appropriate for different subsets of the data set.
    If this is the case, you can use the `by` attribute to specify 
    metadata by which to aggregate the data before estimating (and applying) a 
    model.  The tSNE parameters such as the perplexity are the same across
    each subset, though

    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new columns.
        
    channels : List(Str)
        The channels to apply the decomposition to.

    scale : Dict(Str : {"linear", "logicle", "log"})
        Re-scale the data in the specified channels before fitting.  If a 
        channel is in `channels` but not in `scale`, the current 
        package-wide default (set with `set_default_scale`) is used.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting `by` to ``["Time", "Dox"]`` will 
        fit the model separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    metric : Enum("euclidean", "cosine") (default = "euclidian")
        How to compute "distance"? If using many channels, try changing
        to ``cosine``.
        
    perplexity : Float (default = 10)
        The balance between the local and global structure of the data. Larger 
        datasets benefit from higher perplexity, but be warned -- runtime
        scales linearly with perplexity!
        
    sample : Float (default = 0.01)
        What proportion of the data set to use for training? Defaults to 1%
        of the dataset to help with runtime.
        
            
    Notes
    -----
    Uses ``openTSNE`` by Pavlin G. Policar, Martin Strazar and Blaz Zupan [1]_
    
    References
    ----------
    
    .. [1] Poliar, PG and Strazar, M and Zupan, Blaz (2024). 
           openTSNE: A Modular Python Library for t-SNE Dimensionality Reduction and Embedding
           Journal of Statistical Software 109: 1-30.
           https://www.jstatsoft.org/index.php/jss/article/view/v109i03
        
        
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
        
        >>> tsne = flow.tSNEOp(name = 'tSNE',
        ...                    channels = ['V2-A', 'V2-H', 'Y2-A', 'Y2-H'],
        ...                    scale = {'V2-A' : 'log',
        ...                             'V2-H' : 'log',
        ...                             'Y2-A' : 'log',
        ...                             'Y2-H' : 'log'},
        ...                    by = ["Dox"])
        
    Estimate the decomposition
    
    .. plot::
        :context: close-figs
        
        >>> tsne.estimate(ex)
        
    Apply the operation
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = tsne.apply(ex)

    Plot a scatterplot of the decomposition.  Compare to a scatterplot of 
    the underlying channels.
    
    .. plot::
        :context: close-figs
        
        >>> flow.ScatterplotView(xchannel = "V2-A",
        ...                      xscale = "log",
        ...                      ychannel = "Y2-A",
        ...                      yscale = "log",
        ...                      subset = "Dox == 1.0").plot(ex2)

        >>> flow.ScatterplotView(xchannel = "tSNE_1",
        ...                      ychannel = "tSNE_2",
        ...                      subset = "Dox == 1.0").plot(ex2)
       
    .. plot::
        :context: close-figs
        
        >>> flow.ScatterplotView(xchannel = "V2-A",
        ...                      xscale = "log",
        ...                      ychannel = "Y2-A",
        ...                      yscale = "log",
        ...                      subset = "Dox == 10.0").plot(ex2) 

        >>> flow.ScatterplotView(xchannel = "tSNE_1",
        ...                      ychannel = "tSNE_2",
        ...                      subset = "Dox == 10.0").plot(ex2)
    """
    
    id = Constant('cytoflow.operations.tsne')
    friendly_id = Constant("t-Stochastic Neighbor Embedding")
    
    name = Str
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    perplexity = util.PositiveFloat(10)
    sample = util.UnitFloat(0.01)
    metric = Enum("euclidean", "cosine", "manhattan", "hamming", "dot", "l1", "l2", "taxicab")
    by = List(Str)
    
    _tsne = Dict(Any, Any, transient = True)
    _scale = Dict(Str, Instance(util.IScale), transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the decomposition
        
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
        for c in self.channels:
            if c in self.scale:
                self._scale[c] = util.scale_factory(self.scale[c], experiment, channel = c)
            else:
                self._scale[c] = util.scale_factory(util.get_default_scale(), experiment, channel = c)
                    
        tsne = {}
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError('by',
                                           "Group {} had no data"
                                           .format(group))
            x = data_subset.sample(frac = self.sample).loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
            
            # drop data that isn't in the scale range
            for c in self.channels:
                x = x[~(np.isnan(x[c]))]
                             
            tsne[group] = \
                TSNE(perplexity = self.perplexity,
                     metric = self.metric, 
                     verbose = True, 
                     n_jobs = 8).fit(x.values)
                    
        # set this atomically to support GUI
        self._tsne = tsne                      
         
    def apply(self, experiment):
        """
        Apply the tSNE decomposition to the data.
        
        Returns
        -------
        Experiment
            a new Experiment with additional `Experiment.channels` 
            named ``name_1`` and ``name_2``

        """
 
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
            
        if not self._tsne:
            raise util.CytoflowOpError(None,
                                       "No tSNE found.  Did you forget to call estimate()?")
         
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the operation's name "
                                       "before applying it!")
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name)) 
         
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
            groupby = experiment.data.groupby(self.by, observed = False)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True, observed = False)
            
        # need deep = True because of the data.dropna below
        new_experiment = experiment.clone(deep = True)       
        new_channels = []   
        for i in [0,1]:
            cname = "{}_{}".format(self.name, i + 1)
            if cname in experiment.data:
                raise util.CytoflowOpError('name',
                                           "Channel {} is already in the experiment"
                                           .format(cname))
                                           
            new_experiment.add_channel(cname, pd.Series(index = experiment.data.index))
            new_channels.append(cname)            
                   
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data".format(group), 
                     util.CytoflowOpWarning)
                continue
            
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
                 
            # # which values are missing?
            #
            # x_na = pd.Series([False] * len(x))
            # for c in self.channels:
            #     x_na[np.isnan(x[c]).values] = True
            # x_na = x_na.values
            # x[x_na] = 0
            
            group_idx = data_subset.index
            
            tsne = self._tsne[group]
            x_tf = tsne.transform(x.values)
            # x_tf[x_na] = np.nan
            
            for ci, c in enumerate(new_channels):
                new_experiment.data.loc[group_idx, c] = x_tf[:, ci]

        new_experiment.data.dropna(inplace = True)
        new_experiment.data.reset_index(drop = True, inplace = True)

        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment
