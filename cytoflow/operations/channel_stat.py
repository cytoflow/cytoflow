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
cytoflow.operations.channel_stat
--------------------------------

Creates a new statistic. `channel_stat` has one class:

`ChannelStatisticOp` -- applies a function to subsets of a data set,
and adds the resulting statistic to the `Experiment`
"""

from warnings import warn
import pandas as pd
import numpy as np

from traits.api import (HasStrictTraits, Str, List, Constant, provides, 
                        Callable)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class ChannelStatisticOp(HasStrictTraits):
    """
    Apply a functions to subsets of a data set, and add it as a 
    statistic to the experiment.
    
    The `apply` function groups the data by the variables in `by`, 
    then applies the `function` callable to each group in the channel
    specified by `channel`. 
    
    The `function` callable should take a single `pandas.Series` of ``float`` 
    as an argument and return a ``float``, a value that can be cast to 
    ``float``, or a `pandas.Series` of ``float``. If `function` returns a 
    ``float`` or a value that can be cast to ``float``, then the resulting 
    statistic has one column and its name is set to `channel`. If `function`
    returns a `pandas.Series`, then the ``Series``' index labels become the 
    column names. (If used this way, `function` must **always** return a 
    `pandas.Series` with the same index.)
    
    Attributes
    ----------
    name : Str
        The operation name.  Becomes the name of the new statistic.
    
    channel : Str
        The channel to apply the function to. The channels become the column
        names in the new statistic.
        
    function : Callable
        The function used to compute the statistic.  `function` must take 
        a `pandas.Series` as its only parameter and return either a ``float``,
        a value that can be cast to ``float``, or a `pandas.Series`.  
        
        .. warning::
            Be careful!  Sometimes this function is called with an empty input!
            If this is the case, poorly-behaved functions can return ``NaN`` or 
            throw an error.  If this happens, it will be reported.
        
    by : List(Str)
        A list of metadata attributes to aggregate the data before applying the
        function.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting ``by = ["Time", "Dox"]`` will apply 
        `function` separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    subset : Str
        A Python expression sent to `Experiment.query` to subset the 
        data before computing the statistic.
   
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
        
        >>> ch_op = flow.ChannelStatisticOp(name = 'MeanByDox',
        ...                                 channel = 'Y2-A',
        ...                                 function = flow.geom_mean,
        ...                                 by = ['Dox'])
        >>> ex2 = ch_op.apply(ex)
        
    View the new operation
    
    >>> print(ex2.statistics.keys())
    dict_keys(['MeanByDox'])

    >>> print(ex2.statistics['MeanByDox'])
                Y2-A       B1-A
    Dox                        
    1.0    19.805601  34.845373
    10.0  446.981927  29.917667

    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.channel_statistic')
    friendly_id = Constant("Channel Statistic")
    
    name = Str
    channel = Str
    function = Callable
    by = List(Str)
    subset = Str
    
    def apply(self, experiment):
        """
        Apply the operation to an `Experiment`.
        
        Parameters
        ----------
        experiment
            The `Experiment` to apply this operation to.
            
        Returns
        -------
        Experiment
            A new `Experiment`, containing a new entry in 
            `Experiment.statistics`.  The key of the new entry is a 
            tuple ``(name, function)`` (or ``(name, statistic_name)`` if 
            `statistic_name` is set.
        """

        if not self.name:
            raise util.CytoflowOpError('name', "Must specify a name")
        
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name))  
        
        if not self.channel:
            raise util.CytoflowOpError('channels', "Must specify a channel")

        if not self.function:
            raise util.CytoflowOpError('function', "Must specify a function")

        if self.channel not in experiment.data:
            raise util.CytoflowOpError('channels',
                                       "Channel {} not found in the experiment"
                                       .format(self.channel))
            
        if not self.by:
            raise util.CytoflowOpError('by',
                                       "Must specify some grouping conditions "
                                       "in 'by'")
                     
        if self.name in experiment.statistics:
            raise util.CytoflowOpError('name',
                                       "{} is already in the experiment's statistics"
                                       .format(self.name))

        new_experiment = experiment.clone(deep = False)
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except Exception as exc:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' isn't valid"
                                           .format(self.subset)) from exc
       
        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
            unique = experiment.data[b].unique()

            if len(unique) == 1:
                warn("Only one category for {}".format(b), util.CytoflowOpWarning)

        groupby = experiment.data.groupby(self.by, observed = False)
                
        idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by], 
                                         names = self.by)
        
        stat = None
        
        for group, data_subset in groupby:
            try:
                v = self.function(data_subset[self.channel])
                
            except Exception as e:
                raise util.CytoflowOpError(None,
                                           "Your function threw an error in group {}"
                                           .format(group)) from e
                                           
            try:
                v = float(v)
            except (TypeError, ValueError):
                if not isinstance(v, pd.Series):
                    raise util.CytoflowOpError(None,
                                               "Your function returned a {}. It must return "
                                               "a float, a value that can be cast to float, "
                                               "or a pandas.Series (with type float)"
                                               .format(type(v)))
                    
            if isinstance(v, pd.Series) and v.dtype.kind != 'f':
                raise util.CytoflowOpError(None,
                                           "Your function returned a pandas.Series with dtype {}. "
                                           "If it returns a Series, the data must be floating point."
                                           .format(v.dtype))
                
            if stat is None:
                if isinstance(v, float):
                    stat = pd.DataFrame(data = np.full((len(idx), 1), np.nan),
                                        index = idx,
                                        columns = [self.channel],
                                        dtype = 'float' ).sort_index()
                elif isinstance(v, pd.Series):
                    stat = pd.DataFrame(data = np.full((len(idx), len(v)), np.nan),
                                        index = idx,
                                        columns = v.index.tolist(),
                                        dtype = 'float').sort_index()

                first_v = v
                
            if type(v) != type(first_v):
                raise util.CytoflowOpError('',
                                           "The first call to your function returned a {}, "
                                           "but calling it on group {} returned a {}"
                                           .format(type(first_v), group, type(v)))                           

            stat.loc[group] = v
            print(group)
            print(v)

            # fail on NaNs.
            if stat.loc[group].isna().any():
                if len(data_subset) == 0:
                    raise util.CytoflowOpError('',
                                               "Calling function on category {} returned {} "
                                               "which contains NaN. Also, there was no data in that group. "
                                               "Make sure that your function behaves when called on an "
                                               "empty pandas.Series (by returning 0, for example)".format(group, stat.loc[group]))
                    
                raise util.CytoflowOpError('',
                                           "Calling function on category {} returned {} "
                                           "which contains NaN".format(group, stat.loc[group]))
        
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        new_experiment.statistics[self.name] = stat
        
        return new_experiment
