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

from traitsui.api import View, Item, EnumEditor, Controller, VGroup
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable
from pyface.api import ImageResource

from cytoflow.operations.binning import BinningOp, BinningView
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

class BinningHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('name'),
                    Item('channel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Channel"),
                    Item('scale'),
                    Item('num_bins', label = "Num Bins"),
                    Item('bin_width'),
                    shared_op_traits)

class BinningPluginOp(BinningOp, PluginOpMixin):
    handler_factory = Callable(BinningHandler)

class BinningViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name',
                                style = 'readonly'),
                           Item('channel',
                                style = 'readonly'),
                           Item('huefacet',
                                style = 'readonly'),
                           label = "Binning Default Plot",
                           show_border = False)))

@provides(IView)
class BinningPluginView(BinningView, PluginViewMixin):
    handler_factory = Callable(BinningViewHandler)

@provides(IOperationPlugin)
class BinningPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.binning'
    operation_id = 'edu.mit.synbio.cytoflow.operations.binning'

    short_name = "Binning"
    menu_group = "Gates"
    
    def get_operation(self):
        return BinningPluginOp()
    
    def get_default_view(self):
        return BinningPluginView()
    
    def get_icon(self):
        return ImageResource('binning')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    