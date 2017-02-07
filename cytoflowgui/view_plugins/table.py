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

import numpy as np
import pandas as pd

from traits.api import provides, Callable, Event, on_trait_change, Instance
from traitsui.api import View, Item, Controller, VGroup, ButtonEditor, EnumEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource, FileDialog, OK

from cytoflow import TableView
import cytoflow.utility as util

from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, StatisticViewHandlerMixin, PluginViewMixin
from cytoflowgui.util import DefaultFileDialog

class TableHandler(Controller, ViewHandlerMixin, StatisticViewHandlerMixin):
    """
    docs
    """

    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('statistic',
                                editor = EnumEditor(name='context.statistics_names'),
                                label = "Statistic"),
                           Item('row_facet',
                                editor = ExtendableEnumEditor(name='handler.indices',
                                                            extra_items = {"None" : ""}),
                                label = "Rows"),
                           Item('subrow_facet',
                                editor = ExtendableEnumEditor(name='handler.indices',
                                                            extra_items = {"None" : ""}),
                                label = "Subrows"),
                           Item('column_facet',
                                editor = ExtendableEnumEditor(name='handler.indices',
                                                            extra_items = {"None" : ""}),
                                label = "Columns"),
                           Item('subcolumn_facet',
                                editor = ExtendableEnumEditor(name='handler.indices',
                                                            extra_items = {"None" : ""}),
                                label = "Subcolumn"),
                           Item('export',
                                editor = ButtonEditor(label = "Export..."),
                                enabled_when = 'result is not None'),
                           label = "Table View",
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
                    
    
class TablePluginView(TableView, PluginViewMixin):
    handler_factory = Callable(TableHandler)
    
    export = Event()
    
    # return the result for export
    result = Instance(pd.Series, status = True)
    
    def plot(self, experiment, plot_name = None, **kwargs):
        TableView.plot(self, experiment, **kwargs)
        self.result = experiment.statistics[self.statistic]
        
#         self.result = None
#         if not self.function_name:
#             raise util.CytoflowViewError("Summary function isn't set")
#          
#         self.function = self.summary_functions[self.function_name]
#         TableView.plot(self, experiment, **kwargs)
#          
#         group_vars = []
#         if self.row_facet: group_vars.append(self.row_facet) 
#         if self.subrow_facet: group_vars.append(self.subrow_facet)
#         if self.column_facet: group_vars.append(self.column_facet)
#         if self.subcolumn_facet: group_vars.append(self.subcolumn_facet)
#                  
#         if self.subset:
#             data = experiment.query(self.subset).data
#         else:
#             data = experiment.data
#                  
#         self.result = data.groupby(by = group_vars)[self.channel].aggregate(self.function)
#      
    @on_trait_change('export')
    def _on_export(self):
        
        dialog = DefaultFileDialog(parent = None,
                                   action = 'save as', 
                                   default_suffix = "csv",
                                   wildcard = (FileDialog.create_wildcard("CSV", "*.csv") + ';' + #@UndefinedVariable  
                                               FileDialog.create_wildcard("All files", "*")))     #@UndefinedVariable  

        if dialog.open() != OK:
            return

        
        data = pd.DataFrame(index = self.result.index)
        data[self.result.name] = self.result   
        
        if self.subset:
            data = data.query(self.subset)
        
        names = list(data.index.names)
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                data.index = data.index.droplevel(name) 
                
        facets = filter(lambda x: x, [self.row_facet, self.subrow_facet, 
                                      self.column_facet, self.subcolumn_facet])
        
        if set(facets) != set(data.index.names):
            raise util.CytoflowViewError("Must use all the statistic indices as variables or facets: {}"
                                         .format(data.index.names))
            
        row_groups = data.index.get_level_values(self.row_facet).unique() \
                     if self.row_facet else [None]
                     
        subrow_groups = data.index.get_level_values(self.subrow_facet).unique() \
                        if self.subrow_facet else [None] 
        
        col_groups = data.index.get_level_values(self.column_facet).unique() \
                     if self.column_facet else [None]
                     
        subcol_groups = data.index.get_level_values(self.subcolumn_facet).unique() \
                        if self.subcolumn_facet else [None]

        row_offset = (self.column_facet != "") + (self.subcolumn_facet != "")        
        col_offset = (self.row_facet != "") + (self.subrow_facet != "")
        
        num_rows = len(row_groups) * len(subrow_groups) + row_offset
        num_cols = len(col_groups) * len(subcol_groups) + col_offset

        t = np.empty((num_rows, num_cols), dtype = np.object_)
 
        # make the main table       
        for (ri, r) in enumerate(row_groups):
            for (rri, rr) in enumerate(subrow_groups):
                for (ci, c) in enumerate(col_groups):
                    for (cci, cc) in enumerate(subcol_groups):
                        row_idx = ri * len(subrow_groups) + rri + row_offset
                        col_idx = ci * len(subcol_groups) + cci + col_offset
                        agg_idx = [x for x in (r, rr, c, cc) if x is not None]
                        agg_idx = tuple(agg_idx)
                        if len(agg_idx) == 1:
                            agg_idx = agg_idx[0]
                        t[row_idx, col_idx] = self.result.get(agg_idx) 
                        
        # row headers
        if self.row_facet:
            for (ri, r) in enumerate(row_groups):
                row_idx = ri * len(subrow_groups) + row_offset
                text = "{0} = {1}".format(self.row_facet, r)
                t[row_idx, 0] = text
                
        # subrow headers
        if self.subrow_facet:
            for (ri, r) in enumerate(row_groups):
                for (rri, rr) in enumerate(subrow_groups):
                    row_idx = ri * len(subrow_groups) + rri + row_offset
                    text = "{0} = {1}".format(self.subrow_facet, rr)
                    t[row_idx, 1] = text
                    
        # column headers
        if self.column_facet:
            for (ci, c) in enumerate(col_groups):
                col_idx = ci * len(subcol_groups) + col_offset
                text = "{0} = {1}".format(self.column_facet, c)
                t[0, col_idx] = text

        # column headers
        if self.subcolumn_facet:
            for (ci, c) in enumerate(col_groups):
                for (cci, cc) in enumerate(subcol_groups):
                    col_idx = ci * len(subcol_groups) + cci + col_offset
                    text = "{0} = {1}".format(self.subcolumn_facet, c)
                    t[1, col_idx] = text        
                    
        np.savetxt(dialog.path, t, delimiter = ",", fmt = "%s")
                    
           

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