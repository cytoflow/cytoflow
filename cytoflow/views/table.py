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

from __future__ import division, absolute_import

from traits.api import HasStrictTraits, Str, provides, Callable
import matplotlib.pyplot as plt

from matplotlib.table import Table

import numpy as np
import pandas as pd

from .i_view import IView
import cytoflow.utility as util

@provides(IView)
class TableView(HasStrictTraits):

    # traits   
    id = "edu.mit.synbio.cytoflow.view.table"
    friendly_id = "Table View" 
    
    name = Str
    row_facet = Str
    subrow_facet = Str
    column_facet = Str
    subcolumn_facet = Str
    
    subset = Str
    
    channel = Str
    function = Callable
    
    def plot(self, experiment, **kwargs):
        """Plot a table"""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.channel or self.channel not in experiment.data:
            raise util.CytoflowViewError("Must set a channel")            
        
        if not (self.row_facet or self.column_facet):
            raise util.CytoflowViewError("Must set at least one of row_facet "
                                         "or column_facet")
            
        if self.subrow_facet and not self.row_facet:
            raise util.CytoflowViewError("Must set row_facet before using "
                                         "subrow_facet")
            
        if self.subcolumn_facet and not self.column_facet:
            raise util.CytoflowViewError("Must set column_facet before using "
                                         "subcolumn_facet")
            
        if self.row_facet and self.row_facet not in experiment.conditions:
            raise util.CytoflowViewError("Row facet {0} not in the experiment"
                                    .format(self.row_facet))        
            
        if self.subrow_facet and self.subrow_facet not in experiment.conditions:
            raise util.CytoflowViewError("Subrow facet {0} not in the experiment"
                                    .format(self.subrow_facet))  
            
        if self.column_facet and self.column_facet not in experiment.conditions:
            raise util.CytoflowViewError("Column facet {0} not in the experiment"
                                    .format(self.column_facet))  
            
        if self.subcolumn_facet and self.subcolumn_facet not in experiment.conditions:
            raise util.CytoflowViewError("Subcolumn facet {0} not in the experiment"
                                    .format(self.subcolumn_facet))  
            
        if not self.function:
            raise util.CytoflowViewError("Summary function isn't set")
            
        row_groups = np.sort(pd.unique(experiment[self.row_facet])) \
                     if self.row_facet else [None]
                     
        subrow_groups = np.sort(pd.unique(experiment[self.subrow_facet])) \
                        if self.subrow_facet else [None] 
        
        col_groups = np.sort(pd.unique(experiment[self.column_facet])) \
                     if self.column_facet else [None]
                     
        subcol_groups = np.sort(pd.unique(experiment[self.subcolumn_facet])) \
                        if self.subcolumn_facet else [None]


        if self.subset:
            try:
                data = experiment.query(self.subset).data
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                
            if len(data.index) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
            
        group_vars = []
        if self.row_facet: group_vars.append(self.row_facet) 
        if self.subrow_facet: group_vars.append(self.subrow_facet)
        if self.column_facet: group_vars.append(self.column_facet)
        if self.subcolumn_facet: group_vars.append(self.subcolumn_facet)
                
        agg = data.groupby(by = group_vars)[self.channel].aggregate(self.function)

        # agg is a multi-index series; we can get a particular value from it
        # with get(idx1, idx2...)

        row_offset = (self.column_facet != "") + (self.subcolumn_facet != "")        
        col_offset = (self.row_facet != "") + (self.subrow_facet != "")
        
        num_cols = len(col_groups) * len(subcol_groups) + col_offset
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
        # hide the plot axes that matplotlib tries to make
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        for sp in ax.spines.itervalues():
            sp.set_color('w')
            sp.set_zorder(0)
        
        loc = 'best'
        bbox = None
        
        t = Table(ax, loc, bbox, **kwargs)
        width = [1.0 / num_cols] * num_cols
        height = t._approx_text_height() * 1.8
        
         
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
                        t.add_cell(row_idx, 
                                   col_idx,
                                   width = width[col_idx],
                                   height = height,
                                   text = agg.get(agg_idx))
                        
        # row headers
        if self.row_facet:
            for (ri, r) in enumerate(row_groups):
                row_idx = ri * len(subrow_groups) + row_offset
                text = "{0} = {1}".format(self.row_facet, r)
                t.add_cell(row_idx,
                           0,
                           width = width[0],
                           height = height,
                           text = text)
                
        # subrow headers
        if self.subrow_facet:
            for (ri, r) in enumerate(row_groups):
                for (rri, rr) in enumerate(subrow_groups):
                    row_idx = ri * len(subrow_groups) + rri + row_offset
                    text = "{0} = {1}".format(self.subrow_facet, rr)
                    t.add_cell(row_idx,
                               1,
                               width = width[1],
                               height = height,
                               text = text)
                    
        # column headers
        if self.column_facet:
            for (ci, c) in enumerate(col_groups):
                col_idx = ci * len(subcol_groups) + col_offset
                text = "{0} = {1}".format(self.column_facet, c)
                t.add_cell(0,
                           col_idx,
                           width = width[col_idx],
                           height = height,
                           text = text)

        # column headers
        if self.subcolumn_facet:
            for (ci, c) in enumerate(col_groups):
                for (cci, cc) in enumerate(subcol_groups):
                    col_idx = ci * len(subcol_groups) + cci + col_offset
                    text = "{0} = {1}".format(self.subcolumn_facet, c)
                    t.add_cell(1,
                               col_idx,
                               width = width[col_idx],
                               height = height,
                               text = text)                
                        
        ax.add_table(t)