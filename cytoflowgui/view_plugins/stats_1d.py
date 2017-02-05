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

from cytoflow import Stats1DView

from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, StatisticViewHandlerMixin, PluginViewMixin
    
class Stats1DHandler(Controller, ViewHandlerMixin, StatisticViewHandlerMixin):
    """
    docs
    """
    
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('statistic',
                                editor=EnumEditor(name='context.statistics_names'),
                                label = "Statistic"),
                           Item('variable',
                                editor = EnumEditor(name = 'handler.numeric_indices')),
                           Item('xscale', label = "X Scale"),
                           Item('yscale', label = "Y Scale"),
                           Item('xfacet',
                                editor=ExtendableEnumEditor(name='handler.indices',
                                                            extra_items = {"None" : ""}),
                                label = "Horizontal\nFacet"),
                           Item('yfacet',
                                editor=ExtendableEnumEditor(name='handler.indices',
                                                            extra_items = {"None" : ""}),
                                label = "Vertical\nFacet"),
                           Item('huefacet',
                                editor=ExtendableEnumEditor(name='handler.indices',
                                                            extra_items = {"None" : ""}),
                                label="Hue\nFacet"),
                           Item('huescale', 
                                label = "Hue\nScale"),
                           Item('error_statistic',
                                editor=ExtendableEnumEditor(name='context.statistics_names',
                                                            extra_items = {"None" : ("", "")}),
                                label = "Error\nStatistic"),
                           label = "One-Dimensional Statistics Plot",
                           show_border = False),
                    VGroup(Item('subset_dict',
                                show_label = False,
                                editor = SubsetEditor(conditions = "handler.levels")),
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

class Stats1DPluginView(PluginViewMixin, Stats1DView):
    handler_factory = Callable(Stats1DHandler)
        

@provides(IViewPlugin)
class Stats1DPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.stats1d'
    view_id = 'edu.mit.synbio.cytoflow.view.stats1d'
    short_name = "1D Statistics View"
    
    def get_view(self):
        return Stats1DPluginView()

    def get_icon(self):
        return ImageResource('stats_1d')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self