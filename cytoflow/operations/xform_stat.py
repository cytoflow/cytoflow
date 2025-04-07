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
cytoflow.operations.xform_stat
------------------------------

Transforms a statistic. `xform_stat` has one class:

`TransformStatisticOp` -- apply a function to a statistic, making a new statistic.
"""

from warnings import warn
import pandas as pd
import numpy as np 

from traits.api import (HasStrictTraits, Str, List, Constant, provides,
                        Callable, Tuple, Any)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class TransformStatisticOp(HasStrictTraits):
    """
    Apply a function to a statistic, creating a new statistic.  
    
    If you set `by`, then `function` must be a reduction. Calling `apply`
    will group the input statistic by unique combinations of the conditions in
    `by`, then call `function` on each column in each group. The `function` 
    should take a `pandas.Series` and return a ``float``. The resulting statistic
    will have the same columns as the original statistic, but the levels in
    its index will be the same as the conditions in `by`.
    
    Alternately, if `by` is left empty, then `function` must be a transformation.
    `function` must take a `pandas.Series` as an argument and return a `pandas.Series`
    with exactly the same index. `function` will be called on each column of the 
    input statistic in turn.

    Attributes
    ----------
    name : Str
        The operation name.  Becomes the name of the new statistic.
    
    statistic : Str
        The statistic to apply the function to.
        
    function : Callable
        The function used to transform the statistic.  `function` must 
        take a `pandas.DataFrame` as its only parameter.  The return type is 
        arbitrary, but to work with the rest of `cytoflow` it should 
        probably be a numeric type or an iterable of numeric types..  If 
        `statistic_name` is unset, the name of the function becomes the 
        second in element in the `Experiment.statistics` key tuple.
        
    by : List(Str)
        A list of metadata attributes to aggregate the input statistic before 
        applying the function.  For example, if the statistic has two indices
        ``Time`` and ``Dox``, setting ``by = ["Time", "Dox"]`` will apply 
        `function` separately to each subset of the data with a unique 
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

    name = Str
    statistic = Str
    function = Callable
    by = List(Str)    
    fill = Any(0)

    def apply(self, experiment):
        """
        Applies `function` to a statistic.
        
        Parameters
        ----------
        experiment : `Experiment`
            The `Experiment` to apply the operation to
        
        Returns
        -------
        Experiment
            The same as the old experiment, but with a new statistic that
            results from applying `function` to the statistic specified
            in `statistic`.
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "Must specify an experiment")

        if not self.name:
            raise util.CytoflowOpError('name',
                                       "Must specify a name")
        
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name)) 
        
        if not self.statistic:
            raise util.CytoflowViewError('statistic',
                                         "Statistic not set")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic',
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
        else:
            stat = experiment.statistics[self.statistic]

        if not self.function:
            raise util.CytoflowOpError('function',
                                       "Must specify a function")

        if self.name in experiment.statistics:
            raise util.CytoflowOpError('name',
                                       "{} is already in the experiment's statistics"
                                       .format(self.name))

        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "{} must be in the experiment's conditions")
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
                    
        new_stat = pd.DataFrame(data = np.full((len(stat.columns), len(idx)), self.fill),
                                columns = stat.columns,
                                index = idx, 
                                dtype = 'float').sort_index()
                    
        if self.by: 
            for column in stat.columns:                        
                for group in data[self.by].itertuples(index = False, name = None):                
                    if isinstance(stat.index, pd.MultiIndex):
                        s = stat.xs(group, level = self.by, drop_level = False)[column]
                    else:
                        s = stat.at[group, column]
                                        
                    if len(s) == 0:
                        continue
        
                    try:
                        new_stat.at[group, column] = self.function(s)
                    except Exception as e:
                        raise util.CytoflowOpError('function',
                                                   "Your function threw an error in group {}".format(group)) from e
                                            
                    # check for, and warn about, NaNs.
                    if np.any(np.isnan(new_stat.loc[group])):
                        warn("Category {} returned {}".format(group, new_stat.loc[group]), 
                             util.CytoflowOpWarning)
                    
        else:
            print(new_stat)
            for column in stat.columns: 
                new_stat[column] = self.function(stat[column])
            
            # if not isinstance(new_stat, pd.Series):
            #     raise util.CytoflowOpError('by',
            #                                "Transform function {} does not return a Series; "
            #                                "in this case, you must set 'by'"
            #                                .format(self.function))
                                                    
        # matched_series = True
        # for group in data[self.by].itertuples(index = False, name = None):
        #     if isinstance(stat.index, pd.MultiIndex):
        #         s = stat.xs(group, level = self.by, drop_level = False)
        #     else:
        #         s = stat.loc[list(group)]
        #
        #     if isinstance(new_stat.loc[group], pd.Series) and \
        #         s.index.equals(new_stat.loc[group].index):
        #         pass
        #     else:
        #         matched_series = False
        #         break
        #
        # if matched_series and len(self.by) > 0:
        #     new_stat = pd.concat(new_stat.values)

        # try to convert to numeric, but if there are non-numeric bits ignore
        # try:
        #     stat = pd.to_numeric(stat)
        # except:  # if there are errors, ignore them
        #     pass
        
        # sort the index, for performance
        new_stat = new_stat.sort_index()
        
        new_experiment = experiment.clone(deep = False)
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        new_experiment.statistics[self.name] = new_stat

        return new_experiment
