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
cytoflow.operations.frame_stat
------------------------------
'''
from warnings import warn
import pandas as pd
import numpy as np

from traits.api import (HasStrictTraits, Str, List, Constant, provides, 
                        Callable, CStr, Any)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class FrameStatisticOp(HasStrictTraits):
    """
    Apply a function to subsets of a data set, and add it as a statistic
    to the experiment.
    
    The :meth:`apply` function groups the data by the variables in :attr:`by`, 
    then applies the :attr:`function` callable to each :class:`pandas.DataFrame` 
    subset.  The callable should take a :class:`DataFrame` as its only parameter.  
    The return type is arbitrary, but to be used with the rest of 
    :class:`cytoflow` it should probably be a numeric type or an iterable of 
    numeric types.
    
    Attributes
    ----------
    name : Str
        The operation name.  Becomes the first element in the
        :attr:`Experiment.statistics` key tuple.
        
    function : Callable
        The function used to compute the statistic.  Must take a 
        :class:`pandas.DataFrame` as its only argument.  The return type is 
        arbitrary, but to be used with the rest of :class:`cytoflow` it should 
        probably be a numeric type or an iterable of numeric types.  If 
        :attr:`statistic_name` is unset, the name of the function becomes the 
        second in element in the :attr:`Experiment.statistics` key tuple.
        
    statistic_name : Str
        The name of the function; if present, becomes the second element in
        the :attr:`Experiment.statistics` key tuple.  Particularly useful if 
        :attr:`function` is a lambda.
        
    by : List(Str)
        A list of metadata attributes to aggregate the data before applying the
        function.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting ``by = ["Time", "Dox"]`` will apply 
        :attr:`function` separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    subset : Str
        A Python expression sent to Experiment.query() to subset the data before
        computing the statistic.
        
    fill : Any (default = 0)
        The value to use in the statistic if a slice of the data is empty.
   
    Examples
    --------
    
    >>> stats_op = FrameStatisticOp(name = "ByDox",
    ...                             function = lambda x: np.mean(x["FITC-A"],
    ...                             statistic_name = "Mean",
    ...                             by = ["Dox"])
    >>> ex2 = stats_op.apply(ex)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.statistics')
    friendly_id = Constant("Statistics")
    
    name = CStr
    function = Callable
    statistic_name = Str
    by = List(Str)
    subset = Str
    fill = Any(0)
    
    def apply(self, experiment):
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")

        if not self.name:
            raise util.CytoflowOpError('name',
                                       "Must specify a name")

        if not self.function:
            raise util.CytoflowOpError('function',
                                       "Must specify a function")
            
        if not self.by:
            raise util.CytoflowOpError('by',
                                       "Must specify some grouping conditions "
                                       "in 'by'")

        new_experiment = experiment.clone()

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
            if b not in experiment.data:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {0} not found"
                                           " in the experiment"
                                           .format(b))
            unique = experiment.data[b].unique()
            if len(unique) > 100: #WARNING - magic number
                raise util.CytoflowOpError('by',
                                           "More than 100 unique values found for"
                                           " aggregation metadata {0}.  Did you"
                                           " accidentally specify a data channel?"
                                           .format(b))
                
            if len(unique) == 1:
                warn("Only one category for {}".format(b), util.CytoflowOpWarning)
                
        groupby = experiment.data.groupby(self.by)
                        
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data"
                     .format(group), 
                     util.CytoflowOpWarning)
        
        idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by], 
                                         names = self.by)

        stat = pd.Series(data = self.fill,
                         index = idx, 
                         dtype = np.dtype(object)).sort_index()
        
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                continue
            
            try:
                stat.loc[group] = self.function(data_subset)

            except Exception as e:
                raise util.CytoflowOpError('function',
                                           "Your function threw an error in group {}"
                                           .format(group)) from e    
                            
            # check for, and warn about, NaNs.
            if np.any(np.isnan(stat.loc[group])):
                warn("Category {} returned {}".format(group, stat.loc[group]), 
                     util.CytoflowOpWarning)
                    
        # try to convert to numeric, but if there are non-numeric bits ignore
        stat = pd.to_numeric(stat, errors = 'ignore')

        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        if self.statistic_name:
            new_experiment.statistics[(self.name, self.statistic_name)] = stat
        else:
            new_experiment.statistics[(self.name, self.function.__name__)] = stat

        
        return new_experiment
