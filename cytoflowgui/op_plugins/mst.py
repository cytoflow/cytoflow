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



from traits.api import provides, List
from traitsui.api import View, Item, TextEditor
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..view_plugins.mst import MSTHandler as MSTViewHandler
from ..workflow.operations import MSTWorkflowOp, MSTWorkflowSelectionView

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class MSTOpHandler(OpHandler):
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             shared_op_traits_view) 
        
#
# class MSTViewHandler(ViewHandler):
#     view_traits_view = \
#         View(VGroup(
#              VGroup(Item('channel', 
#                          label = "Channel",
#                          style = "readonly"),
#                     Item('threshold', 
#                          label = "Threshold",
#                          style = "readonly"),
#                     Item('scale'),
#                     Item('huefacet',
#                          editor=ExtendableEnumEditor(name='context_handler.previous_conditions_names',
#                                                      extra_items = {"None" : ""}),
#                          label="Color\nFacet"),
#                     label = "Threshold Setup View",
#                     show_border = False),
#              VGroup(Item('subset_list',
#                          show_label = False,
#                          editor = SubsetListEditor(conditions = "context_handler.previous_conditions",
#                                                    editor = InstanceHandlerEditor(view = 'subset_view',
#                                                                                   handler_factory = subset_handler_factory),
#                                                    mutable = False)),
#                     label = "Subset",
#                     show_border = False,
#                     show_labels = False),
#              Item('context.view_warning',
#                   resizable = True,
#                   visible_when = 'context.view_warning',
#                   editor = ColorTextEditor(foreground_color = "#000000",
#                                           background_color = "#ffff99")),
#              Item('context.view_error',
#                   resizable = True,
#                   visible_when = 'context.view_error',
#                   editor = ColorTextEditor(foreground_color = "#000000",
#                                            background_color = "#ff9191"))))
#
#     view_params_view = \
#         View(Item('plot_params',
#                   editor = InstanceHandlerEditor(view = 'view_params_view',
#                                                  handler_factory = MSTParamsHandler),
#                   style = 'custom',
#                   show_label = False))


@provides(IOperationPlugin)
class MSTPlugin(Plugin, PluginHelpMixin):
    id = 'cytoflowgui.op_plugins.mst'
    operation_id = 'cytoflow.operation.mst'
    view_id = 'cytoflow.view.mst_selection'

    name = "MST"
    menu_group = "Gates"
    
    def get_operation(self):
        return MSTWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, MSTWorkflowOp):
            return MSTOpHandler(model = model, context = context)
        elif isinstance(model, MSTWorkflowSelectionView):
            return MSTViewHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('mst')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]

