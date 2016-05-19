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

from traits.api import provides, Callable, Dict, Event, Str, List, on_trait_change
from traitsui.api import View, Item, Controller, VGroup, ButtonEditor, EnumEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import TableView, geom_mean
import cytoflow.utility as util

from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.clearable_enum_editor import ClearableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin
    
import numpy as np
    
class TableHandler(Controller, ViewHandlerMixin):
    """
    docs
    """


    
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('channel',
                                editor = ClearableEnumEditor(name='context.channels'),
                                label = "Channel"),
                           Item('row_facet',
                                editor = ClearableEnumEditor(name='context.conditions'),
                                label = "Rows"),
                           Item('subrow_facet',
                                editor = ClearableEnumEditor(name='context.conditions'),
                                label = "Subrows"),
                           Item('column_facet',
                                editor = ClearableEnumEditor(name='context.conditions'),
                                label = "Columns"),
                           Item('subcolumn_facet',
                                editor = ClearableEnumEditor(name='context.conditions'),
                                label = "Subcolumn"),
                           Item('function_name',
                                editor = EnumEditor(name='function_names'),
                                label = "Summary\nFunction"),
                           Item('export',
                                editor = ButtonEditor(label = "Export...")),
                           label = "Table View",
                           show_border = False),
                    VGroup(Item('subset',
                                show_label = False,
                                editor = SubsetEditor(conditions_types = "context.conditions_types",
                                                      conditions_values = "context.conditions_values")),
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
                    
    
class TablePluginView(TableView, PluginViewMixin):
    handler_factory = Callable(TableHandler)
    export = Event()
    
    # functions aren't pickleable; send the function name instead
    summary_functions = Dict({"Mean" : np.mean,
                             # TODO - add count and proportion
                             "Geom.Mean" : geom_mean,
                             "Count" : len})
    
    function_names = List(["Mean", "Geom.Mean", "Count"])
    function_name = Str()
    function = Callable(transient = True)
    
    def plot(self, experiment, **kwargs):
        if not self.function_name:
            raise util.CytoflowViewError("Summary function isn't set")
        
        self.function = self.summary_functions[self.function_name]
        TableView.plot(self, experiment, **kwargs)
    
    @on_trait_change('export')
    def _on_export(self):
        pass

@provides(IViewPlugin)
class TablePlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.table'
    view_id = 'edu.mit.synbio.cytoflow.view.table'
    short_name = "1D Statistics View"
    
    def get_view(self):
        return TablePluginView()

    def get_icon(self):
        return ImageResource('table')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self