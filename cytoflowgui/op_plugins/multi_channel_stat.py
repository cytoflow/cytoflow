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
Multi-channel statistic
-----------------

Apply a function to subsets of a data set, and add it as a statistic
to the experiment.

First, the module groups the data by the unique values of the variables
in **By**, then applies **Function** to the **Channel** in each group.
Multiple channels and functions can be specified
    
.. object:: Name

    The operation name.  Becomes the new statistic's name.
    
.. object:: Channel

    The channel to apply the function to.
    
.. object:: Function

    The function to compute on each group.
        
.. object:: Subset

    Only apply the function to a subset of the data.  Useful if the function 
    is very slow.

"""

from natsort import natsorted

from traits.api import provides, List, Event, Property, Str
from traitsui.api import (View, Item, TextEditor, VGroup, EnumEditor, CheckListEditor, 
                          Controller, ButtonEditor)
from pyface.api import ImageResource  # @UnresolvedImport
from envisage.api import Plugin

from ..workflow.operations import MultiChannelStatisticWorkflowOp, MultiChannelStatisticFunction
from ..workflow.operations.multi_channel_stat import summary_functions
from ..editors import SubsetListEditor, InstanceHandlerEditor, VerticalListEditor
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT 
from .op_plugin_base import OpHandler, PluginHelpMixin, shared_op_traits_view

class FunctionHandler(Controller):
    function_view = View(VGroup(Item('channel',
                                     editor = EnumEditor(name = 'context_handler.channels')),
                                Item('function',
                                     editor = EnumEditor(values = sorted(summary_functions.keys()))),
                                Item('feature')))


class MultiChannelStatisticHandler(OpHandler):
    add_function = Event
    remove_function = Event
        
    channels = Property(List(Str), observe = 'context.channels')
    
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             VGroup(
                Item('functions_list',
                     editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'function_view',
                                                                                handler_factory = FunctionHandler),
                                                 style = 'custom',
                                                 mutable = False)),
                Item('handler.add_function',
                     editor = ButtonEditor(value = True,
                                           label = "Add a function")),
                Item('handler.remove_function',
                     editor = ButtonEditor(value = True,
                                           label = "Remove a function")),
                label = "Channels",
                show_labels = False),
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
        
    # MAGIC: called when add_function is set
    def _add_function_fired(self):
        self.model.functions_list.append(MultiChannelStatisticFunction())
        
    # MAGIC: called when remove_function is set
    def _remove_function_fired(self):
        if self.model.functions_list:
            self.model.functions_list.pop()

    # MAGIC: returns the value of the 'channels' property
    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return [] 


@provides(IOperationPlugin)
class MultiChannelStatisticPlugin(Plugin, PluginHelpMixin):
    
    id = 'cytoflowgui.op_plugins.multi_channel_statistic'
    operation_id = 'cytoflowgui.workflow.operations.multi_channel_stat'
    view_id = None

    name = "Multi Channel Statistic"
    menu_group = "Statistics"
    
    def get_operation(self):
        return MultiChannelStatisticWorkflowOp()
    
    def get_handler(self, model, context):
        return MultiChannelStatisticHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('multi_channel_stat')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]

