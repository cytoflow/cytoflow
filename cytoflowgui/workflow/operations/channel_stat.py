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

from traits.api import (Str, Callable, Property, Any, List, provides, observe)

import cytoflow.utility as util
from cytoflow import ChannelStatisticOp
                       
from cytoflowgui.workflow.serialization import camel_registry, traits_repr
from .operation_base import IWorkflowOperation, WorkflowOperation

from ..subset import ISubset

mean_95ci = lambda x: util.ci(x, np.mean, boots = 100)
geomean_95ci = lambda x: util.ci(x, util.geom_mean, boots = 100)

summary_functions = {"Mean" : np.mean,
                     "Mean +- SD" : lambda x: pd.Series({"Mean" : x.mean(),
                                                         "+SD" : x.mean() + x.std(),
                                                         "-SD" : x.mean() - x.std()}),
                     "Geo.Mean" : util.geom_mean,
                     "Geo.Mean */ SD" : lambda x: pd.Series({"Geo.Mean" : util.geom_mean(x),
                                                             "*SD" : util.geom_mean(x) * util.geom_sd(x),
                                                             "/SD" : util.geom_mean(x) / util.geom_sd(x)}),
                     "Median" : np.median,
                     "Count" : len,
                     "Std.Dev" : np.std,
                     "Geo.SD" : util.geom_sd,
                     "SEM" : scipy.stats.sem,
                     "Geo.SEM" : util.geom_sem,
                     "Mean +- SEM" : lambda x: pd.Series({"Mean" : x.mean(),
                                                          "+SEM" : x.mean + scipy.stats.sem(x),
                                                          "-SEM" : x.mean - scipy.stats.sem(x)}),
                     "Geo.Mean */ SEM" : lambda x: pd.Series({"Geo.Mean" : util.geom_mean(x),
                                                              "*SEM" : util.geom_mean(x) * util.geom_sem(x),
                                                              "/SEM" : util.geom_mean(x) / util.geom_sem(x)}),
                     "Mean +- 95% CI" : lambda x: pd.Series({"Mean" : x.mean(),
                                                             "+CI" : x.mean + util.ci(x, np.mean, boots = 100),
                                                             "-CI" : x.mean - util.ci(x, np.mean, boots = 100)}),
                     "Geo.Mean */ 95% CI" : lambda x: pd.Series({"Geo.Mean" : util.geom_mean(x),
                                                             "+CI" : util.geom_mean(x) * util.ci(x, util.geom_mean, boots = 100),
                                                             "-CI" : util.geom_mean(x) / util.ci(x, util.geom_mean, boots = 100)}),
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

ChannelStatisticOp.__repr__ = traits_repr

@provides(IWorkflowOperation)
class ChannelStatisticWorkflowOp(WorkflowOperation, ChannelStatisticOp):
    # operation traits
    name = Str(apply = True)
    channel = Str(apply = True)
    function_name = Str(apply = True)
    by = List(Str, apply = True)
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, apply = True)
    
    # functions aren't picklable, so make this one transient 
    # and send the name instead
    function = Callable(transient = True)
    
    # automatically pick a good fill
    # fill = Property(Any, observe = 'function_name', transient = True)
    fill = 0
    
    # MAGIC - returns the value of the 'fill' property
    # def _get_fill(self):
    #     if self.function_name:
    #         return fill[self.function_name]
    #     else:
    #         return 0
    
    # bits to support the subset editor
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
            
    def apply(self, experiment):
        if not self.function_name:
            raise util.CytoflowOpError("Summary function isn't set")
        
        self.function = summary_functions[self.function_name]
        
        return ChannelStatisticOp.apply(self, experiment) 
    
    def clear_estimate(self):
        # no-op
        return
    
    def get_notebook_code(self, idx):
        op = ChannelStatisticOp()
        op.copy_traits(self, op.copyable_trait_names())
        
        fn_import = {"Mean" : "from numpy import mean",
                     "Mean +- SD" : None,
                     "Geo.Mean" : None,
                     "Geo.Mean */ SD" : None,
                     "Median" : "from numpy import median",
                     "Count" : None,
                     "Std.Dev" : "from numpy import std",
                     "Geo.SD" : None,
                     "SEM" : "from scipy.stats import sem",
                     "Mean +- SEM" : "from scipy.stats import sem",
                     "Geo.Mean */ SEM" : None,
                     "Mean 95% CI" : None,
                     "Geom.Mean 95% CI" : None
                  }
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
        
        op.function = summary_functions[self.function_name]
        
        # try:
        #     # this doesn't work for builtins like "len"
        #     op.function.__name__ = fn_name[self.statistic_name]
        # except AttributeError:
        #     pass
        
        return "\n{import_statement}\nop_{idx} = {repr}\n\nex_{idx} = op_{idx}.apply(ex_{prev_idx})"\
            .format(import_statement = (fn_import[self.function_name]
                                        if fn_import[self.function_name] is not None
                                        else ""),
                    repr = repr(op),
                    idx = idx,
                    prev_idx = idx - 1)
            
    
### Serialization
@camel_registry.dumper(ChannelStatisticWorkflowOp, 'channel-statistic', version = 2)
def _dump(op):
    return dict(name = op.name,
                channel = op.channel,
                function_name = op.function_name,
                by = op.by,
                subset_list = op.subset_list)

@camel_registry.dumper(ChannelStatisticWorkflowOp, 'channel-statistic', version = 1)
def _dump_v1(op):
    return dict(name = op.name,
                channel = op.channel,
                statistic_name = op.statistic_name,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('channel-statistic', version = 2)
def _load(data, version):
    return ChannelStatisticWorkflowOp(**data)
    
@camel_registry.loader('channel-statistic', version = 1)
def _load_v1(data, version):
    del data["statistic_name"]
    del data["fill"]
    # TODO - some warning about how statistics have changed and you'll need to reset the parameters of any
    # function that uses a statistic or view that plots one
    return ChannelStatisticWorkflowOp(**data)

