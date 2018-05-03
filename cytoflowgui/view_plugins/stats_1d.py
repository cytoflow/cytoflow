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
1D Statistics Plot
------------------

Plots a line plot of a statistic.

Each variable in the statistic (ie, each variable chosen in the statistic
operation's **Group By**) must be set as **Variable** or as a facet.

.. object:: Statistic

    Which statistic to plot.
    
.. object:: Variable

    The statistic variable put on the X axis.  Must be numeric.
    
.. object:: X Scale, Y Scale

    How to scale the X and Y axes.
    
.. object:: Horizontal Facet

    Make muliple plots, with each column representing a subset of the statistic
    with a different value for this variable.
        
.. object:: Vertical Facet

    Make multiple plots, with each row representing a subset of the statistic
    with a different value for this variable.
    
.. object:: Hue Facet

    Make multiple bars with different colors; each color represents a subset
    of the statistic with a different value for this variable.
    
.. object:: Color Scale

    If **Color Facet** is a numeric variable, use this scale for the color
    bar.
    
.. object:: Error Statistic

    A statistic to use to make the error bars.  Must have the same variables
    as the statistic in **Statistic**.
    
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
    
    flow.Stats1DView(variable = 'Dox',
                     statistic = ('MeanByDox', 'geom_mean'),
                     scale = 'log',
                     variable_scale = 'log').plot(ex2)
"""

from traits.api import provides, Callable, Property, Enum, Instance, Tuple, Bool
from traitsui.api import View, Item, Controller, EnumEditor, VGroup, TextEditor, TupleEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

import pandas as pd

from cytoflow import Stats1DView
import cytoflow.utility as util

from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import (IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin, 
            PluginHelpMixin, Stats1DPlotParams)
from cytoflowgui.view_plugins.scatterplot import SCATTERPLOT_MARKERS
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent

Stats1DView.__repr__ = traits_repr

LINE_STYLES = ["solid", "dashed", "dashdot", "dotted", "none"]
    
class Stats1DHandler(ViewHandlerMixin, Controller):

    indices = Property(depends_on = "context.statistics, model.statistic, model.subset")
    numeric_indices = Property(depends_on = "context.statistics, model.statistic, model.subset")
    levels = Property(depends_on = "context.statistics, model.statistic")
    
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('statistic',
                                editor=EnumEditor(name='handler.numeric_statistics_names'),
                                label = "Statistic"),
                           Item('scale', label = "Statistic\nScale"),
                           Item('variable',
                                editor = EnumEditor(name = 'handler.numeric_indices')),
                           Item('variable_scale', label = "Variable\nScale"),
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
                                label="Hue\nFacet"),
                           Item('huescale', 
                                label = "Hue\nScale"),
                           Item('error_statistic',
                                editor=ExtendableEnumEditor(name='handler.statistics_names',
                                                            extra_items = {"None" : ("", "")}),
                                label = "Error\nStatistic"),
                           label = "One-Dimensional Statistics Plot",
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
                and self.model.statistic in self.context.statistics):
            return []
        
        stat = self.context.statistics[self.model.statistic]
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
    
    # MAGIC: gets the value for the property 'levels'
    # returns a Dict(Str, pd.Series)
    
    def _get_levels(self):        
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return []
        
        stat = self.context.statistics[self.model.statistic]
        index = stat.index
        
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
        
    # MAGIC: gets the value for the property numeric_indices
    def _get_numeric_indices(self):        
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return []
        
        stat = self.context.statistics[self.model.statistic]
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
    
class Stats1DPluginPlotParams(Stats1DPlotParams):

    variable_lim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    linestyle = Enum(LINE_STYLES)
    marker = Enum(SCATTERPLOT_MARKERS)
    markersize = util.PositiveCFloat(6, allow_zero = False)
    capsize = util.PositiveCFloat(0, allow_zero = True)
    alpha = util.PositiveCFloat(1.0)
    shade_error = Bool(False)
    shade_alpha = util.PositiveCFloat(0.2)
    
    def default_traits_view(self):
        base_view = Stats1DPlotParams.default_traits_view(self)
        
        return View(Item('variable_lim',
                         label = "Variable\nLimits",
                         editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                                    evaluate = float,
                                                                    format_func = lambda x: "" if x == None else str(x)),
                                                         TextEditor(auto_set = False,
                                                                    evaluate = float,
                                                                    format_func = lambda x: "" if x == None else str(x))],
                                              labels = ["Min", "Max"],
                                              cols = 1)),
                    Item('linestyle'),
                    Item('marker'),
                    Item('markersize',
                         editor = TextEditor(auto_set = False),
                         format_func = lambda x: "" if x == None else str(x)),
                    Item('capsize',
                         editor = TextEditor(auto_set = False),
                         format_func = lambda x: "" if x == None else str(x)),
                    Item('alpha'),
                    Item('shade_error'),
                    Item('shade_alpha'),
                    base_view.content)

class Stats1DPluginView(PluginViewMixin, Stats1DView):
    handler_factory = Callable(Stats1DHandler)
    plot_params = Instance(Stats1DPluginPlotParams, ())
    
    def get_notebook_code(self, idx):
        view = Stats1DView()
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
class Stats1DPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.view.stats1d'
    view_id = 'edu.mit.synbio.cytoflow.view.stats1d'
    short_name = "1D Statistics View"
    
    def get_view(self):
        return Stats1DPluginView()

    def get_icon(self):
        return ImageResource('stats_1d')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

### Serialization

@camel_registry.dumper(Stats1DPluginView, 'stats-1d', version = 2)
def _dump(view):
    return dict(statistic = view.statistic,
                variable = view.variable,
                scale = view.scale,
                variable_scale = view.variable_scale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                error_statistic = view.error_statistic,
                subset_list = view.subset_list,
                plot_params = view.plot_params)
    
@camel_registry.loader('stats-1d', version = 1)
def _load_v1(data, version):

    xscale = data.pop('xscale')
    yscale = data.pop('yscale')
    
    data['statistic'] = tuple(data['statistic'])
    data['error_statistic'] = tuple(data['error_statistic'])

    return Stats1DPluginView(scale = yscale,
                             variable_scale = xscale,
                             **data)

@camel_registry.loader('stats-1d', version = 2)
def _load(data, version):
    return Stats1DPluginView(**data)

@camel_registry.dumper(Stats1DPluginPlotParams, 'stats-1d-params', version = 1)
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
                
                # Base1DStatisticsView
                orientation = params.orientation,
                lim = params.lim,
                
                # Stats 1D View
                variable_lim = params.variable_lim,
                linestyle = params.linestyle,
                marker = params.marker,
                markersize = params.markersize,
                capsize = params.capsize,
                alpha = params.alpha,
                shade_error = params.shade_error,
                shade_alpha = params.shade_alpha)

@camel_registry.loader('stats-1d-params', version = any)
def _load_params(data, version):
    return Stats1DPluginPlotParams(**data)