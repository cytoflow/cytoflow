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

from traits.api import provides, Callable
from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.operations.i_operation import IOperation
from cytoflow.operations.range import RangeOp, RangeSelection

from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin, shared_view_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.clearable_enum_editor import ClearableEnumEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

class RangeHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('name'),
                    Item('channel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Channel"),
                    Item('low'),
                    Item('high'),
                    shared_op_traits) 
        
class RangeViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         style = "readonly"),
                    Item('channel', 
                         label = "Channel",
                         style = "readonly"),
                    Item('scale'),
                    Item('huefacet',
                         editor=ClearableEnumEditor(name='context.previous.conditions_names'),
                         label="Color\nFacet"),
                    Item('_'),
                    Item('subset',
                         label = "Subset",
                         editor = SubsetEditor(experiment = 'context.previous.result')),
                    shared_view_traits)

@provides(ISelectionView)
class RangeSelectionView(RangeSelection, PluginViewMixin):
    handler_factory = Callable(RangeViewHandler)
    
@provides(IOperation)
class RangePluginOp(RangeOp, PluginOpMixin):
    handler_factory = Callable(RangeHandler)

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
    
    def get_default_view(self):
        return RangeSelectionView()
    
    def get_icon(self):
        return ImageResource('range')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    