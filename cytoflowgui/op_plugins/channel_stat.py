#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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
Created on Oct 9, 2015

@author: brian
'''

from sklearn import mixture

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor, \
                         CheckListEditor, ButtonEditor, TextEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Instance, Str, List, Dict, Any, DelegatesTo, on_trait_change
from pyface.api import ImageResource

from cytoflow.operations import IOperation
from cytoflow.operations.channel_stat import ChannelStatisticOp
from cytoflow.views.i_selectionview import IView
import cytoflow.utility as util

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.util import summary_functions, error_functions


class ChannelStatisticHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('channel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Channel"),
                    Item('function_name',
                                editor = EnumEditor(values = summary_functions.keys()),
                                label = "Function"),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context.previous.conditions'),
                         label = 'Group\nBy',
                         style = 'custom'),
                    VGroup(Item('subset_dict',
                                show_label = False,
                                editor = SubsetEditor(conditions = "context.previous.conditions")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    shared_op_traits)

class ChannelStatisticPluginOp(PluginOpMixin, ChannelStatisticOp):
    handler_factory = Callable(ChannelStatisticHandler)
    subset_dict = Dict(Str, List)
    
    # functions aren't picklable, so send the name instead
    function_name = Str()
    function = Callable(transient = True)

@provides(IOperationPlugin)
class ChannelStatisticPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.channel_statistic'
    operation_id = 'edu.mit.synbio.cytoflow.operations.channel_statistic'

    short_name = "Channel Statistic"
    menu_group = "Gates"
    
    def get_operation(self):
        return ChannelStatisticPluginOp()
    
    def get_icon(self):
        return ImageResource('channel_stat')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    