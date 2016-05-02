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

from traits.api import provides, Callable
from traitsui.api import View, Item, Controller, EnumEditor, VGroup
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import HistogramView

from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.clearable_enum_editor import ClearableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin
    
class HistogramHandler(Controller, ViewHandlerMixin):
    """
    docs
    """
    
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('channel',
                                editor=EnumEditor(name='context.channels'),
                                label = "Channel"),
                           Item('scale'),
                           Item('xfacet',
                                editor=ClearableEnumEditor(name='context.conditions'),
                                label = "Horizontal\nFacet"),
                            Item('yfacet',
                                editor=ClearableEnumEditor(name='context.conditions'),
                                label = "Vertical\nFacet"),
                           Item('huefacet',
                                editor=ClearableEnumEditor(name='context.conditions'),
                                label="Color\nFacet"),
                            label = "Histogram Plot",
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
    
class HistogramPluginView(HistogramView, PluginViewMixin):
    handler_factory = Callable(HistogramHandler)

@provides(IViewPlugin)
class HistogramPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.histogram'
    view_id = 'edu.mit.synbio.cytoflow.view.histogram'
    short_name = "Histogram"
    
    def get_view(self):
        return HistogramPluginView()
    
    def get_icon(self):
        return ImageResource('histogram')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self