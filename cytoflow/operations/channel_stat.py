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
                        Callable, Float, Property)

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
    column names. (If used this way, each call to `function` must **always** 
    return a `pandas.Series` with the same index.)
    
    Attributes
    ----------
    name : Str
        The operation name.  Becomes the name of the new statistic.
    
    channels : List(Str)
        The channels to apply the function to. The channels become the column 
        (feature) names in the new statistic. If `function` returns a `pandas.Series`,
        the column index becomes a `pandas.MultiIndex`, and the channel names are
        the labels of the first level.
        
    function : Callable
        The function used to compute the statistic.  `function` must take 
        a `pandas.Series` as its only parameter and return either a ``float``,
        a value that can be cast to ``float``, or a `pandas.Series` of ``float``.  
        If `function` returns a `pandas.Series`, the column index of the new statistic
        will be a `pandas.MultiIndex` whose second level has a name the same as
        the name of the `pandas.Series` and whose labels are the row labels of
        the `pandas.Series`.
        
        .. note::
            If `function` returns a `pandas.Series`, please make sure that its
            row index is a plain single-level index. No ``MultiIndex`` shenanigans
            please!
        
        .. warning::
            Be careful!  Sometimes this function is called with an empty input!
            If this is the case, poorly-behaved functions can return ``NaN`` or 
            throw an error.  If this happens, an exception will be raised.
        
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
        >>> import pandas as pd
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
        
    View the new statistic
    
    .. plot::
        :context: close-figs
    
        >>> print(ex2.statistics.keys())
        dict_keys(['MeanByDox'])
        
        >>> print(ex2.statistics['MeanByDox'])
                    Y2-A    
        Dox                        
        1.0    19.805601  
        10.0  446.981927  

    """
    
    id = Constant('cytoflow.operations.channel_statistic')
    friendly_id = Constant("Channel Statistic")
    
    name = Str
    channels = List(Str)
    function = Callable
    by = List(Str)
    subset = Str
    fill = Float(np.nan)
    
    channel = util.Removed(err_string = "Statistics have changed dramatically "
                           "-- use `channels` instead of `channel`, and see the "
                           "documentation for more information.")
    
    # MAGIC: setter for attribute `channel`
    def _set_channel(self, val):
        print(val)
        warn("Statistics have changed -- you should use `channels` instead of `channel`",
             util.CytoflowOpWarning)
        self.channels = [val]
    
    # MAGIC: getter for attribute `channel`
    def _get_channel(self):
        warn("Statistics have changed -- you should use `channels` instead of `channel`",
             util.CytoflowOpWarning)
        return self.channels[0]

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
            `Experiment.statistics`.  The key of the new entry 
            is ``name``.
        """

        if not self.name:
            raise util.CytoflowOpError('name', "Must specify a name")
        
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name))  
        
        if not self.channels:
            raise util.CytoflowOpError('channels', "Must specify a channel")

        if not self.function:
            raise util.CytoflowOpError('function', "Must specify a function")

        for c in self.channels:
            if c not in experiment.data:
                raise util.CytoflowOpError('channels',
                                           "Channel {} not found in the experiment"
                                           .format(c))
            
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

        for i in idx:
            if (i[0] if idx.nlevels == 1 else i) not in groupby.indices:
                warn("No events for category {}".format( [str(i[0]) + "=" + str(i[1])  for i in zip(idx.names, i)]),
                     util.CytoflowOpWarning)
              
        stat = None
        
        for group, data_subset in groupby:
            for channel in self.channels:
                try:
                    v = self.function(data_subset[channel])
                    
                except Exception as e:
                    raise util.CytoflowOpError(None,
                                               "Your function threw an error in group {}"
                                               .format(group)) from e
                                               
                try:
                    v = float(v)
                except (TypeError, ValueError) as e:
                    if not isinstance(v, pd.Series):
                        raise util.CytoflowOpError(None,
                                                   "Your function returned a {}. It must return "
                                                   "a float, a value that can be cast to float, "
                                                   "or a pandas.Series (with type float)"
                                                   .format(type(v))) from e
                        
                if isinstance(v, pd.Series) and v.dtype.kind != 'f':
                    raise util.CytoflowOpError(None,
                                               "Your function returned a pandas.Series with dtype {}. "
                                               "If it returns a Series, the data must be floating point."
                                               .format(v.dtype))
                    
                if isinstance(v, float):
                    # fail on NaNs.
                    if pd.isna(v):
                        raise util.CytoflowOpError(None,
                                                   "Calling function on category {} returned {} "
                                                   "which contains NaN".format(group, v))
                    if stat is None:
                        stat = pd.DataFrame(data = np.full((len(idx), len(self.channels)), self.fill),
                                            index = idx,
                                            columns = self.channels,
                                            dtype = 'float' ).sort_index()
                    stat.loc[group] = v
                    

                elif isinstance(v, pd.Series):
                    # fail on NaNs.
                    if v.isna().any():
                        raise util.CytoflowOpError(None,
                                                   "Calling function on category {} returned {} "
                                                   "which contains NaN".format(group, v))
                        
                    if stat is None:
                        stat = pd.DataFrame(data = np.full((len(idx), len(v) * len(self.channels)), self.fill),
                                            index = idx,
                                            columns = pd.MultiIndex.from_product([self.channels, v.index.to_list()],
                                                                                 names = ["Channel", v.name]),
                                            dtype = 'float').sort_index()
                        first_v = v
                        
                    if not v.index.equals(first_v.index):
                        raise util.CytoflowOpError(None,
                                                   "The first call to your function returned a series with index {}, "
                                                   "but calling it on group {} returned a series with index {}"
                                                   .format(first_v.index, group, v.index))  

                    stat.loc[group, channel] = v.values
    
                    
                         
        

                    
        if stat.isna().any().any():
            raise util.CytoflowOpError(None,
                                       "The statistic has at least one NaN in it, which probably means "
                                       "one of the groups did not have any events AND you forgot to set "
                                       "'fill' to something other than NaN.".format(group, stat.loc[group]))
                
        
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        new_experiment.statistics[self.name] = stat
        
        return new_experiment
