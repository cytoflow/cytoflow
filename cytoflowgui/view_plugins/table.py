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

from traits.api import provides, Callable, Dict, Event, Str, List, \
                       on_trait_change, Instance
from traitsui.api import View, Item, Controller, VGroup, ButtonEditor, EnumEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource, FileDialog, OK, error

from cytoflow import TableView, geom_mean
import cytoflow.utility as util

from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin

class TableHandler(Controller, ViewHandlerMixin):
    """
    docs
    """

    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('channel',
                                editor = EnumEditor(name='context.channels'),
                                label = "Channel"),
                           Item('function_name',
                                editor = EnumEditor(name='function_names'),
                                label = "Summary\nFunction"),
                           Item('row_facet',
                                editor = ExtendableEnumEditor(name='context.conditions',
                                                            extra_items = {"None" : ""}),
                                label = "Rows"),
                           Item('subrow_facet',
                                editor = ExtendableEnumEditor(name='context.conditions',
                                                            extra_items = {"None" : ""}),
                                label = "Subrows"),
                           Item('column_facet',
                                editor = ExtendableEnumEditor(name='context.conditions',
                                                            extra_items = {"None" : ""}),
                                label = "Columns"),
                           Item('subcolumn_facet',
                                editor = ExtendableEnumEditor(name='context.conditions',
                                                            extra_items = {"None" : ""}),
                                label = "Subcolumn"),
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
    
    # functions aren't pickleable; send the function name instead
    summary_functions = Dict({"Mean" : np.mean,
                             # TODO - add count and proportion
                             "Geom.Mean" : geom_mean,
                             "Count" : len})
    
    function_names = List(["Mean", "Geom.Mean", "Count"])
    function_name = Str()
    function = Callable(transient = True)
    
    # return the result for export
    result = Instance(pd.Series, transient = True, status = True)
    
    def plot(self, experiment, **kwargs):
        if not self.function_name:
            raise util.CytoflowViewError("Summary function isn't set")
        
        self.function = self.summary_functions[self.function_name]
        TableView.plot(self, experiment, **kwargs)
        
        group_vars = []
        if self.row_facet: group_vars.append(self.row_facet) 
        if self.subrow_facet: group_vars.append(self.subrow_facet)
        if self.column_facet: group_vars.append(self.column_facet)
        if self.subcolumn_facet: group_vars.append(self.subcolumn_facet)
                
        if self.subset:
            data = experiment.query(self.subset).data
        else:
            data = experiment.data
                
        self.result = data.groupby(by = group_vars)[self.channel].aggregate(self.function)
    
    @on_trait_change('export')
    def _on_export(self):
        
        if not self.result:
            error(None, "Nothing to save yet!", "Error")
            return
        
        dialog = FileDialog(parent = None,
                            action = 'save as',
                            wildcard = "CSV files (*.csv)|*.csv|)")
        if dialog.open() != OK:
            return
        
        idx = self.result.index
        
        if self.row_facet: 
            if isinstance(idx, pd.MultiIndex):
                row_facet_idx = idx.names.index(self.row_facet)
                row_groups = idx.levels[row_facet_idx]
            else:
                row_groups = list(idx)
                
            row_groups = np.sort(row_groups)
        else:
            row_groups = [None]
            
        if self.subrow_facet:
            subrow_facet_idx = idx.names.index(self.subrow_facet)
            subrow_groups = idx.levels[subrow_facet_idx]
            subrow_groups = np.sort(subrow_groups)
        else:
            subrow_groups = [None]
            
        if self.column_facet:
            if isinstance(idx, pd.MultiIndex):
                column_facet_idx = idx.names.index(self.column_facet)
                column_groups = idx.levels[column_facet_idx]
            else:
                column_groups = list(idx)
                
            column_groups = np.sort(column_groups)
        else:
            column_groups = [None]
            
        if self.subcolumn_facet:
            subcolumn_facet_idx = idx.names.index(self.subcolumn_facet)
            subcolumn_groups = idx.levels[subcolumn_facet_idx]
            subcolumn_groups = np.sort(subcolumn_groups)
        else:
            subcolumn_groups = [None]            
            
        row_offset = (self.column_facet != "") + (self.subcolumn_facet != "")        
        col_offset = (self.row_facet != "") + (self.subrow_facet != "")
        
        num_rows = len(row_groups) * len(column_groups) + row_offset
        num_cols = len(column_groups) * len(subcolumn_groups) + col_offset

        t = np.empty((num_rows, num_cols), dtype = np.object_)
 
         # make the main table       
        for (ri, r) in enumerate(row_groups):
            for (rri, rr) in enumerate(subrow_groups):
                for (ci, c) in enumerate(column_groups):
                    for (cci, cc) in enumerate(subcolumn_groups):
                        row_idx = ri * len(subrow_groups) + rri + row_offset
                        col_idx = ci * len(subcolumn_groups) + cci + col_offset
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
            for (ci, c) in enumerate(column_groups):
                col_idx = ci * len(subcolumn_groups) + col_offset
                text = "{0} = {1}".format(self.column_facet, c)
                t[0, col_idx] = text

        # column headers
        if self.subcolumn_facet:
            for (ci, c) in enumerate(column_groups):
                for (cci, cc) in enumerate(subcolumn_groups):
                    col_idx = ci * len(subcolumn_groups) + cci + col_offset
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