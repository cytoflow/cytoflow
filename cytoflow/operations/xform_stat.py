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

import pandas as pd
import numpy as np 

from traits.api import (HasStrictTraits, Str, List, Constant, provides,
                        Callable, Bool)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class TransformStatisticOp(HasStrictTraits):
    """
    Apply a function to a feature of a statistic, creating a new statistic.  
    
    If you set `by`, then calling `apply` will group the input statistic by 
    unique combinations of the conditions in `by`, then call `function` on the
    column specified by `feature` in each group. The `function` should take a 
    `pandas.Series` and it can return a ``float``, a value that can be cast to 
    a ``float``, or `pandas.Series` whose `dtype` is a floating-point. 
    
    If `function` returns a ``float``, then the resulting statistic
    will have one column with the name set to `feature` and levels that are the
    same as the conditions in `by`.
    
    If `function` returns a `pandas.Series`, then the names of the rows will
    become the names of the columns in the new statistic and the levels will
    be the same as the conditions in `by`.
    
    .. note::
        If `function` returns a `pandas.Series`, it must have an index with only
        one level -- no hierarchical indexing, please!
    
    .. note::
        If `function` returns a `pandas.Series`, it must return a series with the
        same index each time! 
    
    Finally, if `by` is left empty, then `function` must be a transformation.
    `function` must take a `pandas.Series` as an argument and return a `pandas.Series`
    with exactly the same index. The new statistic will contain that `pandas.Series`
    as its only column, with the column name set to `feature`.

    Attributes
    ----------
    name : Str
        The operation name.  Becomes the name of the new statistic.
    
    statistic : Str
        The statistic to apply `function` to.
        
    feature : Str
        The feature to apply `function` to.
        
    function : Callable
        The function used to transform the statistic.  `function` must 
        take a `pandas.Series` as its only parameter and return a ``float``,
        a value that can be cast to ``float``, or a `pandas.Series` whose 
        ``dtype`` is ``float``.
        
    by : List(Str)
        A list of metadata attributes to aggregate the input statistic before 
        applying the function.  For example, if the statistic has two indices
        ``Time`` and ``Dox``, setting ``by = ["Time", "Dox"]`` will apply 
        `function` separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    ignore_incomplete_groups : Bool (default = False)
        Sometimes, a statistic doesn't have a row for every possible group of
        labels. If this flag is true, groups that don't have all possible
        labels of the non-grouped levels won't have `function` called -- this
        can make writing `function` easier, at the cost of losing some data.

    Examples
    --------
    
    .. plot::
        :context: close-figs
        
        Make a little data set.
    
        >>> import cytoflow as flow
        >>> import pandas as pd
        >>> import numpy as np
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
        
    Transform the statistic
    
    .. plot::
        :context: close-figs
        
        >>> xform_op = flow.TransformStatisticOp(name = 'LogMean',
        ...                                      statistic = 'MeanByDox',
        ...                                      feature = 'Y2-A',
        ...                                      function = np.log)
        
        >>> ex_3 = xform_op.apply(ex2)
        >>> ex_3.statistics['LogMean']
            Y2-A
        Dox    
        1.0    2.985965
        10.0    6.102518

    """
    
    id = Constant('cytoflow.operations.transform_statistic')
    friendly_id = Constant("Transform Statistic")

    name = Str
    statistic = Str
    feature = Str
    function = Callable
    by = List(Str)    
    ignore_incomplete_groups = Bool(False)

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
            raise util.CytoflowOpError('statistic',
                                         "Statistic not set")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowOpError('statistic',
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
        else:
            stat = experiment.statistics[self.statistic]
            
        if not self.feature:
            raise util.CytoflowOpError('feature',
                                       "Must set a feature")
            
        if self.feature not in stat:
            raise util.CytoflowOpError('feature',
                                       "Can't find feature {} in statistic {}"
                                       .format(self.feature, self.statistic))

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
                
        new_stat = None
                    
        if self.by: 
            for group in stat.index.to_frame()[self.by].itertuples(index = False, name = None):  
                s = stat.xs(group, level = self.by, drop_level = True)[self.feature]

                if len(s) == 0:
                    continue
                
                if isinstance(s.index, pd.MultiIndex):
                    idx = s.index.remove_unused_levels()
                    idx_incomplete = [set(idx.levels[li]) != set(stat.index.to_frame()[level].unique())
                                     for li, level in enumerate(idx.names)]
                    if any(idx_incomplete) and self.ignore_incomplete_groups:
                        continue 
                else:
                    idx = s.index
                    if set(idx.values) != set(stat.index.to_frame()[idx.name].unique()) and self.ignore_incomplete_groups:
                        continue

                try:
                    v = self.function(s)
                except Exception as e:
                    raise util.CytoflowOpError('function',
                                               "Your function threw an error in group {}".format(group)) from e
                           
                if isinstance(v, pd.Series):
                    if v.dtype.kind != 'f':
                        raise util.CytoflowOpError('function',
                                                   "Your function returned a pandas.Series with dtype {}. "
                                                   "If it returns a Series, the data must be floating point."
                                                   .format(v.dtype))
                        
                    # check for, and warn about, NaNs.
                    if np.any(np.isnan(v)):
                        raise util.CytoflowOpError('function',
                                                   "Category {} returned {}, which had NaNs that aren't allowed"
                                                   .format(group, v))
                        
                    # check for, and warn about, NaNs.
                    if np.any(np.isinf(v)):
                        raise util.CytoflowOpError('function',
                                                   "Category {} returned {}, which had infs that aren't allowed"
                                                   .format(group, v))
                else:
                    try:
                        v = float(v)
                    except (TypeError, ValueError) as e:
                        if not isinstance(v, pd.Series):
                            raise util.CytoflowOpError('function',
                                                       "Your function returned a {}. It must return "
                                                       "a float, a value that can be cast to float, "
                                                       "or a pandas.Series (with type float)"
                                                       .format(type(v))) from e
                                                       
                    if np.isnan(v):
                        raise util.CytoflowOpError('function',
                                                   "Category {} returned {} and NaNs aren't allowed"
                                                   .format(group, v))
                        
                    if np.isinf(v):
                        raise util.CytoflowOpError('function',
                                                   "Category {} returned {} and infs aren't allowed"
                                                   .format(group, v))
                    
                if new_stat is None:
                    if isinstance(v, float):
                        new_stat = pd.DataFrame(index = pd.MultiIndex.from_tuples([], names = self.by),
                                                columns = [self.feature],
                                                dtype = 'float' ).sort_index()
                    else:
                        if v.index.nlevels > 1:
                            raise util.CytoflowOpError('function',
                                                       "Your function returned a Series with a multi-level index!")
                            
                        new_stat = pd.DataFrame(index = pd.MultiIndex.from_tuples([], names = self.by),
                                                columns = v.index.tolist(),
                                                dtype = 'float').sort_index()
                        first_v = v
                elif isinstance(v, pd.Series):
                    if not v.index.equals(first_v.index):
                        raise util.CytoflowOpError('function',
                                                   "The first call of 'function' returned series with index of {}, "
                                                   "but the call on group {} returned a series with index {}. "
                                                   "All returned series must have the same index!"
                                                   .format(first_v.index, group, v.index))
                new_stat.loc[group] = v
                                        
                # # check for, and warn about, NaNs.
                # if np.any(np.isnan(new_stat.loc[group])):
                #     raise util.CytoflowOpError('function',
                #                                "Category {} returned {}, which had NaNs that aren't allowed"
                #                                .format(group, new_stat.loc[group]))
                
        else:
            idx = stat.index.copy()
            new_stat = pd.DataFrame(columns = [self.feature],
                                    index = idx, 
                                    dtype = 'float').sort_index()

            v = self.function(stat[self.feature])
            
            if not isinstance(v, pd.Series):
                raise util.CytoflowOpError('function',
                                           "If you don't specify 'by', your function must return a pandas.Series. "
                                           "Instead, the function returned {} ({})".format(v, type(v)))
            new_stat[self.feature] = v
        
        # sort the index, for performance
        new_stat = new_stat.sort_index()
        
        # make sure the new statistic's column index is a type 'string'
        new_stat.rename(columns = str, inplace = True)
        
        new_experiment = experiment.clone(deep = False)
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        new_experiment.statistics[self.name] = new_stat

        return new_experiment
