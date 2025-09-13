#!/usr/bin/env python3.11
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2025
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
cytoflow.views.matrix
---------------------

Plots a "matrix" view -- a 2D representation of a heat map, pie plots, or 
petal plots.

`MatrixView` -- plots the matrix view.
"""

import math
from warnings import warn
from natsort import natsorted

from traits.api import HasStrictTraits, provides, Enum, Str, Constant, Callable
import seaborn as sns
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid

import cytoflow
import cytoflow.utility as util

from .i_view import IView

@provides(IView)
class MatrixView(HasStrictTraits):
    """
    A view that creates a matrix view (a 2D grid representation) of a statistic. 
    Set `statistic` to the name of the statistic to plot; set `feature` to the name
    of that statistic's feature you'd like to analyze.
    
    Setting `xfacet` and `yfacet` to levels of the statistic's index will result in
    a separate column or row for each value of that statistic.
    
    There are three different ways of plotting the values of the matrix view 
    (the "cells" in the matrix), controlled by the `type` parameter:
    
    * Setting `style` to ``heat`` (the default) will produce a "traditional" 
      heat map, where each "cell" is a circle and the color of the circle is 
      related to the intensity of the value of `feature`. (In this scenario, 
      `variable` is ignored.)
      
    * Setting `style` to ``pie`` will draw a pie plot in each cell. If `variable`
      is set, then the values of `variable` are used as the categories of the 
      pie, and the arc length of each slice of pie is related to the intensity 
      of the value of `feature`. If `variable` is not set, however, `feature`
      is ignored and the *features* of the statistic become the categories. In
      this case, *all* of the statistic index levels must be either used in
      the view facets or specified in `plot_name`.
      
    * Setting `style` to ``petal`` will draw a "petal plot" in each cell. If 
      `variable` is set, then the values of `variable` are used as the categories, 
      but unlike a pie plot, the arc width of each slice is equal. Instead, the 
      radius of the pie slice scales with the square root of the intensity, so 
      that the relationship between area and intensity remains the same.
      If `variable` is not set, however, `feature` is ignored and the *features*
      of the statistic become the categories. In this case, *all* of the statistic
      index levels must be either used in the view facets or set on `plot_name`.
      
    .. warning::
        If `style` is ``pie`` or ``petal``, then negative data will be clipped
        to 0! 
        
    Optionally, you can set `size_function` to scale the circles (or pies or petals)
    by a function computed on `Experiment.data`. (Often set to ``len`` to scale 
    by the number of events in each subset.)
    
    Attributes
    ----------
    
    statistic : Str
        The statistic to plot. Must be a key in `Experiment.statistics`.
    
    xfacet : String
        Set to one of the index levels in the statistic being plotted, and 
        a new column of subplots will be added for every unique value
        of that index level.
        
    yfacet : String
        Set to one of the index levels in the statistic being plotted, and 
        a new row of subplots will be added for every unique value
        of that index level.
    
    variable : Str
        The variable (index level) used for plotting pie and petal plots. Ignored 
        for a heatmap. If unset, use the statistic features as categories. 
        
    feature : Str
        The column in the statistic to plot (often a channel name.) Ignored if
        `variable` is left unset.
        
    style : Enum(``heat``, ``pie``, ``petal``) (default = ``heat``)
        What kind of matrix plot to make?
        
    scale : Enum(``linear``, ``log``, ``logicle``} (default = ``linear``)
        For a heat map, how should the color of `feature` be scaled before 
        plotting? If `style` is not ``heat``, `scale` *must* be ``linear``.
        
    size_function : Callable
        If set, separate the `Experiment` into subsets by `xfacet` and `yfacet` 
        (which should be conditions in the `Experiment`), compute a function on
        them, and scale the size of each matrix cell by those values. The 
        callable should take a single `pandas.DataFrame` argument and return a 
        *positive* ``float`` or value that can be cast to ``float`` (such as 
        ``int``).  Of particular use is ``len``, which will scale the cells 
        by the number of events in each subset.
        
    subset : Str
        Only plot a subset of the data in `statistic`. Passed directly to 
        `pandas.DataFrame.query`.
        
    Note
    ----
    `MatrixView` implements the `IView` interface, but it is NOT a subclass 
    `BaseStatisticsView`. This is because `MatrixView` does not use 
    `seaborn.FacetGrid` to lay out the subplots -- all the layout logic imposes 
    a *huge* overhead cost. Instead `MatrixView` uses classes from 
    `mpl_toolkits.axes_grid1` for its layout.


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
    
    Plot the bar chart
    
    .. plot::
        :context: close-figs
        
        >>> flow.MatrixView(statistic = "ByDox",
        ...                 xfacet = 'Dox',
        ...                 variable = 'Threshold',
        ...                 feature = 'Y2-A',
        ...                 style = 'pie').plot(ex3)
        
    """
    
    id = Constant("cytoflow.view.matrix")
    friendly_id = Constant("Matrix Chart") 
    
    statistic = Str
    subset = Str
    xfacet = Str
    yfacet = Str
    variable = Str
    feature = Str
    scale = util.ScaleEnum
    style = Enum("heat", "pie", "petal")
    size_function = Callable

    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot a chart of a variable's values against a statistic.
        
        Parameters
        ----------
        experiment: Experiment
            The `Experiment` to plot using this view.
            
        plot_name : str
            If this `IView` can make multiple plots, ``plot_name`` is
            the name of the plot to make.  Must be one of the values retrieved
            from `enum_plots`.
            
        title : str
            Set the plot title
            
        xlabel : str
            Set the X axis label
        
        ylabel : str
            Set the Y axis label
            
        legend : bool
            Plot a legend or color bar?  Defaults to `True`.
            
        legendlabel : str
            Set the label for the color bar or legend
 
        palette : palette name
            Colors to use for the different levels of the hue variable. 
            Should be something that can be interpreted by
            `seaborn.color_palette`. If plotting a heat map, this should be
            a continuous color map ('viridis' is the default.) Otherwise,
            choose either a discrete color map ('deep' is the default) or
            a continuous color map from which equi-spaced colors will be drawn.
            
        All other parameters are passed to the ``wedgeprops`` argument of 
        `matplotlib.axes.Axes.pie` -- ie, they should be matplotlib patch
        properties.

        """

        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
            
        if not self.statistic:
            raise util.CytoflowViewError('statistic',
                                         "Must set a statistic to plot")
            
        if not self.xfacet and not self.yfacet:
            raise util.CytoflowViewError('xfacet',
                                         "At least one of 'xfacet' and 'yfacet' must be set.")
 
        stat = self._get_stat(experiment)
        data = self._subset_data(stat)
        facets = self._get_facets(data)
        experiment_data = experiment.data

        unused_names = list(set(data.index.names) - set(facets))

        if plot_name is not None and not unused_names:
            raise util.CytoflowViewError('plot_name',
                                         "You specified a plot name, but all "
                                         "the statistic's levels are already used")
        
        if unused_names:
            groupby = data.groupby(level = unused_names, observed = True)

            if plot_name is None:
                raise util.CytoflowViewError('plot_name',
                                             "You must use facets {} in either the "
                                             "plot variables or the plot name. "
                                             "Possible plot names: {}"
                                             .format(unused_names, list(groupby.groups.keys())))

            if plot_name not in set(groupby.groups.keys()):
                raise util.CytoflowViewError('plot_name',
                                             "plot_name must be one of {}"
                                             .format(list(groupby.groups.keys())))
                
            data = groupby.get_group(plot_name if util.is_list_like(plot_name) else (plot_name,))
            
            if self.size_function:
                experiment_data = experiment.data.groupby(by = unused_names, observed = True).get_group(plot_name if util.is_list_like(plot_name) else (plot_name,))
        
        if self.style == "heat":
            if not self.feature:
                raise util.CytoflowViewError('feature',
                                         "For style 'heat', you must set 'feature'!")
            
            if self.feature not in data.columns:
                raise util.CytoflowViewError('feature',
                                             "Can't find feature '{}' in the statistic columns."
                                             .format(self.feature))
            
        else:
            if self.variable and self.variable not in stat.index.names:
                raise util.CytoflowViewError('variable',
                                             "Can't find variable '{}' in the statistic index."
                                             .format(self.variable))
            
            if self.variable and not self.feature:
                raise util.CytoflowViewError('feature',
                                             "For styles 'pie' and 'petal', if you set 'variable', you must set 'feature'!"
                                             .format(self.variable))
                
            if self.variable and self.feature not in data.columns:
                raise util.CytoflowViewError('feature',
                                             "Can't find feature '{}' in the statistic columns."
                                             .format(self.feature))
        
        title = kwargs.pop("title", None)
        xlabel = kwargs.pop("xlabel", self.yfacet)       
        ylabel = kwargs.pop("ylabel", self.xfacet)

        legend = kwargs.pop('legend', True)
        legendlabel = kwargs.pop('legendlabel', self.feature)
                
        if cytoflow.RUNNING_IN_GUI:
            sns_style = kwargs.pop('sns_style', 'whitegrid')
            sns_context = kwargs.pop('sns_context', 'notebook')
            sns.set_style(sns_style)
            sns.set_context(sns_context)
        else:
            if 'sns_style' in kwargs:
                kwargs.pop('sns_style')
                warn("'sns_style' is ignored when not running in the GUI. Feel free to change the seaborn global settings.",
                     util.CytoflowViewWarning)
                
            if 'sns_context' in kwargs:
                kwargs.pop('sns_context')
                warn("'sns_context' is ignored when not running in the GUI. Feel free to change the seaborn global settings.",
                     util.CytoflowViewWarning)
                
        index = data.index.remove_unused_levels()
        rows = kwargs.pop("row_order", (index.levels[index.names.index(self.xfacet)].to_list() if self.xfacet else []))
        cols = kwargs.pop("col_order", (index.levels[index.names.index(self.yfacet)].to_list() if self.yfacet else []))

        # set up the data normalizer
        if 'norm' not in kwargs:
            data_scale = util.scale_factory(scale = self.scale,
                                            experiment = experiment,
                                            statistic = self.statistic,
                                            features = [self.feature] 
                                                       if self.variable 
                                                       else list(data.columns))
            data_norm = data_scale.norm()
        else:
            data_norm = kwargs.pop('norm')
                    
        group_keys = []
        group_keys += [self.xfacet] if self.xfacet else []
        group_keys += [self.yfacet] if self.yfacet else []
        if len(group_keys) == 1:
            group_keys = group_keys[0]
        else:
            # gotta sort the group keys to be the same as the index levels
            group_keys = sorted(group_keys, key = lambda k: data.index.names.index(k))
    
        groups = data.groupby(level = group_keys, observed = True)
        
        if self.size_function:
            group_scale = {}
            s_max = 0.0
            for group_name, group in experiment_data.groupby(by = group_keys, observed = True):
                s = self.size_function(group)
                try:
                    s = float(s)
                except Exception as e:
                    raise util.CytoflowViewError('size_function',
                                                 'Called size_function on group {} and return type was {}; must return a float!'
                                                 .format(group_name, type(s))) from e
                                                 
                if s < 0.0:
                    raise util.CytoflowViewError('size_function',
                                                 'Called size_function on group {} and return was {}; must be >0!'
                                                 .format(group_name, s))
                if s > s_max:
                    s_max = s
                group_scale[group_name] = s
                
            
            group_scale = {k : v / s_max for k, v in group_scale.items()}
            
        # make a new figure. This usually happens in seaborn.FacetGrid
        fig = plt.figure(layout = 'none')
        
        if self.style == "heat":
            cmap_name = kwargs.pop('palette', 'viridis')
            cmap = sns.color_palette(cmap_name, as_cmap = True)
            if isinstance(cmap, list):
                raise util.CytoflowViewError('palette',
                                             "{} is a qualitative (discrete) palette. Choose a continuous one such as 'rocket', 'mako' or 'viridis'")
            
            grid = ImageGrid(fig = fig, 
                             rect = 111, 
                             nrows_ncols = (len(rows) if len(rows) > 0 else 1, 
                                            len(cols) if len(cols) > 0 else 1),
                             label_mode = "keep",
                             axes_pad = 0.0,
                             cbar_mode = "single",
                             cbar_pad = 0.1,
                             cbar_size = 0.15)
                    
            for group_name, group in groups:
                if not self.xfacet:
                    # only yfacet -- ie, one row
                    row_idx = 0
                    col_idx = cols.index(group_name)
                elif not self.yfacet:
                    # only xfacet -- ie, one column
                    row_idx = rows.index(group_name)
                    col_idx = 0
                else:
                    # can't depend on the order of row, column
                    row_name = next(filter(lambda x: x in rows, group_name))
                    row_idx = rows.index(row_name)
                    col_name = next(filter(lambda x: x in cols, group_name))
                    col_idx = cols.index(col_name)
                    
                plt.sca(grid.axes_row[row_idx][col_idx])
                patches, _ = plt.pie([1], wedgeprops = kwargs)
                patches[0].set_facecolor(cmap(data_norm(group.iloc[0][self.feature])))
                
                if self.size_function:
                    patches[0].set_radius(patches[0].r * group_scale[group_name])
                
            if legend:
                mpl.colorbar.Colorbar(grid[0].cax, 
                                      cmap = cmap, 
                                      norm = data_norm,
                                      label = legendlabel)
                
            for ax in grid:
                if not ax.has_data():
                    ax.set_frame_on(False)

        elif self.style == "pie":

            grid = ImageGrid(fig = fig, 
                             rect = 111, 
                             nrows_ncols = (len(rows) if len(rows) > 0 else 1, 
                                            len(cols) if len(cols) > 0 else 1),
                             label_mode = "keep",
                             axes_pad = 0.0,
                             cbar_mode = None)
                
            if self.variable:
                variable_values = list(data.index.get_level_values(self.variable).unique())
            else:
                variable_values = list(data.columns)
            palette_name = kwargs.pop('palette', 'deep')
            palette = sns.color_palette(palette_name, n_colors = len(variable_values))
            colors = {var : palette[vi] for vi, var in enumerate(variable_values)}
            legend_artists = {}
            
            for group_name, group_data in groups:
                if not self.xfacet:
                    # only yfacet -- ie, one row
                    row_idx = 0
                    col_idx = cols.index(group_name)
                elif not self.yfacet:
                    # only xfacet -- ie, one column
                    row_idx = rows.index(group_name)
                    col_idx = 0
                else:
                    # can't depend on the order of row, column
                    row_name = next(filter(lambda x: x in rows, group_name))
                    row_idx = rows.index(row_name)
                    col_name = next(filter(lambda x: x in cols, group_name))
                    col_idx = cols.index(col_name)
                    
                if self.variable:
                    pie_data = group_data[self.feature]
                else:
                    assert(len(group_data) == 1)
                    pie_data = group_data.iloc[0]
                normed_data = data_norm(pie_data)
                
                plt.sca(grid.axes_row[row_idx][col_idx])
                patches, _ = plt.pie(normed_data, 
                                     counterclock = False,
                                     startangle = 90,
                                     wedgeprops = kwargs)
                
                for pi, patch in enumerate(patches):
                    if self.variable:
                        label = group_data.index.get_level_values(self.variable)[pi]
                    else:
                        label = pie_data.index.values[pi]
                    color = colors[label]
                    patch.set(label = label, facecolor = color)
                    if label not in legend_artists:
                        legend_artists[label] = patch
                    if self.size_function:
                        patch.set_radius(patch.r * group_scale[group_name])
                
            if(legend):
                legend_artists = {k: legend_artists[k] for k in natsorted(legend_artists.keys())}
                grid.axes_row[0][-1].legend(handles = legend_artists.values(),
                                            bbox_to_anchor = (1, 1), 
                                            loc = "upper left",
                                            title = legendlabel)
                
            for ax in grid:
                if not ax.has_data():
                    ax.set_frame_on(False)
            
        elif self.style == "petal":
            
            grid = ImageGrid(fig = fig, 
                             rect = 111, 
                             nrows_ncols = (len(rows) if len(rows) > 0 else 1, 
                                            len(cols) if len(cols) > 0 else 1),
                             label_mode = "keep",
                             axes_pad = 0.0,
                             cbar_mode = None)
                
            if self.variable:
                variable_values = list(data.index.get_level_values(self.variable).unique())
            else:
                variable_values = list(data.columns)
                
            palette_name = kwargs.pop('palette', 'deep')
            palette = sns.color_palette(palette_name, n_colors = len(variable_values))
            
            legend_artists = {}

            for group_name, group in groups:
                if not self.xfacet:
                    # only yfacet -- ie, one row
                    row_idx = 0
                    col_idx = cols.index(group_name)
                elif not self.yfacet:
                    # only xfacet -- ie, one column
                    row_idx = rows.index(group_name)
                    col_idx = 0
                else:
                    # can't depend on the order of row, column
                    row_name = next(filter(lambda x: x in rows, group_name))
                    row_idx = rows.index(row_name)
                    col_name = next(filter(lambda x: x in cols, group_name))
                    col_idx = cols.index(col_name)
                    
                plt.sca(grid.axes_row[row_idx][col_idx])
                patches, _ = plt.pie([1.0 / len(variable_values)] * len(variable_values), 
                                     counterclock = False,
                                     startangle = 90,
                                     wedgeprops = kwargs)
                
                if self.variable:
                    group = group.set_index(group.index.droplevel(group_keys))
                else:
                    assert(len(group) == 1)
                    group = group.iloc[0]
                    
                for pi, patch in enumerate(patches):
                    label = variable_values[pi]
                    color = palette[pi]
                    
                    if label not in group.index:
                        value = 0
                    elif self.variable:
                        value = group.loc[label, self.feature]
                        value = data_norm(value)
                    else:
                        value = group.loc[label]
                        value = data_norm(value)
                    
                    radius = math.sqrt(value)
                    if self.size_function:
                        radius *= group_scale[group_name]
                        
                    patch.set(label = label, radius = radius, facecolor = color)

                    if label not in legend_artists:
                        legend_artists[label] = patch

            if(legend):
                legend_artists = {k: legend_artists[k] for k in natsorted(legend_artists.keys())}
                grid.axes_row[0][-1].legend(handles = legend_artists.values(),
                                            bbox_to_anchor = (1, 1), 
                                            loc = "upper left",
                                            title = legendlabel)
                
            for ax in grid:
                if not ax.has_data():
                    ax.set_frame_on(False)
            
        if self.yfacet:
            for i, ax in enumerate(grid.axes_row[0]):
                ax.xaxis.set_label_text(cols[i])
                ax.xaxis.set_label_position("top")
                ax.xaxis.label.set(size = 'small')
        
        if self.xfacet:
            for i, ax in enumerate(grid.axes_column[0]):
                ax.yaxis.set_label_text(rows[i])
                ax.yaxis.label.set(rotation = 'horizontal', 
                                   horizontalalignment = 'right', 
                                   verticalalignment = 'center',
                                   size = 'small')

        # x and y in supxlabel and supylabel are in figure units, but we dont
        # know the size of the figure (with the labels) until we draw it!            
        plt.gcf().draw_without_rendering()
        
        max_y = 0.0
        for i, ax in enumerate(grid.axes_row[0]):
            bbox = ax.xaxis.label.get_window_extent(renderer = plt.gcf().canvas.get_renderer())
            bbox = plt.gcf().transFigure.inverted().transform_bbox(bbox)
            if bbox.y1 > max_y:
                max_y = bbox.y1
        
        plt.gcf().supxlabel(xlabel, y = max_y + 0.01)
        
        min_x = 1.0
        for i, ax in enumerate(grid.axes_column[0]):        
            bbox = ax.yaxis.label.get_window_extent(renderer = plt.gcf().canvas.get_renderer())
            bbox = plt.gcf().transFigure.inverted().transform_bbox(bbox)
            if bbox.x0 < min_x:
                min_x = bbox.x0
        
        plt.gcf().supylabel(ylabel, x = min_x - 0.04)
        
        if title:
            plt.suptitle(title, y = 1.02)
            
    def enum_plots(self, experiment):
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
            
        if not self.xfacet and not self.yfacet:
            raise util.CytoflowViewError('xfacet',
                                         "At least one of 'xfacet' and 'yfacet' must be set.")

        if self.style == "heat" and self.variable != "":
            raise util.CytoflowViewError("variable",
                                         "If `style` is \"heat\", `variable` must be empty!")
                        
        stat = self._get_stat(experiment)
        data = self._subset_data(stat)
        facets = self._get_facets(data)

        unused_names = list(set(data.index.names) - set(facets))      
        
        class plot_iter(object):
            
            def __init__(self, data, by):
                self.by = by
                self._iter = None
                self._returned = False
                
                if by:
                    self._iter = data.groupby(level = by, observed = True).groups.keys().__iter__()
                
            def __iter__(self):
                return self
            
            def __next__(self):
                if self._iter:
                    return next(self._iter)
                else:
                    if self._returned:
                        raise StopIteration
                    else:
                        self._returned = True
                        return None
            
        return plot_iter(data, unused_names)

    def _get_stat(self, experiment):
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.statistic:
            raise util.CytoflowViewError('statistic', "Statistic not set")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic',
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
            
        stat = experiment.statistics[self.statistic]

        return stat
    
    def _get_facets(self, data):
        if self.xfacet and self.xfacet not in data.index.names:
            raise util.CytoflowViewError('xfacet',
                                         "X facet {} not in statistics; must be one of {}"
                                         .format(self.xfacet, data.index.names))

        
        if self.yfacet and self.yfacet not in data.index.names:
            raise util.CytoflowViewError('yfacet',
                                         "Y facet {} not in statistics; must be one of {}"
                                         .format(self.yfacet, data.index.names))
            
        facets = [x for x in [self.xfacet, self.yfacet] if x]

        if self.variable:            
            if self.variable not in data.index.names:
                raise util.CytoflowViewError('variable',
                                             "Variable {} not found in the data. Must be one of {}"
                                             .format(self.variable, data.index.names))
                
            facets = facets + [self.variable]    

        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError(None, "Can't reuse facets")
        
        return facets
    
    def _subset_data(self, data):
        
        if self.subset:
            try:
                # TODO - either sanitize column names, or check to see that
                # all conditions are valid Python variables
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
                                                 
        # droplevel makes this a plain Index instead of a MultiIndex. no bueno.
        if not isinstance(data.index, pd.MultiIndex):
            data.index = pd.MultiIndex.from_tuples([(x,) for x in data.index.to_list()], 
                                                   names = [data.index.name])

        return data
    
    

    

        