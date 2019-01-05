#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
2D Statistics Plot
------------------

Plot two statistics on a scatter plot.  A point (X,Y) is drawn for every
pair of elements with the same value of **Variable**; the X value is from 
** X statistic** and the Y value is from **Y statistic**.

.. object:: X Statistic

    Which statistic to plot on the X axis.

.. object:: Y Statistic

    Which statistic to plot on the Y axis.  Must have the same indices as
    **X Statistic**.

.. object:: X Scale, Y Scale

    How to scale the X and Y axes.
    
.. object:: Variable

    The statistic variable to put on the plot.

.. object:: Horizontal Facet

    Make muliple plots, with each column representing a subset of the statistic
    with a different value for this variable.
        
.. object:: Vertical Facet

    Make multiple plots, with each row representing a subset of the statistic
    with a different value for this variable.
    
.. object:: Color Facet

    Make lines on the plot with different colors; each color represents a subset
    of the statistic with a different value for this variable.
    
.. object:: Color Scale

    If **Color Facet** is a numeric variable, use this scale for the color
    bar.
    
.. object:: X Error Statistic

    A statistic to use to make error bars in the X direction.  Must have the 
    same indices as the statistic in **X Statistic**.

.. object:: Y Error Statistic

    A statistic to use to make error bars in the Y direction.  Must have the 
    same indices as the statistic in **Y Statistic**.
    
.. object:: Subset

    Plot only a subset of the statistic.

.. plot::

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()

    ch_op = flow.ChannelStatisticOp(name = 'MeanByDox',
                        channel = 'Y2-A',
                        function = flow.geom_mean,
                        by = ['Dox'])
    ex2 = ch_op.apply(ex)
    ch_op_2 = flow.ChannelStatisticOp(name = 'SdByDox',
                          channel = 'Y2-A',
                          function = flow.geom_sd,
                          by = ['Dox'])
    ex3 = ch_op_2.apply(ex2)
    
    flow.Stats2DView(variable = 'Dox',
                     xstatistic = ('MeanByDox', 'geom_mean'),
                     xscale = 'log',
                     ystatistic = ('SdByDox', 'geom_sd'),
                     yscale = 'log').plot(ex3)
"""

import pandas as pd

from traits.api import provides, Callable, Property, Enum, Instance
from traitsui.api import View, Item, Controller, EnumEditor, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import Stats2DView
import cytoflow.utility as util

from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import (IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin, 
            PluginHelpMixin, Stats2DPlotParams)
from cytoflowgui.view_plugins.scatterplot import SCATTERPLOT_MARKERS
from cytoflowgui.view_plugins.stats_1d import LINE_STYLES
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent

Stats2DView.__repr__ = traits_repr
    
class Stats2DHandler(ViewHandlerMixin, Controller):

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
        
        try:
            ystat.index = ystat.index.reorder_levels(xstat.index.names)
            ystat.sort_index(inplace = True)
        except AttributeError:
            pass
        
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
        
        try:
            ystat.index = ystat.index.reorder_levels(xstat.index.names)
            ystat.sort_index(inplace = True)
        except AttributeError:
            pass
        
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
            return {}
        
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
    
class Stats2DPluginPlotParams(Stats2DPlotParams):

    linestyle = Enum(LINE_STYLES)
    marker = Enum(SCATTERPLOT_MARKERS)
    markersize = util.PositiveCFloat(6, allow_zero = False)
    capsize = util.PositiveCFloat(None, allow_none = True, allow_zero = False)
    alpha = util.PositiveCFloat(1.0)
    
    def default_traits_view(self):
        base_view = Stats2DPlotParams.default_traits_view(self)
        
        return View(Item('linestyle'),
                    Item('marker'),
                    Item('markersize',
                         editor = TextEditor(auto_set = False),
                         format_func = lambda x: "" if x == None else str(x)),
                    Item('capsize',
                         editor = TextEditor(auto_set = False),
                         format_func = lambda x: "" if x == None else str(x)),
                    Item('alpha'),
                    base_view.content)

    
class Stats2DPluginView(PluginViewMixin, Stats2DView):
    handler_factory = Callable(Stats2DHandler)
    plot_params = Instance(Stats2DPluginPlotParams, ())
    
    def get_notebook_code(self, idx):
        view = Stats2DView()
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        {repr}.plot(ex_{idx}{plot}{plot_params})
        """
        .format(repr = repr(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.plot_names else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))

@provides(IViewPlugin)
class Stats2DPlugin(Plugin, PluginHelpMixin):

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
    
### Serialization

@camel_registry.dumper(Stats2DPluginView, 'stats-2d', version = 2)
def _dump(view):
    return dict(xstatistic = view.xstatistic,
                xscale = view.xscale,
                ystatistic = view.ystatistic,
                yscale = view.yscale,
                variable = view.variable,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                x_error_statistic = view.x_error_statistic,
                y_error_statistic = view.y_error_statistic,
                subset_list = view.subset_list,
                plot_params = view.plot_params)
    
@camel_registry.dumper(Stats2DPluginView, 'stats-2d', version = 1)
def _dump_v1(view):
    return dict(xstatistic = view.xstatistic,
                xscale = view.xscale,
                ystatistic = view.ystatistic,
                yscale = view.yscale,
                variable = view.variable,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                x_error_statistic = view.x_error_statistic,
                y_error_statistic = view.y_error_statistic,
                subset_list = view.subset_list)


@camel_registry.loader('stats-2d', version = any)
def _load(data, version):
    data['xstatistic'] = tuple(data['xstatistic'])
    data['ystatistic'] = tuple(data['ystatistic'])
    data['x_error_statistic'] = tuple(data['x_error_statistic'])
    data['y_error_statistic'] = tuple(data['y_error_statistic'])

    return Stats2DPluginView(**data)

@camel_registry.dumper(Stats2DPluginPlotParams, 'stats-2d-params', version = 1)
def _dump_params(params):
    return dict(
                # BasePlotParams
                title = params.title,
                xlabel = params.xlabel,
                ylabel = params.ylabel,
                huelabel = params.huelabel,
                col_wrap = params.col_wrap,
                sns_style = params.sns_style,
                sns_context = params.sns_context,
                legend = params.legend,
                sharex = params.sharex,
                sharey = params.sharey,
                despine = params.despine,
                
                # Base2DStatisticsView
                xlim = params.xlim,
                ylim = params.ylim,
                
                # Stats 2D View
                linestyle = params.linestyle,
                marker = params.marker,
                markersize = params.markersize,
                capsize = params.capsize,
                alpha = params.alpha)

@camel_registry.loader('stats-2d-params', version = any)
def _load_params(data, version):
    return Stats2DPluginPlotParams(**data)