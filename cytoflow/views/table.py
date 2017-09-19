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

'''
cytoflow.views.table
--------------------
'''

from warnings import warn
from traits.api import HasStrictTraits, Str, provides, Tuple, Constant
import matplotlib.pyplot as plt

from matplotlib.table import Table

import pandas as pd

from .i_view import IView
import cytoflow.utility as util

@provides(IView)
class TableView(HasStrictTraits):
    """
    "Plot" a tabular view of a statistic.  Mostly useful for GUIs.  Each level 
    of the statistic's index must be used in :attr:`row_facet`, 
    :attr:`column_facet`, :attr:`subrow_facet`, or :attr:`subcolumn_facet`.
    This module can't "plot" a statistic with more than four index levels
    unless :attr:`subset` is set and that results in extra levels being 
    dropped.
    
    Attributes
    ----------
    statistic : (str, str)
        The name of the statistic to plot.  Must be a key in the  
        :attr:`~Experiment.statistics` attribute of the :class:`~.Experiment`
        being plotted.  Each level of the statistic's index must be used 
        in :attr:`row_facet`, :attr:`column_facet`, :attr:`subrow_facet`, or
        :attr:`subcolumn_facet`.
        
    row_facet, column_facet : str
        The statistic facets to be used as row and column headers.
        
    subrow_facet, subcolumn_facet : str
        The statistic facets to be used as subrow and subcolumn headers.
        
    subset : str
        A Python expression used to select a subset of the statistic to plot.
        
    Examples
    --------
    
    Make a little data set.
    
    .. plot::
        :context: close-figs
            
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
        
    Add a threshold gate
    
    .. plot::
        :context: close-figs
    
        >>> ex2 = flow.ThresholdOp(name = 'Threshold',
        ...                        channel = 'Y2-A',
        ...                        threshold = 2000).apply(ex)
        
    Add a statistic
    
    .. plot::
        :context: close-figs

        >>> ex3 = flow.ChannelStatisticOp(name = "ByDox",
        ...                               channel = "Y2-A",
        ...                               by = ['Dox', 'Threshold'],
        ...                               function = len).apply(ex2) 
    
    "Plot" the table
    
    .. plot::
        :context: close-figs
        
        >>> flow.TableView(statistic = ("ByDox", "len"),
        ...                row_facet = "Dox",
        ...                column_facet = "Threshold").plot(ex3)
        
    """

    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.table")
    friendly_id = Constant("Table View") 

    REMOVED_ERROR = Constant("Statistics have changed dramatically in 0.5; please see the documentation")
    channel = util.Removed(err_string = REMOVED_ERROR)
    function = util.Removed(err_string = REMOVED_ERROR)
    
    statistic = Tuple(Str, Str)
    row_facet = Str
    subrow_facet = Str
    column_facet = Str
    subcolumn_facet = Str
    
    subset = Str

    def plot(self, experiment, plot_name = None, **kwargs):
        """Plot a table"""
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")   
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic', 
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
        else:
            stat = experiment.statistics[self.statistic]    
            
        data = pd.DataFrame(index = stat.index)
        data[stat.name] = stat   
        
        if self.subset:
            try:
                data = data.query(self.subset)
            except Exception as e:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(self.subset)) from e
                
            if len(data) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no values"
                                             .format(self.subset))
            
        names = list(data.index.names)
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                warn("Only one value for level {}; dropping it.".format(name),
                     util.CytoflowViewWarning)
                try:
                    data.index = data.index.droplevel(name)
                except AttributeError as e:
                    raise util.CytoflowViewError(None,
                                                 "Must have more than one "
                                                 "value to plot.") from e
        
        if not (self.row_facet or self.column_facet):
            raise util.CytoflowViewError('row_facet',
                                         "Must set at least one of row_facet "
                                         "or column_facet")
            
        if self.subrow_facet and not self.row_facet:
            raise util.CytoflowViewError('subrow_facet',
                                         "Must set row_facet before using "
                                         "subrow_facet")
            
        if self.subcolumn_facet and not self.column_facet:
            raise util.CytoflowViewError('subcolumn_facet',
                                         "Must set column_facet before using "
                                         "subcolumn_facet")
            
        if self.row_facet and self.row_facet not in experiment.conditions:
            raise util.CytoflowViewError('row_facet',
                                         "Row facet {} not in the experiment, "
                                         "must be one of {}"
                                         .format(self.row_facet, experiment.conditions))        

        if self.row_facet and self.row_facet not in data.index.names:
            raise util.CytoflowViewError('row_facet',
                                         "Row facet {} not a statistic index; "
                                         "must be one of {}"
                                         .format(self.row_facet, data.index.names))  
            
        if self.subrow_facet and self.subrow_facet not in experiment.conditions:
            raise util.CytoflowViewError('subrow_facet',
                                         "Subrow facet {} not in the experiment, "
                                         "must be one of {}"
                                         .format(self.subrow_facet, experiment.conditions))  
            
        if self.subrow_facet and self.subrow_facet not in data.index.names:
            raise util.CytoflowViewError('subrow_facet',
                                         "Subrow facet {} not a statistic index; "
                                         "must be one of {}"
                                         .format(self.subrow_facet, data.index.names))  
            
        if self.column_facet and self.column_facet not in experiment.conditions:
            raise util.CytoflowViewError('column_facet',
                                         "Column facet {} not in the experiment, "
                                         "must be one of {}"
                                         .format(self.column_facet, experiment.conditions))  
            
        if self.column_facet and self.column_facet not in data.index.names:
            raise util.CytoflowViewError('column_facet',
                                         "Column facet {} not a statistic index; "
                                         "must be one of {}"
                                         .format(self.column_facet, data.index.names)) 
            
        if self.subcolumn_facet and self.subcolumn_facet not in experiment.conditions:
            raise util.CytoflowViewError('subcolumn_facet',
                                         "Subcolumn facet {} not in the experiment, "
                                         "must be one of {}"
                                         .format(self.subcolumn_facet, experiment.conditions))  
            
        if self.subcolumn_facet and self.subcolumn_facet not in data.index.names:
            raise util.CytoflowViewError('subcolumn_facet',
                                         "Subcolumn facet {} not a statistic index; "
                                         "must be one of {}"
                                         .format(self.subcolumn_facet, data.index.names))  

        facets = [x for x in [self.row_facet, self.subrow_facet, 
                                      self.column_facet, self.subcolumn_facet] if x]
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError(None, 
                                         "Can't reuse facets")
        
        if set(facets) != set(data.index.names):
            raise util.CytoflowViewError(None,
                                         "Must use all the statistic indices as variables or facets: {}"
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
        
        num_cols = len(col_groups) * len(subcol_groups) + col_offset
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
        # hide the plot axes that matplotlib tries to make
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        for sp in ax.spines.values():
            sp.set_color('w')
            sp.set_zorder(0)
        
        loc = 'upper left'
        bbox = None
        
        t = Table(ax, loc, bbox, **kwargs)
        t.auto_set_font_size(False)
        for c in range(num_cols):
            t.auto_set_column_width(c)

        width = [0.2] * num_cols

        height = t._approx_text_height() * 1.8
         
        # make the main table       
        for (ri, r) in enumerate(row_groups):
            for (rri, rr) in enumerate(subrow_groups):
                for (ci, c) in enumerate(col_groups):
                    for (cci, cc) in enumerate(subcol_groups):
                        row_idx = ri * len(subrow_groups) + rri + row_offset
                        col_idx = ci * len(subcol_groups) + cci + col_offset
                        
                        # this is not pythonic, but i'm tired
                        agg_idx = []
                        for data_idx in data.index.names:
                            if data_idx == self.row_facet:
                                agg_idx.append(r)
                            elif data_idx == self.subrow_facet:
                                agg_idx.append(rr)
                            elif data_idx == self.column_facet:
                                agg_idx.append(c)
                            elif data_idx == self.subcolumn_facet:
                                agg_idx.append(cc)
                        
                        agg_idx = tuple(agg_idx)
                        if len(agg_idx) == 1:
                            agg_idx = agg_idx[0]
                            
                        try:
                            text = "{:g}".format(data.loc[agg_idx][stat.name])
                        except ValueError:
                            text = data.loc[agg_idx][stat.name]
                        t.add_cell(row_idx, 
                                   col_idx,
                                   width = width[col_idx],
                                   height = height,
                                   text = text)
                        
        # row headers
        if self.row_facet:
            for (ri, r) in enumerate(row_groups):
                row_idx = ri * len(subrow_groups) + row_offset
                try:
                    text = "{0} = {1:g}".format(self.row_facet, r)
                except ValueError:
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
                    try:
                        text = "{0} = {1:g}".format(self.subrow_facet, rr)
                    except ValueError:
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
                try:
                    text = "{0} = {1:g}".format(self.column_facet, c)
                except ValueError:
                    text = "{0} = {1}".format(self.column_facet, c)
                t.add_cell(0,
                           col_idx,
                           width = width[col_idx],
                           height = height,
                           text = text)

        # subcolumn headers
        if self.subcolumn_facet:
            for (ci, c) in enumerate(col_groups):
                for (cci, cc) in enumerate(subcol_groups):
                    col_idx = ci * len(subcol_groups) + cci + col_offset
                    try:
                        text = "{0} = {1:g}".format(self.subcolumn_facet, cc)
                    except ValueError:
                        text = "{0} = {1}".format(self.subcolumn_facet, cc)
                    t.add_cell(1,
                               col_idx,
                               width = width[col_idx],
                               height = height,
                               text = text)                
                        
        ax.add_table(t)