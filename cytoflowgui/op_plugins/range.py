#!/usr/bin/env python2.7
# coding: latin-1

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

from traits.api import provides, Callable, Str, Instance, DelegatesTo
from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.operations import IOperation
from cytoflow.operations.range import RangeOp, RangeSelection

from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.workflow import Changed

class RangeHandler(OpHandlerMixin, Controller):
    
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('channel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Channel"),
                    Item('low',
                         editor = TextEditor(auto_set = False)),
                    Item('high',
                         editor = TextEditor(auto_set = False)),
                    shared_op_traits) 
        
class RangeViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('channel', 
                                label = "Channel",
                                style = "readonly"),
                           Item('scale'),
                           Item('huefacet',
                                editor=ExtendableEnumEditor(name='handler.previous_conditions_names',
                                                            extra_items = {"None" : ""}),
                                label="Color\nFacet"),
                            label = "Range Setup View",
                            show_border = False),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous.conditions")),
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

@provides(ISelectionView)
class RangeSelectionView(PluginViewMixin, RangeSelection):
    handler_factory = Callable(RangeViewHandler)
    op = Instance(IOperation, fixed = True)
    low = DelegatesTo('op', status = True)
    high = DelegatesTo('op', status = True)
    name = Str
    
    def should_plot(self, changed):
        if changed == Changed.PREV_RESULT or changed == Changed.VIEW:
            return True
        else:
            return False
    
    def plot_wi(self, wi):
        self.plot(wi.previous.result)
    
    
@provides(IOperation)
class RangePluginOp(PluginOpMixin, RangeOp):
    handler_factory = Callable(RangeHandler)
    
    def default_view(self, **kwargs):
        return RangeSelectionView(op = self, **kwargs)

@provides(IOperationPlugin)
class RangePlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.range'
    operation_id = 'edu.mit.synbio.cytoflow.operations.range'

    short_name = "Range"
    menu_group = "Gates"
    
    def get_operation(self):
        return RangePluginOp()
    
    def get_icon(self):
        return ImageResource('range')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    