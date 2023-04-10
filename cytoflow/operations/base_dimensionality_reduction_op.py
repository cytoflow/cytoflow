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
cytoflow.operations.dimensionality_reduction_base
-----------------------

Apply dimensionality reduction to flow data -- base class for 
dimesnionality reduction operations like PCA or UMAP.
`base_dimensionality_reduction_op` has one class:

`BaseDimensionalityReductionOp` -- the `IOperation`
 that applies an embedding algorithm to an `Experiment`.
"""


from traits.api import (HasStrictTraits, Str, Dict, Any, Instance, 
                        Constant, List, Bool, provides)

import numpy as np
import pandas as pd

import cytoflow.utility as util
from .i_operation import IOperation
from abc import ABC, abstractmethod

@provides(IOperation)
class BaseDimensionalityReductionOp(HasStrictTraits):
    """
    A base class for dimensionality reduction operations like PCA or UMAP.
    
    Call `estimate` to fit the embeddding.
      
    Calling `apply` creates new "channels" named ``{name}_1 ... {name}_n``,
    where ``name`` is the `name` attribute and ``n`` is `num_components`.

    The same dimensionality reduction may not be appropriate 
    for different subsets of the data set.
    If this is the case, you can use the `by` attribute to specify 
    metadata by which to aggregate the data before estimating (and applying) a 
    model.  The embedder parameters are the same across each subset, though.

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

    num_components : Int (default = 2)
        How many components to fit to the data?  Must be a positive integer.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting `by` to ``["Time", "Dox"]`` will 
        fit the model separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.base_dimensionality_reduction_op')
    friendly_id = Constant("Base Dimensionality Reduction Operation")
    
    name = Str
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    num_components = util.PositiveInt(2, allow_zero = False)
    by = List(Str)
    
    _embedder = Dict(Any, Any, transient = True)
    _scale = Dict(Str, Instance(util.IScale), transient = True)

    def estimate(self, experiment, subset = None):
        """
        Estimate the decomposition
        
        Parameters
        ----------
        experiment : Experiment
            The `Experiment` to use to estimate the embedding.
            
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
        
        #custom valditions in child class
        self._validate_estimate(experiment=experiment, subset=subset)

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
                    
        embedder = {}
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
             
            embedder[group] = self._init_embedder(group, data_subset)
            
            embedder[group].fit(x)
        
        # set this atomically to support GUI
        self._embedder = embedder                      
         
    def apply(self, experiment):
        """
        Apply the embedder to the data.
        
        Returns
        -------
        Experiment
            a new Experiment with additional `Experiment.channels` 
            named ``name_1 ... name_n``

        """
 
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
            
        if not self._embedder:
            raise util.CytoflowOpError(None,
                                       "No fitted embeddings found.  Did you forget to call estimate()?")
         
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
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True)
            
        # need deep = True because of the data.dropna below
        new_experiment = experiment.clone(deep = True)       
        new_channels = []   
        for i in range(self.num_components):
            cname = "{}_{}".format(self.name, i + 1)
            if cname in experiment.data:
                raise util.CytoflowOpError('name',
                                           "Channel {} is already in the experiment"
                                           .format(cname))
                                           
            new_experiment.add_channel(cname, pd.Series(index = experiment.data.index))
            new_channels.append(cname)            
                   
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError('by',
                                           "Group {} had no data"
                                           .format(group))
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
                 
            # which values are missing?
   
            x_na = pd.Series([False] * len(x))
            for c in self.channels:
                x_na[np.isnan(x[c]).values] = True
            x_na = x_na.values
            x[x_na] = 0
            
            group_idx = groupby.groups[group]
            
            emebedder = self._embedder[group]
            x_tf = emebedder.transform(x)
            x_tf[x_na] = np.nan
            
            for ci, c in enumerate(new_channels):
                new_experiment.data.loc[group_idx, c] = x_tf[:, ci]

        new_experiment.data.dropna(inplace = True)
        new_experiment.data.reset_index(drop = True, inplace = True)

        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment

    @abstractmethod
    def _validate_estimate(self, experiment, subset = None):
        pass

    @abstractmethod
    def _init_embedder(self, group, data_subset):
        pass