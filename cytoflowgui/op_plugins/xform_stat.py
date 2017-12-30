#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
Transform statistic
-------------------

Apply a function to a statistic, and add it as a statistic
to the experiment.

First, the module groups the data by the unique values of the variables
in **By**, then applies **Function** to the statistic in each group.

.. note:: 

    Statistics are a central part of *Cytoflow*.  More documentation is
    forthcoming.

.. object:: Name

    The operation name.  Becomes the first part of the new statistic's name.
    
.. object:: Statistic

    The statistic to apply the function to.
    
.. object:: Function

    The function to compute on each group.
        
.. object:: Subset

    Only apply the function to a subset of the input statistic.  Useful if the 
    function is very slow.

'''

import numpy as np
import pandas as pd
import scipy.stats

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, \
                         CheckListEditor, TextEditor
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, List, Property, on_trait_change,
                        Str)
from pyface.api import ImageResource

from cytoflow.operations.xform_stat import TransformStatisticOp
import cytoflow.utility as util

from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import SubsetListEditor, ISubset
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.workflow import Changed
from cytoflowgui.serialization import camel_registry, traits_repr, dedent

TransformStatisticOp.__repr__ = traits_repr

mean_95ci = lambda x: util.ci(x, np.mean, boots = 100)
geomean_95ci = lambda x: util.ci(x, util.geom_mean, boots = 100)

transform_functions = {"Mean" : np.mean,
                       "Geom.Mean" : util.geom_mean,
                       "Count" : len,
                       "Std.Dev" : np.std,
                       "Geom.SD" : util.geom_sd_range,
                       "SEM" : scipy.stats.sem,
                       "Geom.SEM" : util.geom_sem_range,
                       "Mean 95% CI" : mean_95ci,
                       "Geom.Mean 95% CI" : geomean_95ci,
                       "Sum" : np.sum,
                       "Proportion" : lambda a: pd.Series(a / a.sum()),
                       "Percentage" : lambda a: pd.Series(a / a.sum()) * 100.0,
                       "Fold" : lambda a: pd.Series(a / a.min())
                       }


class TransformStatisticHandler(OpHandlerMixin, Controller):
    
#     prev_statistics = Property(depends_on = "info.ui.context")
    indices = Property(depends_on = "context.previous_wi.statistics, "
                                    "model.statistic, "
                                    "model.subset")
    levels = Property(depends_on = "context.previous_wi.statistics, model.statistic")    

    # MAGIC: gets the value for the property indices
    def _get_indices(self):        
        if not (self.context 
                and self.context.previous_wi 
                and self.context.previous_wi.statistics 
                and self.model 
                and self.model.statistic 
                and self.model.statistic in self.context.previous_wi.statistics):
            return []
        
        stat = self.context.previous_wi.statistics[self.model.statistic]
        data = pd.DataFrame(index = stat.index)
        
        if self.model.subset:
            data = data.query(self.model.subset)
            
        if len(data) == 0:
            return []       
        
        names = list(data.index.names)
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                data.index = data.index.droplevel(name)
        
        return list(data.index.names)
    
    # MAGIC: gets the value for the property 'levels'
    # returns a Dict(Str, pd.Series)
    
    def _get_levels(self):
        
        if not (self.context 
                and self.context.previous_wi 
                and self.context.previous_wi.statistics 
                and self.model 
                and self.model.statistic
                and self.model.statistic in self.context.previous_wi.statistics):
            return []
        
        stat = self.context.previous_wi.statistics[self.model.statistic]
        index = stat.index
        
        names = list(index.names)
        for name in names:
            unique_values = index.get_level_values(name).unique()
            if len(unique_values) == 1:
                index = index.droplevel(name)

        names = list(index.names)
        ret = {}
        for name in names:
            ret[name] = pd.Series(np.unique(index.get_level_values(name)))
            
        return ret
    
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('statistic',
                         editor=EnumEditor(name='handler.previous_statistics_names'),
                         label = "Statistic"),
                    Item('statistic_name',
                         editor = EnumEditor(values = list(transform_functions.keys())),
                         label = "Function"),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'handler.indices'),
                         
                         label = 'Group\nBy',
                         style = 'custom'),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "handler.levels")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    shared_op_traits)

class TransformStatisticPluginOp(PluginOpMixin, TransformStatisticOp):
    handler_factory = Callable(TransformStatisticHandler)

    # functions aren't picklable, so send the name instead
    function = Callable(transient = True)
    
    # bits to support the subset editor
    
    subset_list = List(ISubset)    
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change('subset_list.str', post_init = True)
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.OPERATION, ('subset_list', self.subset_list))
    
    
    def apply(self, experiment):
        if not self.statistic_name:
            raise util.CytoflowOpError("Transform function not set")
        
        self.function = transform_functions[self.statistic_name]
        
        return TransformStatisticOp.apply(self, experiment)


    def get_notebook_code(self, wi, idx):
        op = TransformStatisticOp()
        op.copy_traits(self, op.copyable_trait_names())
        
        fn_import = {"Mean" : "from numpy import mean",
                     "Geom.Mean" : None,
                     "Count" : None,
                     "Std.Dev" : "from numpy import std",
                     "Geom.SD" : None,
                     "SEM" : "from scipy.stats import sem",
                     "Geom.SEM" : None,
                     "Mean 95% CI" : "from numpy import mean\nmean_ci = lambda x: ci(x, mean, boots = 100)",
                     "Geom.Mean 95% CI" : "geom_mean_ci = lambda x: ci(x, geom_mean, boots = 100)",
                     "Sum" : "from numpy import sum",
                     "Proportion" : "proportion = lambda a: pd.Series(a / a.sum())",
                     "Percentage" : "percentage = lambda a: pd.Series(a / a.sum()) * 100.0",
                     "Fold" : "fold = lambda a: pd.Series(a / a.min())"
                  }
        
        fn_name = {"Mean" : "mean",
                   "Geom.Mean" : "geom_mean",
                   "Count" : "len",
                   "Std.Dev" : "std",
                   "Geom.SD" : "geom_sd_range",
                   "SEM" : "sem",
                   "Geom.SEM" : "geom_sem_range",
                   "Mean 95% CI" : "mean_ci",
                   "Geom.Mean 95% CI" : "geom_mean_ci",
                   "Sum" : "sum",
                   "Proportion" : "proportion",
                   "Percentage" : "percentage",
                   "Fold" : "fold"
                   }
        
        op.function = transform_functions[self.statistic_name]
        op.function.__name__ = fn_name[self.statistic_name]
        
        return dedent("""
        {import_statement}
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(import_statement = (fn_import[self.statistic_name] + "\n" 
                                    if fn_import[self.statistic_name] is not None
                                    else ""),
                repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        pass


@provides(IOperationPlugin)
class TransformStatisticPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.transform_statistic'
    operation_id = 'edu.mit.synbio.cytoflow.operations.transform_statistic'

    short_name = "Transform Statistic"
    menu_group = "Gates"
    
    def get_operation(self):
        return TransformStatisticPluginOp()
    
    def get_icon(self):
        return ImageResource('xform_stat')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
### Serialization
@camel_registry.dumper(TransformStatisticPluginOp, 'transform-statistic', version = 1)
def _dump(op):
    return dict(name = op.name,
                statistic = op.statistic,
                statistic_name = op.statistic_name,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('transform-statistic', version = 1)
def _load(data, version):
    return TransformStatisticPluginOp(**data)