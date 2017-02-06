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

import pandas as pd

from traits.api import provides, Callable, Property
from traitsui.api import View, Item, Controller, EnumEditor, VGroup
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import Stats2DView
import cytoflow.utility as util

from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, StatisticViewHandlerMixin, PluginViewMixin
    
class Stats2DHandler(Controller, ViewHandlerMixin, StatisticViewHandlerMixin):
    """
    docs
    """
    
    # override corresponding props from the StatisticViewHandlerMixin
    numeric_indices = Property(depends_on = "model.xstatistic")
    indices = Property(depends_on = "model.xstatistic")
    
    # MAGIC: gets the value for the property numeric_indices
    def _get_numeric_indices(self):
        context = self.info.ui.context['context']
        
        if not (context and context.statistics and self.model and self.model.xstatistic[0]):
            return []
        
        stat = context.statistics[self.model.xstatistic]
        data = pd.DataFrame(index = stat.index)
        
        if self.model.subset:
            data = data.query(self.model.subset)
            
        if len(data) == 0:
            return []       
        
        names = list(data.index.names)
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                data.index = data.index.droplevel(name)
        
        data.reset_index(inplace = True)
        return [x for x in data if util.is_numeric(data[x])]
    
    # MAGIC: gets the value for the property indices
    def _get_indices(self):
        context = self.info.ui.context['context']
        
        if not (context and context.statistics and self.model and self.model.xstatistic[0]):
            return []
        
        stat = context.statistics[self.model.xstatistic]
        data = pd.DataFrame(index = stat.index)
        
        if self.model.subset:
            data = data.query(self.model.subset)
            
        if len(data) == 0:
            return []       
        
        names = list(data.index.names)
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                data.index = data.index.droplevel(name)
        
        return list(data.index.names)
    
    
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('xstatistic',
                                editor = EnumEditor(name = 'context.statistics_names'),
                                label = "X Statistic"),
                           Item('xscale', label = "X Scale"),
                           Item('ystatistic',
                                editor = EnumEditor(name = 'context.statistics_names'),
                                label = "Y Statistic"),
                           Item('yscale', label = "Y Scale"),
                           Item('variable',
                                editor=EnumEditor(name='handler.numeric_indices')),
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
                                label="Color\nFacet"),
                           Item('huescale', 
                                label = "Hue\nScale"),
                           Item('x_error_statistic',
                                editor=ExtendableEnumEditor(name='context.statistics_names',
                                                            extra_items = {"None" : ("", "")}),
                                label = "X Error\nStatistic"),
                           Item('y_error_statistic',
                                editor=ExtendableEnumEditor(name='context.statistics_names',
                                                            extra_items = {"None" : ("", "")}),
                                label = "Y Error\nStatistic"),
                           label = "Two-Dimensional Statistics Plot",
                           show_border = False),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "handler.levels")),
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