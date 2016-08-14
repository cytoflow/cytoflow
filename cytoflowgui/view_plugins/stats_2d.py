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
from traitsui.api import View, Item, Controller, EnumEditor, VGroup
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import Stats2DView
import cytoflow.utility as util

from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin
from cytoflowgui.util import summary_functions, error_functions
    
class Stats2DHandler(Controller, ViewHandlerMixin):
    """
    docs
    """
    
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('variable',
                                # TODO - restrict this to numeric values?
                                editor=EnumEditor(name='context.conditions')),
                           Item('xchannel',
                                editor=EnumEditor(name='context.channels'),
                                label = "X Channel"),
                           Item('xscale',
                                label = "X Scale"),
                           Item('xfunction_name',
                                editor = EnumEditor(values = summary_functions.keys()),
                                label = "X Summary\nFunction"),
                           Item('x_error_bars',
                                editor = ExtendableEnumEditor(name='context.conditions',
                                                              extra_items = {"None" : "",
                                                                             "DATA" : "data"}),
                                 label = "X Error bars"),
                           Item('x_error_function_name',
                                editor = EnumEditor(values = error_functions.keys()),
                                label = "X Error\nfunction",
                                visible_when = 'x_error_bars'),
                           Item('ychannel',
                                editor=EnumEditor(name='context.channels'),
                                label = "Y Channel"),
                           Item('yscale',
                                label = "Y Scale"),
                           Item('yfunction_name',
                                editor = EnumEditor(values = summary_functions.keys()),
                                label = "Y Summary\nFunction"),
                           Item('y_error_bars',
                                editor = ExtendableEnumEditor(name='context.conditions',
                                                              extra_items = {"None" : "",
                                                                             "DATA" : "data"}),
                                 label = "Y Error bars"),
                           Item('y_error_function_name',
                                editor = EnumEditor(values = error_functions.keys()),
                                label = "Y Error\nfunction",
                                visible_when = 'y_error_bars'),
                           Item('xfacet',
                                editor=ExtendableEnumEditor(name='context.conditions',
                                                            extra_items = {"None" : ""}),
                                label = "Horizontal\nFacet"),
                           Item('yfacet',
                                editor=ExtendableEnumEditor(name='context.conditions',
                                                            extra_items = {"None" : ""}),
                                label = "Vertical\nFacet"),
                           Item('huefacet',
                                editor=ExtendableEnumEditor(name='context.conditions',
                                                            extra_items = {"None" : ""}),
                                label="Color\nFacet"),
                           label = "One-Dimensional Statistics Plot",
                           show_border = False),
                    VGroup(Item('subset',
                                show_label = False,
                                editor = SubsetEditor(conditions_types = "context.conditions_types",
                                                      conditions_values = "context.conditions_values")),
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

    
class Stats2DPluginView(Stats2DView, PluginViewMixin):
    handler_factory = Callable(Stats2DHandler)
    
    # functions aren't picklable, so send the name instead
    
    xfunction_name = Str()
    xfunction = Callable(transient = True)
    x_error_function_name = Str()
    x_error_function = Callable(transient = True)
    yfunction_name = Str()
    yfunction = Callable(transient = True)
    y_error_function_name = Str()
    y_error_function = Callable(transient = True)
    
    def plot(self, experiment, **kwargs):
        if not self.xfunction_name:
            raise util.CytoflowViewError("X Summary function isn't set")
        
        self.xfunction = summary_functions[self.xfunction_name]
        
        if not self.yfunction_name:
            raise util.CytoflowViewError("Y Summary function isn't set")
        
        self.yfunction = summary_functions[self.yfunction_name]
        
        if self.x_error_bars and self.x_error_function_name:
            self.x_error_function = error_functions[self.x_error_function_name]

        if self.y_error_bars and self.y_error_function_name:
            self.y_error_function = error_functions[self.y_error_function_name]
             
        
        Stats2DView.plot(self, experiment, **kwargs)
        

@provides(IViewPlugin)
class Stats2DPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.stats2d'
    view_id = 'edu.mit.synbio.cytoflow.view.stats2d'
    short_name = "2D Statistics View"
    
    def get_view(self):
        return Stats2DPluginView()

    def get_icon(self):
        return ImageResource('stats_2d')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self