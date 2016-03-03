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
Created on Apr 25, 2015

@author: brian
'''

from traits.api import provides, Callable
from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.operations.polygon import PolygonOp, PolygonSelection

from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin, shared_view_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

class PolygonHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.xchannel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "X Channel"),
                    Item('object.ychannel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Y Channel"),
                    shared_op_traits) 
        
class PolygonViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('object.name', 
                         style = 'readonly'),
                    Item('object.xchannel', 
                         label = "X Channel", 
                         style = 'readonly'),
                    Item('object.xscale',
                         label = "X Scale"),
                    Item('object.ychannel',
                         label = "Y Channel",
                         style = 'readonly'),
                    Item('object.yscale',
                         label = "Y Scale"),
                    Item('object.huefacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label="Color\nFacet"),
                    Item('_'),
                    Item('object.subset',
                         label = "Subset",
                         editor = SubsetEditor(experiment = 'handler.wi.previous.result')),
                    shared_view_traits)

@provides(ISelectionView)
class PolygonSelectionView(PolygonSelection, PluginViewMixin):
    handler_factory = Callable(PolygonViewHandler)
    
class PolygonPluginOp(PolygonOp, PluginOpMixin):
    handler_factory = Callable(PolygonHandler)

@provides(IOperationPlugin)
class PolygonPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.polygon'
    operation_id = 'edu.mit.synbio.cytoflow.operations.polygon'

    short_name = "Polygon Gate"
    menu_group = "Gates"
    
    def get_operation(self):
        return PolygonPluginOp()
    
    def get_default_view(self):
        return PolygonSelectionView()
     
    def get_icon(self):
        return ImageResource('polygon')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self