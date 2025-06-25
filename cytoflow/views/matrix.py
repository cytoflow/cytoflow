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
"""

import math
from warnings import warn

from traits.api import provides, Enum, Str, Callable, Constant
import seaborn as sns
from natsort import natsorted
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import Grid, ImageGrid

import cytoflow
import cytoflow.utility as util

from .i_view import IView
from .base_views import BaseStatisticsView

@provides(IView)
class MatrixView(BaseStatisticsView):
    """
    A view that creates a matrix view (a 2D grid representation) of a statistic. 
    Set `statistic` to the name of the statistic to plot; set `feature` to the name
    of that statistic's feature you'd like to analyze.
    
    Setting `xfacet` and `yfacet` to levels of the statistic's index will result in
    a separate column or row for each value of that statistic.
    
    There are three different ways of plotting the values of the matrix view 
    (the "cells" in the matrix), controlled by the `type` parameter:
    
    * Setting `style` to ``heat`` (the default) will produce a "traditional" heat map, 
      where each "cell" is a circle and the color of the circle is related to the 
      intensity of the value of `feature`. (In this scenario, `variable` must be left empty.).
      
    * Setting `style` to ``pie`` will draw a pie plot in each cell. The values of `variable`
      are used as the categories of the pie, and the arc length of each slice of pie is related 
      to the intensity of the value of `feature`.
      
    * Setting `style` to ``petal`` will draw a "petal plot" in each cell. The values of `variable` 
      are used as the categories, but unlike a pie plot, the arc width of each slice
      is equal. Instead, the radius of the pie slice scales with the square root of
      the intensity, so that the relationship between area and intensity remains the same.
          
    Optionally, you can set `size_feature` to scale the circles' (or pies or petals)' area
    by another feature of the statistic. For example, you might scale the size of each
    circle by the number of events in some subset. For the ``heat`` style, this is 
    enough -- but for ``pie`` or ``petal`` plots, you need to *reduce* the feature
    (because there is only one pie plot, but there are multiple slices of the pie.)
    Set `size_function` to a callable that takes a `pandas.Series` as an argument and returns
    a ``float``.
    
    Attributes
    ----------
    
    variable : Str
        The variable used for plotting pie and petal plots. Must be left empty
        for a heatmap.
        
    feature : Str
        The column in the statistic to plot (often a channel name.)
        
    style : Enum(``heat``, ``pie``, ``petal``) (default = ``heat``)
        What kind of matrix plot to make?
        
    scale : {'linear', 'log', 'logicle'}
        How should the color, arc length, or radii be scaled before
        plotting?
        
    size_feature : String
        Which feature to use to scale the size of the circle/pie/petal?
        
    size_function : String
        If `size_feature` is set and `style` is ``pie`` or ``petal``, this function
        is used to reduce `size_feature` before scaling the pie plots. The function 
        should take a `pandas.Series` and return a ``float``. Often something like
        ``lambda x: x.sum()``.
        
    Note
    ----
    While `MatrixView` is a subclass of `BaseStatisticsView`, it does *not* call
    `BaseStatisticsView.plot`. This is because `MatrixView` does not use 
    `seaborn.FacetGrid` to lay out the subplots -- all the layout logic imposes 
    a *huge* overhead cost. Instead `MatrixView` uses classes from 
    `mpl_toolkits.axes_grid1` for its layout. It does use other functions in the
    superclass such as `enum_plots`.


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
    
    variable = Str
    feature = Str
    scale = util.ScaleEnum
    style = Enum("heat", "pie", "petal")
    huefacet = Constant("")   # can't facet by hue
    huescale = Constant("linear")   # can't facet by hue. use `scale`.
    
    size_feature = Str
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
            
        All other parameters are passed to `matplotlib.pyplot.pie`.

        """

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

        if plot_name is not None and not unused_names:
            raise util.CytoflowViewError('plot_name',
                                         "You specified a plot name, but all "
                                         "the facets are already used")
        
        if unused_names:
            groupby = data.groupby(unused_names, observed = True)

            if plot_name is None:
                raise util.CytoflowViewError('plot_name',
                                             "You must use facets {} in either the "
                                             "plot variables or the plot name. "
                                             "Possible plot names: {}"
                                             .format(unused_names, list(groupby.groups.keys())))

            if plot_name not in set(groupby.groups.keys()):
                raise util.CytoflowViewError('plot_name',
                                             "Plot {} not from plot_enum; must "
                                             "be one of {}"
                                             .format(plot_name, list(groupby.groups.keys())))
                
            data = groupby.get_group(plot_name if util.is_list_like(plot_name) else (plot_name,))
                
        if self.style != "heat" and self.variable not in stat.index.names:
            raise util.CytoflowViewError('variable',
                                         "Can't find variable '{}' in the statistic index."
                                         .format(self.variable))
        
        if self.size_feature and self.size_feature not in stat:
            raise util.CytoflowViewError('size_feature',
                                         "Feature {} not in statistic {}"
                                         .format(self.size_feature, self.statistic))
        
        data = data.reset_index()
        
        title = kwargs.pop("title", None)
        xlabel = kwargs.pop("xlabel", self.xfacet)       
        ylabel = kwargs.pop("ylabel", self.yfacet)

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
                
        rows = kwargs.pop("row_order", (natsorted(data[self.xfacet].unique()) if self.xfacet else []))
        cols = kwargs.pop("col_order", (natsorted(data[self.yfacet].unique()) if self.yfacet else []))

        # set up the range of the color map
        if 'norm' not in kwargs:
            data_scale = util.scale_factory(scale = self.scale,
                                            experiment = experiment,
                                            statistic = self.statistic,
                                            features = [self.feature])
            data_norm = data_scale.norm()
        else:
            data_norm = kwargs.pop('norm')
        
        group_keys = []
        group_keys += [self.xfacet] if self.xfacet else []
        group_keys += [self.yfacet] if self.yfacet else []
        
        groups = data.groupby(by = group_keys, observed = True)
        
        if self.style == "heat":
            cmap_name = kwargs.pop('palette', 'viridis')
            cmap = sns.color_palette(cmap_name, as_cmap = True)
            if isinstance(cmap, list):
                raise util.CytoflowViewError('palette',
                                             "{} is a qualitative (discrete) palette. Choose a continuous one such as 'rocket', 'mako' or 'viridis'")
            
            grid = ImageGrid(fig = plt.gcf(), 
                             rect = 111, 
                             nrows_ncols = (len(rows) if len(rows) > 0 else 1, 
                                            len(cols) if len(cols) > 0 else 1),
                             label_mode = "keep",
                             axes_pad = 0.0,
                             cbar_mode = "single",
                             cbar_pad = 0.1,
                             cbar_size = 0.15)
                    
            for idx, (_, group) in enumerate(groups):
                plt.sca(grid[idx])
                patches, _ = plt.pie([1], **kwargs)
                patches[0].set_facecolor(cmap(data_norm(group.reset_index().at[0, self.feature])))
                
            if legend:
                mpl.colorbar.Colorbar(grid[0].cax, 
                                      cmap = cmap, 
                                      norm = data_norm,
                                      label = legendlabel)

        elif self.style == "pie":
            palette_name = kwargs.pop('palette', 'deep')
                       
            # the context manager goes here because the color cycler is a
            # property of the axes 
            with sns.color_palette(palette_name):
                grid = ImageGrid(fig = plt.gcf(), 
                                 rect = 111, 
                                 nrows_ncols = (len(rows) if len(rows) > 0 else 1, 
                                                len(cols) if len(cols) > 0 else 1),
                                 label_mode = "keep",
                                 axes_pad = 0.0,
                                 cbar_mode = None)
            
            for idx, (_, group) in enumerate(groups):
                plt.sca(grid[idx])
                patches, _ = plt.pie(group[self.feature], **kwargs)
                
                for pi, patch in enumerate(patches):
                    patch.set_label(group.reset_index().at[pi, self.variable])
                
            if(legend):
                grid.axes_row[0][-1].legend(bbox_to_anchor = (1, 1), 
                                            title = self.feature)
            
        elif self.style == "petal":
            palette_name = kwargs.pop('palette', 'deep')
                       
            # the context manager goes here because the color cycler is a
            # property of the axes 
            with sns.color_palette(palette_name):
                grid = ImageGrid(fig = plt.gcf(), 
                                 rect = 111, 
                                 nrows_ncols = (len(rows) if len(rows) > 0 else 1, 
                                                len(cols) if len(cols) > 0 else 1),
                                 label_mode = "keep",
                                 axes_pad = 0.0,
                                 cbar_mode = None)
            
            for idx, (_, group) in enumerate(groups):
                plt.sca(grid[idx])
                patches, _ = plt.pie([1.0 / len(group[self.feature])] * len(group[self.feature]), **kwargs)
                
                for pi, patch in enumerate(patches):
                    patch.set_label(group.reset_index().at[pi, self.variable])
                    patch.set(radius = math.sqrt(group.reset_index().at[pi, self.feature] / group.reset_index()[self.feature].sum()))
                    
            if(legend):
                grid.axes_row[0][-1].legend(bbox_to_anchor = (1, 1), title = self.feature)
            
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
        
        if self.feature not in stat:
            raise util.CytoflowViewError('feature',
                                         "Can't find feature {} in statistic {}. "
                                         "Possible features: {}"
                                         .format(self.feature, self.statistic, stat.columns.to_list()))
                
        return stat
    
    def _get_facets(self, data):
        if self.variable:            
            if self.variable not in data.index.names:
                raise util.CytoflowViewError('variable',
                                             "Variable {} not found in the data. Must be one of {}"
                                             .format(self.variable, data.index.names))
                
            facets = super()._get_facets(data) + [self.variable]
        else:
            facets = super()._get_facets(data)
                    
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError(None, "Can't reuse facets")
        
        return facets
    

    # def _grid_plot(self, experiment, grid, **kwargs):
    #
    #     if self.size_feature and self.size_function:
    #         for _, group in grid.facet_data():
    #             try:
    #                 v = self.size_function(group[self.size_feature])
    #             except Exception as e:
    #                 raise util.CytoflowViewError(None,
    #                                            "Your function threw an error in group {}"
    #                                            .format(group)) from e
    #
    #             try:
    #                 v = float(v)
    #             except (TypeError, ValueError) as e:
    #                 raise util.CytoflowOpError(None,
    #                                            "Your function returned a {}. It must return "
    #                                            "a float or a value that can be cast to float."
    #                                            .format(type(v))) from e
    #
    #             grid.data.loc[group.index, '_scale'] = v
    #     elif self.size_feature:
    #         grid.data['_scale'] = grid.data[self.size_feature]
    #     else:
    #         grid.data['_scale'] = [1.0] * len(grid.data)
    #
    #     grid.data['_scale'] = grid.data['_scale'] / grid.data['_scale'].max()
    #
    #     if self.style == "heat":
    #         # set the default color map
    #         kwargs.setdefault('cmap', plt.get_cmap('viridis'))
    #
    #         # set up the range of the color map
    #         if 'norm' not in kwargs:
    #             hue_scale = util.scale_factory(scale = self.scale,
    #                                            experiment = experiment,
    #                                            statistic = self.statistic,
    #                                            features = [self.feature])
    #
    #             kwargs['norm'] = hue_scale.norm()
    #
    #         grid.map(_heat_plot, self.feature, '_scale', **kwargs)
    #
    #         return {"cmap" : kwargs['cmap'], 
    #                 "norm" : kwargs['norm']}
    #
    #     elif self.style == "pie":
    #         patches = {}
    #
    #         arc_scale = util.scale_factory(scale = self.scale,
    #                                        experiment = experiment,
    #                                        statistic = self.statistic,
    #                                        features = [self.feature])
    #
    #         kwargs['norm'] = arc_scale.norm()
    #
    #         grid.map(_pie_plot, self.feature, "_scale", patches = patches, **kwargs)
    #
    #         # legends only get added in BaseView.plot for hue facets, so we need to add one here.
    #         grid.add_legend(title = self.variable, 
    #                         legend_data = dict(zip(grid.data[self.variable].unique(),
    #                                                [plt.Rectangle((0, 0), 1, 1, fc = p.get_facecolor()) for p in patches[plt.gca()]])),
    #                         loc = 1)
    #
    #         return {}
    #
    #     elif self.style == "petal":
    #         patches = {}
    #         rad_scale = util.scale_factory(scale = self.scale,
    #                                        experiment = experiment,
    #                                        statistic = self.statistic,
    #                                        features = [self.feature])
    #
    #         kwargs['norm'] = rad_scale.norm()
    #         grid.map(_petal_plot, self.feature, "_scale", patches = patches, **kwargs)
    #
    #         # legends only get added in BaseView.plot for hue facets, so we need to add one here.
    #         grid.add_legend(title = self.variable, 
    #                         legend_data = dict(zip(grid.data[self.variable].unique(),
    #                                                [plt.Rectangle((0, 0), 1, 1, fc = p.get_facecolor()) for p in patches[plt.gca()]])),
    #                         loc = 1)
    #
    #         return {}


# def _heat_plot(data, size, color = None, **kws):
#     cmap = kws.pop('cmap')
#     norm = kws.pop('norm')
#
#     pie_patches, _ = plt.pie(data, **kws)
#
#     pie_patches[0].set_facecolor(cmap(norm(data.iat[0])))
#     pie_patches[0].set(radius = size.iat[0])       


#
# def _pie_plot(data, size, patches, color = None, **kws):
#     norm = kws.pop('norm')
#     pie_patches, _ = plt.pie(data, **kws)
#     for patch in pie_patches:
#         patch.set(radius = norm(size.iat[0]))
#
#     patches[plt.gca()] = pie_patches

# def _petal_plot(data, patches, color = None, **kws):  
#
#     norm = kws.pop('norm')
#     pie_patches, _ = plt.pie([1.0 / len(data)] * len(data), **kws)
#     for i, p in enumerate(pie_patches):
#         p.set(radius = math.sqrt(p.r * norm(data.iat[i])))
#
#     patches[plt.gca()] = pie_patches        

util.expand_class_attributes(MatrixView)

    

        