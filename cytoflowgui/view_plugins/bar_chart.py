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

"""
Created on Feb 24, 2015

@author: brian
"""

from traits.api import provides, Callable, Str
from traitsui.api import View, Item, VGroup, Controller, EnumEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import BarChartView
import cytoflow.utility as util

from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin
    
from cytoflowgui.util import summary_functions, error_functions
    
class BarChartHandler(Controller, ViewHandlerMixin):
    """
    docs
    """

    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('channel',
                                editor=EnumEditor(name='context.channels'),
                                label = "Channel"),
                           Item('variable',
                                editor=EnumEditor(name='context.conditions'),
                                label = "Variable"),
                           Item('function_name',
                                editor = EnumEditor(values = summary_functions.keys()),
                                label = "Summary\nFunction"),
                           Item('orientation'),
                           Item('error_bars',
                                editor = ExtendableEnumEditor(name='handler.conditions',
                                                              extra_items = {"None" : "",
                                                                             "DATA" : "data"}),
                                 label = "Error bars"),
                           Item('error_function_name',
                                editor = EnumEditor(values = error_functions.keys()),
                                label = "Error\nfunction",
                                visible_when = 'object.error_bars'),
                           Item('xfacet',
                                editor=ExtendableEnumEditor(name='handler.conditions',
                                                            extra_items = {"None" : ""}),
                                label = "Horizontal\nFacet"),
                           Item('yfacet',
                                editor=ExtendableEnumEditor(name='handler.conditions',
                                                            extra_items = {"None" : ""}),
                                label = "Vertical\nFacet"),
                           Item('huefacet',
                                editor=ExtendableEnumEditor(name='handler.conditions',
                                                            extra_items = {"None" : ""}),
                                label="Color\nFacet"),
                             label = "Bar Chart",
                             show_border = False),
                    VGroup(Item('subset_dict',
                                show_label = False,
                                editor = SubsetEditor(conditions = "context.conditions")),
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
    
class BarChartPluginView(PluginViewMixin, BarChartView):
    handler_factory = Callable(BarChartHandler)
    
    # functions aren't pickleable, so send the name instead.  must make
    # the callables transient so we don't get a loop!
    
    function_name = Str
    #function = Callable(transient = True)

    error_function_name = Str
    #error_function = Callable(transient = True)
    
    def plot(self, experiment, **kwargs):
        
        if not self.function_name:
            raise util.CytoflowViewError("Summary function isn't set")
        
        self.function = summary_functions[self.function_name]
         
        if self.error_bars and self.error_function_name:
            self.error_function = error_functions[self.error_function_name]
             
        BarChartView.plot(self, experiment, **kwargs)

@provides(IViewPlugin)
class BarChartPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.barchart'
    view_id = 'edu.mit.synbio.cytoflow.view.barchart'
    short_name = "Bar Chart"
    
    def get_view(self):
        return BarChartPluginView()

    def get_icon(self):
        return ImageResource('bar_chart')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self