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
1D Statistics Plot
------------------

Plots a line plot of a statistic.

Each variable in the statistic (ie, each variable chosen in the statistic
operation's **Group By**) must be set as **Variable** or as a facet.

.. object:: Statistic

    Which statistic to plot.
    
.. object:: Feature
        The column in the statistic to plot on the Y axis (often a channel name.)
    
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
   :include-source: False

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
                     statistic = 'MeanByDox',
                     feature = 'Y2-A',
                     scale = 'log',
                     variable_scale = 'log').plot(ex2)
"""

import pandas as pd

from traits.api import provides, Property, List
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller, TupleEditor
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

import cytoflow.utility as util

from ..workflow.views import Stats1DWorkflowView, Stats1DPlotParams
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler, PluginHelpMixin, Stats1DPlotParamsView


class Stats1DParamsHandler(Controller):
    view_params_view = \
        View(Item('variable_lim',
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
             Stats1DPlotParamsView.content)

  
class Stats1DHandler(ViewHandler):
    indices = Property(depends_on = "context.statistics, model.statistic, model.subset")
    numeric_indices = Property(depends_on = "context.statistics, model.statistic, model.subset")
    levels = Property(depends_on = "context.statistics, model.statistic")
    features = Property(depends_on = "context.statistics, model.statistic")

    view_traits_view = \
        View(VGroup(
             VGroup(Item('statistic',
                         editor=EnumEditor(name='context_handler.statistics_names'),
                         label = "Statistic"),
                    Item('feature',
                         editor = EnumEditor(name='handler.features'),
                         label = "Feature"),
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
                    Item('error_low',
                         editor=ExtendableEnumEditor(name='handler.features',
                                                     extra_items = {"None" : ""}),
                         label = "Error Bar Low"),
                    Item('error_high',
                         editor=ExtendableEnumEditor(name='handler.features',
                                                     extra_items = {"None" : ""}),
                         label = "Error Bar High"),
                    label = "One-Dimensional Statistics Plot",
                    show_border = False),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "handler.levels",
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory),
                                                   mutable = False)),
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
        
    view_params_view = \
        View(Item('plot_params',
                  editor = InstanceHandlerEditor(view = 'view_params_view',
                                                 handler_factory = Stats1DParamsHandler),
                  style = 'custom',
                  show_label = False))
        
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
            return {}
        
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
        
    # MAGIC: gets the value for the property "features"
    def _get_features(self):
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return []
         
        stat = self.context.statistics[self.model.statistic]
        return stat.columns.to_list()


@provides(IViewPlugin)
class Stats1DPlugin(Plugin, PluginHelpMixin):

    id = 'cytoflowgui.view.stats1d'
    view_id = 'cytoflow.view.stats1d'
    name = "1D Statistics View"
    
    def get_view(self):
        return Stats1DWorkflowView()
    
    def get_handler(self, model, context):
        if isinstance(model, Stats1DWorkflowView):
            return Stats1DHandler(model = model, context = context)
        elif isinstance(model, Stats1DPlotParams):
            return Stats1DParamsHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('stats_1d')

    plugin = List(contributes_to = VIEW_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
    


