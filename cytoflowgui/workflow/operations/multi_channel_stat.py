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
cytoflowgui.workflow.operations.channel_stat
--------------------------------------------

"""

import numpy as np
import pandas as pd
import scipy.stats

from traits.api import (HasTraits, Str, Callable, Property, Constant, List, provides, observe)

import cytoflow.utility as util
from cytoflow import FrameStatisticOp
                       
from cytoflowgui.workflow.serialization import camel_registry, traits_repr
from .operation_base import IWorkflowOperation, WorkflowOperation

from ..subset import ISubset

summary_functions = {"Mean" : np.mean,
                     "Geo.Mean" : util.geom_mean,
                     "Median" : np.median,
                     "Count" : len,
                     "Std.Dev" : np.std,
                     "Geo.SD" : util.geom_sd,
                     "SEM" : scipy.stats.sem,
                     "Geo.SEM" : util.geom_sem,
                     }

# fill = {"Mean +- SD" : 0,
#         "Geo.Mean */ SD" : 0,
#         "Median" : 0,
#         "Count" : 0,
#         "Std.Dev" : 0,
#         "Geo.SD" : 0,
#         "SEM" : 0,
#         "Mean +- SEM" : 0,
#         "Geo.Mean */ SEM" : 0,
#         "Mean +- 95% CI" : 0,
#         "Geo.Mean */ 95% CI" : 0
#         }

FrameStatisticOp.__repr__ = traits_repr

class Function(HasTraits):
    channel = Str
    function = Str
    feature = Str

    def __repr__(self):
        return traits_repr(self)

@provides(IWorkflowOperation)
class MultiChannelStatisticWorkflowOp(WorkflowOperation, FrameStatisticOp):
    id = Constant('edu.mit.synbio.cytoflowgui.workflow.operations.multi_channel_stat')

    # operation traits
    name = Str(apply = True)
    functions_list = List(Function, apply = True)
    by = List(Str, apply = True)
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, apply = True)
    
    # functions aren't picklable, so make this one transient 
    # and send the list of function names instead
    function = Callable(transient = True)
    fill = 0
    
    @observe('functions_list:items, functions_list:items.+type', post_init = True)
    def _on_functions_items_changed(self, _):
        self.changed = 'functions_list'
    
    # bits to support the subset editor
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
            
    def apply(self, experiment):
        for function in self.functions_list:
            if function.channel == "":
                raise util.CytoflowOpError('functions_list', "At least one channel isn't set.")
            if function.function == "":
                raise util.CytoflowOpError('functions_list', "At least one function isn't set.")
            if function.feature == "":
                raise util.CytoflowOpError('functions_list', "At least one feature isn't set.")
        
        self.function = lambda x, fl = self.functions_list : pd.Series({f.feature : summary_functions[f.function](x[f.channel])
                                                                        for f in fl})   
        
        return FrameStatisticOp.apply(self, experiment) 
    
    def clear_estimate(self):
        # no-op
        return
    
    def get_notebook_code(self, idx):
        op = FrameStatisticOp()
        op.copy_traits(self, op.copyable_trait_names())
        
        raise NotImplementedError("Notebook export for multi_channel_stat still TODO")
        
        # fn_import = {"Mean" : "from numpy import mean",
        #              "Geo.Mean" : None,
        #              "Median" : "from numpy import median",
        #              "Count" : None,
        #              "Std.Dev" : "from numpy import std",
        #              "Geo.SD" : None,
        #              "SEM" : "from scipy.stats import sem",
        #              "Mean 95% CI" : None,
        #              "Geom.Mean 95% CI" : None
        #           }
        #
        # fn_name = {"Mean" : "mean",
        #            "Median" : "median",
        #            "Geom.Mean" : "geom_mean",
        #            "Count" : "len",
        #            "Std.Dev" : "std",
        #            "Geom.SD" : "geom_sd_range",
        #            "SEM" : "sem",
        #            "Geom.SEM" : "geom_sem_range",
        #            "Mean 95% CI" : "lambda x: ci(x, mean, boots = 100)",
        #            "Geom.Mean 95% CI" : "lambda x: ci(x, geom_mean, boots = 100)"
        #            }
        
        # op.function = summary_functions[self.function_name]
        
        # try:
        #     # this doesn't work for builtins like "len"
        #     op.function.__name__ = fn_name[self.statistic_name]
        # except AttributeError:
        #     pass
        
        # return "\n{import_statement}\nop_{idx} = {repr}\n\nex_{idx} = op_{idx}.apply(ex_{prev_idx})"\
        #     .format(import_statement = (fn_import[self.function_name]
        #                                 if fn_import[self.function_name] is not None
        #                                 else ""),
        #             repr = repr(op),
        #             idx = idx,
        #             prev_idx = idx - 1)
            

### Serialization

@camel_registry.dumper(Function, 'multi-channel-stat-function', version = 1)
def _dump_function(channel):
    return dict(channel = channel.channel,
                function = channel.function,
                feature = channel.feature)
    
@camel_registry.loader('multi-channel-stat-function', version = 1)
def _load_channel(data, version):
    return Function(**data)

@camel_registry.dumper(MultiChannelStatisticWorkflowOp, 'multi-channel-statistic', version = 1)
def _dump(op):
    return dict(name = op.name,
                functions_list = op.functions_list,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('multi-channel-statistic', version = 1)
def _load(data, version):
    return MultiChannelStatisticWorkflowOp(**data)
    
#
# @camel_registry.dumper(ChannelStatisticWorkflowOp, 'channel-statistic', version = 1)
# def _dump_v1(op):
#     return dict(name = op.name,
#                 channel = op.channel,
#                 statistic_name = op.statistic_name,
#                 by = op.by,
#                 subset_list = op.subset_list)
#

#
# @camel_registry.loader('channel-statistic', version = 1)
# def _load_v1(data, version):
#     del data["statistic_name"]
#     del data["fill"]
#     # TODO - some warning about how statistics have changed and you'll need to reset the parameters of any
#     # function that uses a statistic or view that plots one
#     return ChannelStatisticWorkflowOp(**data)

