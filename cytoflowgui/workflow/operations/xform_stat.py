#!/usr/bin/env python3.8

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
cytoflowgui.workflow.operations.xform_stat
------------------------------------------

"""

import numpy as np
import scipy.stats
import pandas
from warnings import warn

from traits.api import (Str, Callable, Property, List, provides, observe, Undefined)

import cytoflow.utility as util
from cytoflow import TransformStatisticOp
                       
from cytoflowgui.workflow.serialization import camel_registry, traits_repr
from .operation_base import IWorkflowOperation, WorkflowOperation

from ..subset import ISubset

TransformStatisticOp.__repr__ = traits_repr

mean_95ci = lambda x: util.ci(x, np.mean, boots = 100)
geomean_95ci = lambda x: util.ci(x, util.geom_mean, boots = 100)

transform_functions = {"Mean" : np.mean,
                       "Geom.Mean" : util.geom_mean,
                       "Median" : np.median,
                       "Count" : len,
                       "Std.Dev" : np.std,
                       "Geom.SD" : util.geom_sd_range,
                       "SEM" : scipy.stats.sem,
                       "Geom.SEM" : util.geom_sem_range,
                       "Mean 95% CI" : mean_95ci,
                       "Geom.Mean 95% CI" : geomean_95ci,
                       "Sum" : np.sum,
                       "Proportion" : lambda a: pandas.Series(a / a.sum()),
                       "Percentage" : lambda a: pandas.Series(a / a.sum()) * 100.0,
                       "Fold" : lambda a: pandas.Series(a / a.min())
                       }


@provides(IWorkflowOperation)
class TransformStatisticWorkflowOp(WorkflowOperation, TransformStatisticOp):
    name = Str(apply = True)
    statistic = Str(apply = True)
    function_name = Str(apply = True)
    by = List(Str, apply = True)  
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, apply = True)

    # functions aren't picklable, so send the name instead
    function = Callable(transient = True)
    
    fill = 0
        
    # bits to support the subset editor
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    def apply(self, experiment):
        if not self.function_name:
            raise util.CytoflowOpError("Transform function not set")
        
        self.function = transform_functions[self.function_name]
        
        ret = TransformStatisticOp.apply(self, experiment)
        
        stat = ret.statistics[self.name]
        
        if Undefined in stat:
            warn("One of the transformed values was Undefined. "
                 "Subsequent operations may fail. "
                 "Please report this as a bug! ")
                    
        return ret
    
    def clear_estimate(self):
        # no-op
        return

    def get_notebook_code(self, idx):
        op = TransformStatisticOp()
        op.copy_traits(self, [x for x in op.copyable_trait_names() if x != 'fill'])
        
        fn_import = {"Mean" : "from numpy import mean",
                     "Median" : "from numpy import median",
                     "Geom.Mean" : None,
                     "Count" : None,
                     "Std.Dev" : "from numpy import std",
                     "Geom.SD" : None,
                     "SEM" : "from scipy.stats import sem",
                     "Geom.SEM" : None,
                     "Mean 95% CI" : None,
                     "Geom.Mean 95% CI" : None,
                     "Sum" : "from numpy import sum",
                     "Proportion" : "from pandas import Series",
                     "Percentage" : "from pandas import Series",
                     "Fold" : "from pandas import Series"
                  }
        
        # fn_name = {"Mean" : "mean",
        #            "Median" : "median",
        #            "Geom.Mean" : "geom_mean",
        #            "Count" : "len",
        #            "Std.Dev" : "std",
        #            "Geom.SD" : "geom_sd_range",
        #            "SEM" : "sem",
        #            "Geom.SEM" : "geom_sem_range",
        #            "Mean 95% CI" : "lambda x: ci(x, mean, boots = 100)",
        #            "Geom.Mean 95% CI" : "lambda x: ci(x, geom_mean, boots = 100)",
        #            "Sum" : "sum",
        #            "Proportion" : "lambda a: Series(a / a.sum())",
        #            "Percentage" : "lambda a: Series(a / a.sum()) * 100.0",
        #            "Fold" : "lambda a: Series(a / a.min())"
        #            }
        
        op.function = transform_functions[self.function_name]
        # try:
        #     op.function.__name__ = fn_name[self.statistic_name]
        # except AttributeError:
        #     # can't reassign the name of "len", for example
        #     pass
        
        return "\n{import_statement}\nop_{idx} = {repr}\n\nex_{idx} = op_{idx}.apply(ex_{prev_idx})" \
            .format(import_statement = (fn_import[self.function_name]
                                        if fn_import[self.function_name] is not None
                                        else ""),
                repr = repr(op),
                idx = idx,
                prev_idx = idx - 1) 
            
### Serialization
@camel_registry.dumper(TransformStatisticWorkflowOp, 'transform-statistic', version = 2)
def _dump(op):
    return dict(name = op.name,
                statistic = op.statistic,
                function_name = op.function_name,
                by = op.by,
                subset_list = op.subset_list)

@camel_registry.dumper(TransformStatisticWorkflowOp, 'transform-statistic', version = 1)
def _dump_v1(op):
    return dict(name = op.name,
                statistic = op.statistic,
                statistic_name = op.function_name,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('transform-statistic', version = 2)
def _load(data, version):
    return TransformStatisticWorkflowOp(**data)

@camel_registry.loader('transform-statistic', version = 1)
def _load_v1(data, version):
    data['statistic'] = tuple(data['statistic'])[0]
    del data['statistic_name']
    # TODO - some warning about how stats have changed.
    return TransformStatisticWorkflowOp(**data)

