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

from traits.api import provides, Callable, Constant
from traitsui.api import View, Item, EnumEditor, Controller, VGroup
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.operations.range2d import Range2DOp, RangeSelection2D
from cytoflow.views.i_selectionview import ISelectionView

from cytoflowgui.op_plugins.i_op_plugin \
    import IOperationPlugin, OpHandlerMixin, PluginOpMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.clearable_enum_editor import ClearableEnumEditor

class Range2DHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('name'),
                    Item('xchannel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "X Channel"),
                    Item('xlow', label = "X Low"),
                    Item('xhigh', label = "X High"),
                    Item('ychannel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Y Channel"),
                    Item('ylow', label = "Y Low"),
                    Item('yhigh', label = "Y High"),
                    shared_op_traits) 
        
class RangeView2DHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name', 
                                style = 'readonly'),
                           Item('xchannel', 
                                label = "X Channel", 
                                style = 'readonly'),
                           Item('xscale',
                                label = "X Scale"),
                           Item('object.ychannel',
                                label = "Y Channel",
                                style = 'readonly'),
                           Item('yscale',
                                label = "Y Scale"),
                           Item('huefacet',
                                editor=ClearableEnumEditor(name='context.previous.conditions_names'),
                                label="Color\nFacet"),
                           label = "2D Range Setup View",
                           show_border = False),
                    VGroup(Item('subset',
                                show_label = False,
                                editor = SubsetEditor(conditions = "context.conditions",
                                                      values = "context.conditions_values")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('warning',
                         resizable = True,
                         visible_when = 'warning',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                 background_color = "#ffff99")),
                    Item('error',
                         resizable = True,
                         visible_when = 'error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191"))))

@provides(ISelectionView)
class Range2DSelectionView(RangeSelection2D, PluginViewMixin):
    handler_factory = Callable(RangeView2DHandler)
    
    def plot_wi(self, wi):
        self.plot(wi.previous.result)
    
class Range2DPluginOp(Range2DOp, PluginOpMixin):
    handler_factory = Callable(Range2DHandler)
    
    def default_view(self, **kwargs):
        return Range2DSelectionView(op = self, **kwargs)

@provides(IOperationPlugin)
class Range2DPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.range2d'
    operation_id = 'edu.mit.synbio.cytoflow.operations.range2d'

    short_name = "Range 2D"
    menu_group = "Gates"
    
    def get_operation(self):
        return Range2DPluginOp()

    def get_icon(self):
        return ImageResource('range2d')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self