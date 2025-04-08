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
                        Callable, Float, Union)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class ChannelStatisticOp(HasStrictTraits):
    """
    Apply a function to subsets of a data set, and add it as a statistic
    to the experiment.
    
    The `apply` function groups the data by the variables in `by`, 
    then applies the `function` callable to each group in each channel in 
    `channels`. The callable should take a single `pandas.Series` 
    as an argument and return a ``float`` (or type that can be coerced
    to ``float``.
    
    Attributes
    ----------
    name : Str
        The operation name.  Becomes the name of the new statistic.
    
    channels : List(Str)
        The channels to apply the function to. These channels become the column
        names in the new statistic.
        
    function : Callable
        The function used to compute the statistic.  `function` must take 
        a `pandas.Series` as its only parameter and return a ``float``.  
        (or type that can be coerced to a ``float``.)
        
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
        
    fill : Float (default = `pandas.NA`)
        The value to use in the statistic if a slice of the data is empty.
   
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
        ...                                 channels = ['Y2-A', 'B1-A'],
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
    channels = List(Str)
    function = Callable
    by = List(Str)
    subset = Str
    fill = Union(Constant(pd.NA), Float, default_value = pd.NA)
    
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
        
        if experiment is None:
            raise util.CytoflowOpError('experiment', "Must specify an experiment")

        if not self.name:
            raise util.CytoflowOpError('name', "Must specify a name")
        
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name))  
        
        if not self.channels:
            raise util.CytoflowOpError('channels', "Must specify at least one channel")

        if not self.function:
            raise util.CytoflowOpError('function', "Must specify a function")

        for channel in self.channels:
            if channel not in experiment.data:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not found in the experiment"
                                           .format(channel))
            
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
                
            if len(experiment) == 0:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' returned no events"
                                           .format(self.subset))
       
        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
            unique = experiment.data[b].unique()

            if len(unique) == 1:
                warn("Only one category for {}".format(b), util.CytoflowOpWarning)

        groupby = experiment.data.groupby(self.by, observed = True)

        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data"
                     .format(group), 
                     util.CytoflowOpWarning)
                
        idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by], 
                                         names = self.by)

        stat = pd.DataFrame(data = np.full((len(self.channels), len(idx)), self.fill),
                            index = idx, 
                            columns = self.channels,
                            dtype = 'float').sort_index()
        
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                continue
            
            if not isinstance(group, tuple):
                group = (group,)
            
            for channel in self.channels:
                try:
                    v = self.function(data_subset[channel])
                    stat.at[group, channel] = v
    
                except Exception as e:
                    raise util.CytoflowOpError(None,
                                               "Your function threw an error in group {}"
                                               .format(group)) from e
                
                # check for, and warn about, NaNs.
                if pd.Series(stat.loc[group]).isna().any():
                    warn("Found NaN in category {} returned {}"
                         .format(group, stat.loc[group]), 
                         util.CytoflowOpWarning)
                    
        # try to convert to numeric, but if there are non-numeric bits ignore
        # try:
        #     stat = pd.to_numeric(stat)
        # except:  # if there are errors, ignore them
        #     pass
        
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        new_experiment.statistics[self.name] = stat
        
        return new_experiment
