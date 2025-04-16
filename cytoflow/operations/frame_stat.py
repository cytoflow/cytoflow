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
cytoflow.operations.frame_stat
------------------------------

The `frame_stat` module contains one class:

`FrameStatisticOp` -- applies a function to subsets of a data set,
and adds the resulting statistic to the `Experiment`.  Unlike
`ChannelStatisticOp`, which operates on a single channel, this operation
operates on entire `pandas.DataFrame`.
"""

from warnings import warn
import pandas as pd
import numpy as np

from traits.api import (HasStrictTraits, Str, List, Constant, provides, 
                        Callable)
import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class FrameStatisticOp(HasStrictTraits):
    """
    Apply a function to subsets of a data set, and add it as a statistic
    to the experiment.
    
    The `apply` function groups the data by the variables in `by`, 
    then applies the `function` callable to each `pandas.DataFrame` 
    subset.  The callable should take a `pandas.DataFrame` as its only 
    parameter and return a `pandas.Series` whose values are ``float``. 
    The columns of the resulting statistic come from the index (ie, the 
    row names) of the first `pandas.Series` to be returned.
    
    Attributes
    ----------
    name : Str
        The operation name.  Becomes the first element in the
        `Experiment.statistics` key tuple.
        
    function : Callable
        The function used to compute the statistic.  Must take a 
        `pandas.DataFrame` as its only argument and return a 
        `pandas.DataFrame` containing ``float`` values. The column names
        of this dataframe will become the column names of the new statistic.

    by : List(Str)
        A list of metadata attributes to aggregate the data before applying the
        function.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting ``by = ["Time", "Dox"]`` will apply 
        `function` separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    subset : Str
        A Python expression sent to Experiment.query() to subset the data before
        computing the statistic.
   
    Examples
    --------
    
    >>> stats_op = FrameStatisticOp(name = "MeanByDox",
    ...                             function = lambda x: x.mean,
    ...                             by = ["Dox"])
    >>> ex2 = stats_op.apply(ex)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.frame_statistic')
    friendly_id = Constant("Frame Statistic")
    
    name = Str
    function = Callable
    by = List(Str)
    subset = Str
    
    def apply(self, experiment):
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")

        if not self.name:
            raise util.CytoflowOpError('name',
                                       "Must specify a name")
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name))  

        if not self.function:
            raise util.CytoflowOpError('function',
                                       "Must specify a function")
            
        if not self.by:
            raise util.CytoflowOpError('by',
                                       "Must specify some grouping conditions "
                                       "in 'by'")
                    
        new_experiment = experiment.clone(deep = False)

        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except Exception as e:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' isn't valid"
                                           .format(self.subset)) from e
                
            if len(experiment) == 0:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' returned no events"
                                           .format(self.subset))
       
        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           " must be one of {}"
                                           .format(b, experiment.conditions))
            unique = experiment.data[b].unique()
                
            if len(unique) == 1:
                warn("Only one category for {}".format(b), util.CytoflowOpWarning)
                
        groupby = experiment.data.groupby(self.by, observed = False)
        idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by], 
                                         names = self.by)

        stat = pd.DataFrame(index = idx, 
                            dtype = 'float').sort_index()
        
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data".format(group), 
                     util.CytoflowOpWarning)
                continue
            
            try:
                v = self.function(data_subset)
                if not isinstance(v, pd.Series):
                    raise util.CytoflowOpError('function',
                                               "'function' must return a pandas.Series")
                    
                if len(stat.columns) == 0:
                    for col in v.index:
                        stat.insert(len(stat.columns), col, value = np.nan)
                
                stat.loc[group] = v

            except Exception as e:
                raise util.CytoflowOpError('function',
                                           "Your function threw an error in group {}"
                                           .format(group)) from e    
                            
            # check for, and warn about, NaNs.
            if pd.Series(stat.loc[group]).isna().any():
                raise util.CytoflowOpError('',
                                           "Category {} returned {}".format(group, stat.loc[group]))

        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        new_experiment.statistics[self.name] = stat

        return new_experiment
