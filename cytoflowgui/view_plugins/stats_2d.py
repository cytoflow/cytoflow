#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin
    
class Stats2DHandler(ViewHandlerMixin, Controller):
    """
    docs
    """
    
    indices = Property(depends_on = "context.statistics, model.xstatistic, model.ystatistic, model.subset")
    numeric_indices = Property(depends_on = "context.statistics, model.xstatistic, model.ystatistic, model.subset")
    levels = Property(depends_on = "context.statistics, model.xstatistic, model.ystatistic")
    
    
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('xstatistic',
                                editor = EnumEditor(name = 'handler.numeric_statistics_names'),
                                label = "X Statistic"),
                           Item('xscale', label = "X Scale"),
                           Item('ystatistic',
                                editor = EnumEditor(name = 'handler.numeric_statistics_names'),
                                label = "Y Statistic"),
                           Item('yscale', label = "Y Scale"),
                           Item('variable',
                                editor=EnumEditor(name='handler.indices')),
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
                                editor=ExtendableEnumEditor(name='handler.statistics_names',
                                                            extra_items = {"None" : ("", "")}),
                                label = "X Error\nStatistic"),
                           Item('y_error_statistic',
                                editor=ExtendableEnumEditor(name='handler.statistics_names',
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
        
    # MAGIC: gets the value for the property indices
    def _get_indices(self):
        if not (self.context and self.context.statistics 
                and self.model.xstatistic in self.context.statistics
                and self.model.ystatistic in self.context.statistics):
            return []
        
        xstat = self.context.statistics[self.model.xstatistic]
        ystat = self.context.statistics[self.model.ystatistic]
        
        index = xstat.index.intersection(ystat.index)
        
        data = pd.DataFrame(index = index)
        
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
        
    # MAGIC: gets the value for the property numeric_indices
    def _get_numeric_indices(self):        
        if not (self.context and self.context.statistics 
                and self.model.xstatistic in self.context.statistics
                and self.model.ystatistic in self.context.statistics):
            return []
        
        xstat = self.context.statistics[self.model.xstatistic]
        ystat = self.context.statistics[self.model.ystatistic]
        index = xstat.index.intersection(ystat.index)
        data = pd.DataFrame(index = index)
        
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
    
    # MAGIC: gets the value for the property 'levels'
    # returns a Dict(Str, pd.Series)
    
    def _get_levels(self):        
        if not (self.context and self.context.statistics 
                and self.model.xstatistic in self.context.statistics
                and self.model.ystatistic in self.context.statistics):
            return []
        
        xstat = self.context.statistics[self.model.xstatistic]
        ystat = self.context.statistics[self.model.ystatistic]
    
        index = xstat.index.intersection(ystat.index)
        
        names = list(index.names)
        for name in names:
            unique_values = index.get_level_values(name).unique()
            if len(unique_values) == 1:
                index = index.droplevel(name)

        names = list(index.names)
        ret = {}
        for name in names:
            ret[name] = pd.Series(index.get_level_values(name)).sort_values()
            ret[name] = pd.Series(ret[name].unique())
            
        return ret

    
class Stats2DPluginView(PluginViewMixin, Stats2DView):
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