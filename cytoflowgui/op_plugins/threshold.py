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

from cytoflow.operations.threshold import ThresholdOp, ThresholdSelection

from cytoflowgui.op_plugins.i_op_plugin \
    import IOperationPlugin, OpHandlerMixin, PluginOpMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin, shared_view_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.clearable_enum_editor import ClearableEnumEditor

class ThresholdHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('name'),
                    Item('channel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Channel"),
                    Item('threshold'),
                    shared_op_traits) 
        
class ThresholdViewHandler(Controller, ViewHandlerMixin):
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
                    Item('object.subset',
                         label = "Subset",
                         editor = SubsetEditor(experiment = 'context.previous.result')),
                    shared_view_traits)

class ThresholdSelectionView(ThresholdSelection, PluginViewMixin):
    handler_factory = Callable(ThresholdViewHandler)
    
class ThresholdPluginOp(ThresholdOp, PluginOpMixin):
    handler_factory = Callable(ThresholdHandler)

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
    
    def get_default_view(self):
        return ThresholdSelectionView()

    def get_icon(self):
        return ImageResource('threshold')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    