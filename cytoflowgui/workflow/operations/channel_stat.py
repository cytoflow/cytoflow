#!/usr/bin/env python3.8

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


"""
Channel statistic
-----------------

Apply a function to subsets of a data set, and add it as a statistic
to the experiment.

First, the module groups the data by the unique values of the variables
in **By**, then applies **Function** to the **Channel** in each group.
    

.. object:: Name

    The operation name.  Becomes the first part of the new statistic's name.
    
.. object:: Channel

    The channel to apply the function to.
    
.. object:: Function

    The function to compute on each group.
        
.. object:: Subset

    Only apply the function to a subset of the data.  Useful if the function 
    is very slow.

"""

import numpy as np
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
                     "Geom.Mean" : util.geom_mean,
                     "Median" : np.median,
                     "Count" : len,
                     "Std.Dev" : np.std,
                     "Geom.SD" : util.geom_sd_range,
                     "SEM" : scipy.stats.sem,
                     "Geom.SEM" : util.geom_sem_range,
                     "Mean 95% CI" : mean_95ci,
                     "Geom.Mean 95% CI" : geomean_95ci
                     }

fill = {"Mean" : 0,
        "Geom.Mean" : 0,
        "Median" : 0,
        "Count" : 0,
        "Std.Dev" : 0,
        "Geom.SD" : (0,0),
        "SEM" : 0,
        "Geom.SEM" : (0,0),
        "Mean 95% CI" : 0,
        "Geom.Mean 95% CI" : 0
        }

ChannelStatisticOp.__repr__ = traits_repr

@provides(IWorkflowOperation)
class ChannelStatisticWorkflowOp(WorkflowOperation, ChannelStatisticOp):
    # operation traits
    name = Str(apply = True)
    channel = Str(apply = True)
    statistic_name = Str(apply = True)
    by = List(Str, apply = True)
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset)
    
    # functions aren't picklable, so make this one transient 
    # and send the name instead
    function = Callable(transient = True)
    
    # automatically pick a good fill
    fill = Property(Any, observe = 'statistic_name', transient = True)
    
    # MAGIC - returns the value of the 'fill' property
    def _get_fill(self):
        if self.statistic_name:
            return fill[self.statistic_name]
        else:
            return 0
    
    # bits to support the subset editor
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
            
    def apply(self, experiment):
        if not self.statistic_name:
            raise util.CytoflowOpError("Summary function isn't set")
        
        self.function = summary_functions[self.statistic_name]
        
        return ChannelStatisticOp.apply(self, experiment) 
    
    def clear_estimate(self):
        # no-op
        return
    
    def get_notebook_code(self, idx):
        op = ChannelStatisticOp()
        op.copy_traits(self, op.copyable_trait_names())
        
        fn_import = {"Mean" : "from numpy import mean",
                     "Median" : "from numpy import median",
                     "Geom.Mean" : None,
                     "Count" : None,
                     "Std.Dev" : "from numpy import std",
                     "Geom.SD" : None,
                     "SEM" : "from scipy.stats import sem",
                     "Geom.SEM" : None,
                     "Mean 95% CI" : "from numpy import mean",
                     "Geom.Mean 95% CI" : None
                  }
        
        fn_name = {"Mean" : "mean",
                   "Median" : "median",
                   "Geom.Mean" : "geom_mean",
                   "Count" : "len",
                   "Std.Dev" : "std",
                   "Geom.SD" : "geom_sd_range",
                   "SEM" : "sem",
                   "Geom.SEM" : "geom_sem_range",
                   "Mean 95% CI" : "lambda x: ci(x, mean, boots = 100)",
                   "Geom.Mean 95% CI" : "lambda x: ci(x, geom_mean, boots = 100)"
                   }
        
        op.function = summary_functions[self.statistic_name]
        
        try:
            # this doesn't work for builtins like "len"
            op.function.__name__ = fn_name[self.statistic_name]
        except AttributeError:
            pass
        
        return "\n{import_statement}\nop_{idx} = {repr}\n\nex_{idx} = op_{idx}.apply(ex_{prev_idx})"\
            .format(import_statement = (fn_import[self.statistic_name]
                                        if fn_import[self.statistic_name] is not None
                                        else ""),
                    repr = repr(op),
                    idx = idx,
                    prev_idx = idx - 1)
            
    
### Serialization
@camel_registry.dumper(ChannelStatisticWorkflowOp, 'channel-statistic', version = 1)
def _dump(op):
    return dict(name = op.name,
                channel = op.channel,
                statistic_name = op.statistic_name,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('channel-statistic', version = 1)
def _load(data, version):
    return ChannelStatisticWorkflowOp(**data)

