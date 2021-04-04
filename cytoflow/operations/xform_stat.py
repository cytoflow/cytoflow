#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
cytoflow.operations.xform_stat
------------------------------
'''

from warnings import warn
import pandas as pd
import numpy as np 

from traits.api import (HasStrictTraits, Str, List, Constant, provides,
                        Callable, Tuple, Any, Undefined)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class TransformStatisticOp(HasStrictTraits):
    """
    Apply a function to a statistic, creating a new statistic.  The function can
    be applied to the entire statistic, or it can be applied individually to 
    groups of the statistic.  The function should take a :class:`pandas.Series` 
    as its only argument.  Return type is arbitrary, but a to be used with the 
    rest of :class:`cytoflow` it should probably be a numeric type or an 
    iterable of numeric types.
    
    As a special case, if the function returns a :class:`pandas.Series` *with 
    the same index that it was passed*, it is interpreted as a transformation.  
    The resulting statistic will have the same length, index names and index 
    levels as the original statistic.

    Attributes
    ----------
    name : Str
        The operation name.  Becomes the first element in the
        :attr:`~Experiment.statistics` key tuple.
    
    statistic : Tuple(Str, Str)
        The statistic to apply the function to.
        
    function : Callable
        The function used to transform the statistic.  :attr:`function` must 
        take a :class:`pandas.Series` as its only parameter.  The return type is 
        arbitrary, but to work with the rest of :class:`cytoflow` it should 
        probably be a numeric type or an iterable of numeric types..  If 
        :attr:`statistic_name` is unset, the name of the function becomes the 
        second in element in the :attr:`~Experiment.statistics` key tuple.
        
    statistic_name : Str
        The name of the function; if present, becomes the second element in
        the :attr:`~Experiment.statistics` key tuple.
        
    by : List(Str)
        A list of metadata attributes to aggregate the input statistic before 
        applying the function.  For example, if the statistic has two indices
        ``Time`` and ``Dox``, setting ``by = ["Time", "Dox"]`` will apply 
        :attr:`function` separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    fill : Any (default = 0)
        Value to use in the statistic if a slice of the data is empty.
   
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

    name = Str(Undefined)
    statistic = Tuple(Str, Str)
    function = Callable(Undefined)
    statistic_name = Str(Undefined)
    by = List(Str)    
    fill = Any(0)

    def apply(self, experiment):
        """
        Applies :attr:`function` to a statistic.
        
        Parameters
        ----------
        experiment : Experiment
            The experiment to apply the operation to
        
        Returns
        -------
        Experiment
            The same as the old experiment, but with a new statistic that
            results from applying :attr:`function` to the statistic specified
            in :attr:`statistic`.
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "Must specify an experiment")

        if self.name is Undefined:
            raise util.CytoflowOpError('name',
                                       "Must specify a name")
        
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name)) 
        
        if self.statistic is Undefined:
            raise util.CytoflowViewError('statistic',
                                         "Statistic not set")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic',
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
        else:
            stat = experiment.statistics[self.statistic]

        if self.function is Undefined:
            raise util.CytoflowOpError('function',
                                       "Must specify a function")
            
        stat_name = (self.name, self.statistic_name) \
                     if self.statistic_name is not Undefined \
                     else (self.name, self.function.__name__)
                     
        if stat_name in experiment.statistics:
            raise util.CytoflowOpError('name',
                                       "{} is already in the experiment's statistics"
                                       .format(stat_name))

        for b in self.by:
            if b not in stat.index.names:
                raise util.CytoflowOpError('by',
                                           "{} is not a statistic index; "
                                           " must be one of {}"
                                           .format(b, stat.index.names))
                
        data = stat.reset_index()
                
        if self.by:
            idx = pd.MultiIndex.from_product([data[x].unique() for x in self.by], 
                                             names = self.by)
        else:
            idx = stat.index.copy()
                    
        new_stat = pd.Series(data = self.fill,
                             index = idx, 
                             dtype = np.dtype(object)).sort_index()
                    
        if self.by:                         
            for group in data[self.by].itertuples(index = False, name = None):                
                if isinstance(stat.index, pd.MultiIndex):
                    s = stat.xs(group, level = self.by, drop_level = False)
                else:
                    s = stat.loc[list(group)]
                                    
                if len(s) == 0:
                    continue
    
                try:
                    new_stat[group] = self.function(s)
                except Exception as e:
                    raise util.CytoflowOpError('function',
                                               "Your function threw an error in group {}".format(group)) from e
                                        
                # check for, and warn about, NaNs.
                if np.any(np.isnan(new_stat.loc[group])):
                    warn("Category {} returned {}".format(group, new_stat.loc[group]), 
                         util.CytoflowOpWarning)
                    
        else:
            new_stat = self.function(stat)
            
            if not isinstance(new_stat, pd.Series):
                raise util.CytoflowOpError('by',
                                           "Transform function {} does not return a Series; "
                                           "in this case, you must set 'by'"
                                           .format(self.function))
                
        new_stat.name = "{} : {}".format(stat_name[0], stat_name[1])
                                                    
        matched_series = True
        for group in data[self.by].itertuples(index = False, name = None):
            if isinstance(stat.index, pd.MultiIndex):
                s = stat.xs(group, level = self.by, drop_level = False)
            else:
                s = stat.loc[list(group)]

            if isinstance(new_stat.loc[group], pd.Series) and \
                s.index.equals(new_stat.loc[group].index):
                pass
            else:
                matched_series = False
                break
            
        if matched_series and len(self.by) > 0:
            new_stat = pd.concat(new_stat.values)
            
        # try to convert to numeric, but if there are non-numeric bits ignore
        new_stat = pd.to_numeric(new_stat, errors = 'ignore')
        
        # sort the index, for performance
        new_stat = new_stat.sort_index()
        
        new_experiment = experiment.clone()
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        if self.statistic_name:
            new_experiment.statistics[(self.name, self.statistic_name)] = new_stat
        else:
            new_experiment.statistics[(self.name, self.function.__name__)] = new_stat

        return new_experiment
