#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflow.views.table
--------------------

"Plot" a long (or "tidy") tabular view of a statistic.

`LongTableView` -- the `IView` class that makes the plot.
"""

from warnings import warn
from traits.api import HasStrictTraits, Str, provides, Constant
import matplotlib.pyplot as plt

from matplotlib.table import Table
import numpy as np

from .i_view import IView
import cytoflow
import cytoflow.utility as util

@provides(IView)
class LongTableView(HasStrictTraits):
    """
    "Plot" a long (or "tidy") tabular view of a statistic.  Mostly useful for 
    GUIs.  
    
    Attributes
    ----------
    statistic : Str
        The name of the statistic to plot.  Must be a key in the  
        `Experiment.statistics` attribute of the `Experiment`
        being plotted.  Each level of the statistic's index must be used 
        in `row_facet`, `column_facet`, `subrow_facet`, or
        `subcolumn_facet`.
                
    subset : Str
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
        
        >>> flow.LongTableView(statistic = "ByDox").plot(ex3)
        
    """

    # traits   
    id = Constant("cytoflow.view.long_table")
    friendly_id = Constant("Long Table View") 
    
    statistic = util.ChangedStr(err_string = "Statistics have changed dramatically -- see the documentation for updates.")
    subset = Str

    def plot(self, experiment, plot_name = None, **kwargs):
        """Plot a table"""
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")   
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic', 
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))

        data = experiment.statistics[self.statistic]
        
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
                
        if len(data) > 50:
            if cytoflow.RUNNING_IN_GUI:
                raise util.CytoflowViewError(None,
                                             "Can't make a table with more than 50 rows! "
                                             "You can still export the table, though." )
            else:
                raise util.CytoflowViewError(None,
                                             "Can't make a table with more than 50 rows!")
            
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
                                                 
        names = list(data.index.names)
        num_cols = len(names) + len(data.columns)

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

        width = [0.2] * (num_cols + 1)

        height = t._approx_text_height() * 1.8
                                                
        for name_idx, name in enumerate(names):
            t.add_cell(0, 
                       name_idx,
                       width = width[name_idx],
                       height = height,
                       text = name)
            
        for col_idx, col in enumerate(data.columns):
            t.add_cell(0, 
                       len(names) + col_idx,
                       width = width[len(names)],
                       height = height,
                       text = col)

        row_i = 1
        for row_idx, row_data in data.iterrows():
            
            # if there's only one level in the index, row_idx will be a single
            # value, not an iterable.
            
            try:
                iter(row_idx)
            except TypeError:
                row_idx = [row_idx]
                
            for idx_i, idx in enumerate(row_idx):
                try:
                    text = "{:g}".format(idx)
                except (TypeError, ValueError):
                    text = idx
                
                t.add_cell(row_i,
                           idx_i,
                           width = width[idx_i],
                           height = height,
                           text = text)
                
            for col_i, col in enumerate(data.columns):
                try:
                    text = "{:g}".format(row_data.loc[col])
                except (TypeError, ValueError):
                    text = row_data.loc[col]
                
                t.add_cell(row_i,
                           len(names) + col_i,
                           width = width[num_cols],
                           height = height,
                           text = text)     
            
            row_i = row_i + 1       
                        
        ax.add_table(t)
        
    def export(self, experiment, filename):
        """
        Export the table to a file.
        """
    
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")   
    
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic', 
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))

        stat = experiment.statistics[self.statistic]     
    
        self._export_data(stat, filename)
    
    def _export_data(self, data, filename):
    
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
    

        names = list(data.index.names)
        num_cols = len(names) + len(data.columns)
        num_rows = len(data) + 1
    
        t = np.empty((num_rows, num_cols), dtype = np.object_)
        
        for name_idx, name in enumerate(names):
            t[0, name_idx] = name
            
        for col_idx, col in enumerate(data.columns):
            t[0, len(names) + col_idx] = col
            
        row_i = 1
        for row_idx, row_data in data.iterrows():
            
            # if there's only one level in the index, row_idx will be a single
            # value, not an iterable.
            
            try:
                iter(row_idx)
            except TypeError:
                row_idx = [row_idx]
                
            for idx_i, idx in enumerate(row_idx):
                try:
                    text = "{:g}".format(idx)
                except (TypeError, ValueError):
                    text = idx
                
                t[row_i, idx_i] = text
                
            for col_i, col in enumerate(data.columns):
                t[row_i, len(names) + col_i] = row_data[col]
                
            row_i = row_i + 1
    
        np.savetxt(filename, t, delimiter = ",", fmt = "%s")
    
    
