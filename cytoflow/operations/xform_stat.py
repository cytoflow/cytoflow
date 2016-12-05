#!/usr/bin/env python2.7

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
Created on Sep 13, 2016

@author: brian
'''

from __future__ import division, absolute_import

from warnings import warn
import pandas as pd
import numpy as np

from traits.api import (HasStrictTraits, Str, List, Constant, provides, 
                        Callable, CStr, Tuple, Any, Undefined)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class TransformStatisticOp(HasStrictTraits):
    """
    Apply a function to a statistic, creating a new statistic.  The function can
    be applied to the entire statistic, or it can be applied individually to groups
    of the statistic.  The function should take a `pandas.Series` as its only argument.
    Return type is arbitrary, but a `float` or a `pandas.Series` is most common.

    Attributes
    ----------
    name : Str
        The operation name.  Becomes the first element in the
        Experiment.statistics key tuple.
    
    statistic : Tuple(Str, Str)
        The statistic to apply the function to.
        
    function : Callable
        The function used to transform the statistic.  `function` must take a 
        Series as its only parameter.  The return type is arbitrary, but a `float`
        or a `pandas.Series` is most common.  If `statistic_name` is unset, the name 
        of the function becomes the second in element in the Experiment.statistics key tuple.
        
    statistic_name : Str
        The name of the function; if present, becomes the second element in
        the Experiment.statistics key tuple.
        
    by : List(Str)
        A list of metadata attributes to aggregate the input statistic before 
        applying the function.  For example, if the statistic has two indices
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will apply `function` 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
        
    fill : Any (default = 0)
        Value to fill NaNs in the output
   
    Examples
    --------
    
    >>> stats_op = ChannelStatisticOp(name = "Mean",
    ...                               channel = "Y2-A",
    ...                               function = np.mean,
    ...                               by = ["Dox"])
    >>> ex2 = stats_op.apply(ex)
    >>> log_op = TransformStatisticOp(name = "LogMean",
    ...                               statistic = ("Mean", "mean"),
    ...                               function = np.log)
    >>> ex3 = log_op.apply(ex2)  
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.transform_statistic')
    friendly_id = Constant("Transform Statistic")
    
    name = CStr()
    statistic = Tuple(Str, Str)
    function = Callable()
    statistic_name = Str()
    by = List(Str)    
    fill = Any(Undefined)

    def apply(self, experiment):
        
        if not experiment:
            raise util.CytoflowOpError("Must specify an experiment")

        if not self.name:
            raise util.CytoflowOpError("Must specify a name")
        
        if not self.statistic:
            raise util.CytoflowViewError("Statistic not set")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError("Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
        else:
            stat = experiment.statistics[self.statistic]

        if not self.function:
            raise util.CytoflowOpError("Must specify a function")

        if not self.by:
            raise util.CytoflowOpError("Must specify some grouping conditions "
                                       "in 'by'")
       
        for b in self.by:
            if b not in stat.index.names:
                raise util.CytoflowOpError("{} is not a statistic index; "
                                           " must be one of {}"
                                           .format(b, stat.index.names))
                
        data = stat.reset_index()
        
        idx = pd.MultiIndex.from_product([data[x].unique() for x in self.by], 
                                         names = self.by)
        
        new_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
                
        for group in data[self.by].itertuples(index = False):
            s = stat.xs(group, level = self.by)
            try:
                new_stat[group] = self.function(s)
            except Exception as e:
                raise util.CytoflowOpError("Your function threw an error: {}"
                                      .format(e))
        
        # fill in NaNs; in general, we don't want those.
        if self.fill is Undefined:
            fill = 0
        else:
            fill = self.fill
                
        new_stat.fillna(fill, inplace = True)
                
        # special handling for lists
        if type(new_stat.iloc[0]) is pd.Series:
            new_stat = pd.concat(new_stat.to_dict(), names = self.by + new_stat.iloc[0].index.names)
        
        new_experiment = experiment.clone()
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        if self.statistic_name:
            new_experiment.statistics[(self.name, self.statistic_name)] = new_stat
        else:
            new_experiment.statistics[(self.name, self.function.__name__)] = new_stat

        return new_experiment
