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

'''
Transform statistic
-------------------

Apply a function to groups of a statistic, and add the result as a statistic
to the experiment.

First, the module groups the data by the unique values of the variables
in **By**, then applies **Function** to the values in each group. This is
repeated for each feature (column) in the statistic.

.. object:: Name

    The operation name.  Becomes the new statistic's name.
    
.. object:: Statistic

    The statistic to apply the function to.
    
.. object:: Function

    The function to compute on each group.
        
.. object:: Subset

    Only apply the function to a subset of the input statistic. 

'''

import numpy as np
import pandas as pd

from traits.api import provides, Property, List
from traitsui.api import (View, Item, TextEditor, VGroup, EnumEditor, CheckListEditor)
from pyface.api import ImageResource  # @UnresolvedImport
from envisage.api import Plugin
                       
from ..workflow.operations import TransformStatisticWorkflowOp
from ..workflow.operations.xform_stat import transform_functions
from ..editors import SubsetListEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT 
from .op_plugin_base import OpHandler, PluginHelpMixin, shared_op_traits_view


class TransformStatisticHandler(OpHandler):
    
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
            return {}
        
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
    
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('statistic',
                  editor=EnumEditor(name='context_handler.previous_statistics_names'),
                  label = "Statistic"),
             Item('function_name',
                  editor = EnumEditor(values = sorted(transform_functions.keys())),
                  label = "Function"),
             Item('by',
                  editor = CheckListEditor(cols = 2,
                                           name = 'handler.indices'),
                  
                  label = 'Group\nBy',
                  style = 'custom'),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "handler.levels", 
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory))),
                    label = "Subset",
                    show_border = False,
                    show_labels = False),
             shared_op_traits_view)



@provides(IOperationPlugin)
class TransformStatisticPlugin(Plugin, PluginHelpMixin):
    
    id = 'cytoflowgui.op_plugins.transform_statistic'
    operation_id = 'cytoflow.operations.transform_statistic'
    view_id = None

    name = "Transform Statistic"
    short_name = "Xform\nStatistic"
    menu_group = "Statistics"
    
    def get_operation(self):
        return TransformStatisticWorkflowOp()
    
    def get_handler(self, model, context):
        return TransformStatisticHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('xform_stat')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
