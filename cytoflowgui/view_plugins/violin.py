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
from traitsui.api import View, Item, VGroup, Controller, EnumEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import ViolinPlotView

from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin
    
class ViolinHandler(Controller, ViewHandlerMixin):
    """
    docs
    """
    
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('variable',
                                editor=EnumEditor(name='context.conditions'),
                                label = "X Variable"),
                           Item('channel',
                                editor=EnumEditor(name='context.channels'),
                                label = "Y Channel"),
                           Item('scale',
                                label = "Y Channel\nScale"),
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
                             label = "Violin Plot",
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
    
class ViolinPlotPluginView(ViolinPlotView, PluginViewMixin):
    handler_factory = Callable(ViolinHandler)

@provides(IViewPlugin)
class ViolinPlotPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.violin'
    view_id = 'edu.mit.synbio.cytoflow.view.violin'
    short_name = "Violin Plot"
    
    def get_view(self):
        return ViolinPlotPluginView()

    def get_icon(self):
        return ImageResource('violin')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self