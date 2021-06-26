#!/usr/bin/env python3.8
# coding: latin-1

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

from traits.api import provides
from traitsui.api import (View, Item, TextEditor, VGroup, EnumEditor, CheckListEditor)
from pyface.api import ImageResource
from envisage.api import Plugin, contributes_to
                       
from ..workflow.operations import ChannelStatisticWorkflowOp
from ..workflow.operations.channel_stat import summary_functions
from ..editors import SubsetListEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT 
from .op_plugin_base import OpHandler, PluginHelpMixin, shared_op_traits_view


class ChannelStatisticHandler(OpHandler):
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('channel',
                  editor= EnumEditor(name='context_handler.previous_channels'),
                  label = "Channel"),
             Item('statistic_name',
                         editor = EnumEditor(values = sorted(summary_functions.keys())),
                         label = "Function"),
             Item('by',
                  editor = CheckListEditor(cols = 2,
                                           name = 'context_handler.previous_conditions_names'),
                  label = 'Group\nBy',
                  style = 'custom'),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "context_handler.previous_conditions",
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory))),
                    label = "Subset",
                    show_border = False,
                    show_labels = False),
             shared_op_traits_view)


@provides(IOperationPlugin)
class ChannelStatisticPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.channel_statistic'
    operation_id = 'edu.mit.synbio.cytoflow.operations.channel_statistic'
    view_id = None

    short_name = "Channel Statistic"
    menu_group = "Gates"
    
    def get_operation(self):
        return ChannelStatisticWorkflowOp()
    
    def get_handler(self, model, context):
        return ChannelStatisticHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('channel_stat')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
