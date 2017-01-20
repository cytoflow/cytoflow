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

from traits.api import provides, Callable, Instance, Str, DelegatesTo
from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.operations import IOperation
from cytoflow.operations.threshold import ThresholdOp, ThresholdSelection

from cytoflowgui.op_plugins.i_op_plugin \
    import IOperationPlugin, OpHandlerMixin, PluginOpMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor

class ThresholdHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('channel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Channel"),
                    Item('threshold',
                         editor = TextEditor(auto_set = False)),
                    shared_op_traits) 
        
class ThresholdViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name',
                                style = "readonly"),
                           Item('channel', 
                                label = "Channel",
                                style = "readonly"),
                           Item('threshold', 
                                label = "Threshold",
                                style = "readonly"),
                           Item('scale'),
                           Item('huefacet',
                                editor=ExtendableEnumEditor(name='context.previous.conditions_names',
                                                            extra_items = {"None" : ""}),
                                label="Color\nFacet"),
                           label = "Threshold Setup View",
                           show_border = False),
                    VGroup(Item('subset_dict',
                                show_label = False,
                                editor = SubsetEditor(conditions = "context.previous.conditions")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('context.view_warning',
                         resizable = True,
                         visible_when = 'context.view_warning',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                 background_color = "#ffff99")),
                    Item('context.view_error',
                         resizable = True,
                         visible_when = 'context.view_error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191"))))

class ThresholdSelectionView(PluginViewMixin, ThresholdSelection):
    handler_factory = Callable(ThresholdViewHandler, transient = True)    
    op = Instance(IOperation, fixed = True)
    threshold = DelegatesTo('op', status = True)
    name = Str
    
    def should_plot(self, changed):
        if changed == "prev_result" or changed == "view":
            return True
        else:
            return False
        
    def plot_wi(self, wi):        
        self.plot(wi.previous.result)
    
class ThresholdPluginOp(ThresholdOp, PluginOpMixin):
    handler_factory = Callable(ThresholdHandler, transient = True)
     
    def default_view(self, **kwargs):
        return ThresholdSelectionView(op = self, **kwargs)

@provides(IOperationPlugin)
class ThresholdPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.threshold'
    operation_id = 'edu.mit.synbio.cytoflow.operations.threshold'

    short_name = "Threshold"
    menu_group = "Gates"
    
    def get_operation(self):
        return ThresholdPluginOp()

    def get_icon(self):
        return ImageResource('threshold')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    