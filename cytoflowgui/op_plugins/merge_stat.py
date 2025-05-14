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
Merge two statistics
--------------------

Create a new statistic out of the features of two existing statistics. The 
indices of the two statistics (the levels and codes of the index) must be
identical, and they cannot share any feature names.

.. object:: Name

    The operation name.  Becomes the new statistic's name.
    
.. object:: Statistic #1

    The first statistic to merge.
    
.. object:: Statistic #2

    The second statistic to merge.

'''

import numpy as np
import pandas as pd

from traits.api import provides, List
from traitsui.api import (View, Item, TextEditor, EnumEditor)
from pyface.api import ImageResource  # @UnresolvedImport
from envisage.api import Plugin
                       
from ..workflow.operations import MergeStatisticsWorkflowOp

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT 
from .op_plugin_base import OpHandler, PluginHelpMixin, shared_op_traits_view


class MergeStatisticsHandler(OpHandler):
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('statistic_1',
                  editor=EnumEditor(name='context_handler.previous_statistics_names'),
                  label = "Statistic 1"),
             Item('statistic_2',
                  editor=EnumEditor(name='context_handler.previous_statistics_names'),
                  label = "Statistic 2"),
             shared_op_traits_view)



@provides(IOperationPlugin)
class MergeStatisticsPlugin(Plugin, PluginHelpMixin):
    
    id = 'cytoflowgui.op_plugins.merge_statistics'
    operation_id = 'cytoflowgui.workflow.operations.merge_statistics'
    view_id = None

    name = "Merge Statistics"
    menu_group = "Statistics"
    
    def get_operation(self):
        return MergeStatisticsWorkflowOp()
    
    def get_handler(self, model, context):
        return MergeStatisticsHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('merge_stat')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
