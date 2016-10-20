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

from traits.api import (HasStrictTraits, Str, List, Constant, provides, 
                        Callable, CStr)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class StatisticsOp(HasStrictTraits):
    """
    Apply a function to subsets of a data set, and add it as a statistic
    to the experiment.
    
    The `apply()` function groups the data by the variables in `by`, then
    applies the `function` callable to each subset.  The callable should take
    a Series or a DataFrame and return a float.
    
    Attributes
    ----------
    name : Str
        The operation name.  Becomes the first element in the
        Experiment.statistics key tuple.
    
    channel : Str, optional
        The channel to apply the function to.  If specified, `function` must
        take a Series and return a float; otherwise, `function` must take
        a `pandas.DataFrame` and return a float.
        
    function : Callable
        The function used to compute the statistic.  If `channel` is set,
        `function` takes a Series and returns a float; otherwise, `function`
        takes a `pandas.DataFrame` and returns a float. If `function_name` is 
        empty, the name of the function becomes the second in element in the 
        Experiment.statistics key tuple.
        
    function_name : Str
        The name of the function; if present, becomes the second element in
        the Experiment.statistics key tuple.
        
    by : List(Str)
        A list of metadata attributes to aggregate the data before applying the
        function.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will apply `function` 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
        
    subset : Str
        A Python expression sent to Experiment.query() to subset the data before
        computing the statistic.
   
    Examples
    --------
    
    >>> stats_op = StatisticsOp(name = "Mean",
    ...                         channel = "Y2-A",
    ...                         function = np.mean,
    ...                         by = ["Dox"])
    >>> ex2 = stats_op.apply(ex)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.statistics')
    friendly_id = Constant("Statistics")
    
    name = CStr()
    channel = Str()
    function = Callable()
    function_name = Str()
    by = List(Str)
    subset = Str()
    
    def apply(self, experiment):
        """
        Estimate the Gaussian mixture model parameters
        """
        
        if not experiment:
            raise util.CytoflowOpError("No experiment specified")

        if not self.name:
            raise util.CytoflowOpError("Name isn't specified")

        if self.channel and self.channel not in experiment.data:
            raise util.CytoflowOpError("Channel {0} not found in the experiment"
                                  .format(self.channel))
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))
            if len(experiment.data[b].unique()) > 100: #WARNING - magic number
                raise util.CytoflowOpError("More than 100 unique values found for"
                                      " aggregation metadata {0}.  Did you"
                                      " accidentally specify a data channel?"
                                      .format(b))
                
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                
            if len(experiment) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
                
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda x: True)
                        
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data"
                     .format(group), 
                     util.CytoflowOpWarning)
        
        if self.channel:
            stat = groupby[self.channel].aggregate(self.function)
        else:
            idx = pd.MultiIndex(levels = [[]] * len(self.by), 
                                labels = [[]] * len(self.by), 
                                names = self.by)
            stat = pd.Series(index = idx)
            
            for group, data_subset in groupby:
                stat[group] = self.function(data_subset)
        
        new_experiment = experiment.clone()
        
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        if self.function_name:
            new_experiment.statistics[(self.name, self.function_name)] = stat
        else:
            new_experiment.statistics[(self.name, self.function.__name__)] = stat

        
        return new_experiment
