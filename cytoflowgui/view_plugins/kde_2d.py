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

'''
2D Kernel Density Estimate
--------------------------

Plots a 2-d kernel-density estimate.  Sort of like a smoothed histogram.
The density is visualized with a set of isolines.

.. object:: X Channel, Y Channel

    The channels to plot on the X and Y axes.
    
.. object:: X Scale, Y Scale

    How to scale the X and Y axes of the plot.
    
.. object:: Horizonal Facet

    Make multiple plots.  Each column has a unique value of this variable.
    
.. object:: Vertical Facet

    Make multiple plots.  Each row has a unique value of this variable.
    
.. object:: Color Facet

    Plot with multiple colors.  Each color has a unique value of this variable.
    
.. object:: Color Scale

    If **Color Facet** is a numeric variable, use this scale for the color
    bar.
    
.. object:: Tab Facet

    Make multiple plots in differen tabs; each tab's plot has a unique value
    of this variable.
    
.. object:: Subset

    Plot only a subset of the data in the experiment.

.. plot::

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()
    
    flow.Kde2DView(xchannel = 'V2-A',
                   xscale = 'log',
                   ychannel = 'Y2-A',
                   yscale = 'log',
                   huefacet = 'Dox').plot(ex)
'''

from traits.api import provides, Callable, Str, Bool, Instance, Enum
from traitsui.api import View, Item, Controller, EnumEditor, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import Kde2DView
import cytoflow.utility as util

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import (IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin, 
            PluginHelpMixin, Data2DPlotParams)
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent
from cytoflowgui.util import IterWrapper

Kde2DView.__repr__ = traits_repr

class Kde2DHandler(ViewHandlerMixin, Controller):

    def default_traits_view(self):
        return View(
                  VGroup(
                     Item('xchannel',
                          editor=EnumEditor(name='context.channels'),
                          label = "X Channel"),
                     Item('xscale',
                          label = "X Scale"),
                     Item('ychannel',
                          editor=EnumEditor(name='context.channels'),
                          label = "Y Channel"),
                     Item('yscale',
                          label = "Y Scale"),
                     Item('xfacet',
                          editor=ExtendableEnumEditor(name='handler.conditions_names',
                                                      extra_items = {"None" : ""}),
                          label = "Horizontal\nFacet"),
                     Item('yfacet',
                          editor=ExtendableEnumEditor(name='handler.conditions_names',
                                                      extra_items = {"None" : ""}),
                          label = "Vertical\nFacet"),
                     Item('huefacet',
                          editor=ExtendableEnumEditor(name='handler.conditions_names',
                                                      extra_items = {"None" : ""}),
                          label="Color\nFacet"),
                     Item('huescale',
                          label = "Color\nScale"),
                     Item('plotfacet',
                          editor=ExtendableEnumEditor(name='handler.conditions_names',
                                                      extra_items = {"None" : ""}),
                          label = "Tab\nFacet"),
                     label = "2D Kernel Density Estimate",
                     show_border = False),
                  VGroup(Item('subset_list',
                              show_label = False,
                              editor = SubsetListEditor(conditions = "context.conditions")),
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
                                                background_color = "#ff9191")))
        
class Kde2DPlotParams(Data2DPlotParams):
    
    shade = Bool(False)
    min_alpha = util.PositiveCFloat(0.2, allow_zero = False)
    max_alpha = util.PositiveCFloat(0.9, allow_zero = False)
    n_levels = util.PositiveCInt(10, allow_zero = False)
    bw = Enum(['scott', 'silverman'])
    gridsize = util.PositiveCInt(50, allow_zero = False)
    
    def default_traits_view(self):
        base_view = Data2DPlotParams.default_traits_view(self)
        
        return View(Item('shade'),
                    Item('min_alpha',
                         editor = TextEditor(auto_set = False)),
                    Item('max_alpha',
                         editor = TextEditor(auto_set = False)),
                    Item('n_levels',
                         editor = TextEditor(auto_set = False),
                         label = "Num\nlevels"),
                    Item('bw', label = "Bandwidth"),
                    Item('gridsize',
                         editor = TextEditor(auto_set = False),
                         label = "Grid size"),
                    base_view.content)


class Kde2DPluginView(PluginViewMixin, Kde2DView):
    handler_factory = Callable(Kde2DHandler)
    plot_params = Instance(Kde2DPlotParams, ())
    plotfacet = Str

    def enum_plots_wi(self, wi):
        if not self.plotfacet:
            return iter([])
        
        if self.plotfacet and self.plotfacet not in wi.result.conditions:
            raise util.CytoflowViewError("Plot facet {0} not in the experiment"
                                    .format(self.huefacet))
        values = np.sort(pd.unique(wi.result[self.plotfacet]))
        return IterWrapper(iter(values), [self.plotfacet])

    
    def plot(self, experiment, plot_name = None, **kwargs):
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
        
        if self.plotfacet and plot_name is not None:
            experiment = experiment.subset(self.plotfacet, plot_name)

        Kde2DView.plot(self, experiment, **kwargs)
        
        if self.plotfacet and plot_name is not None:
            plt.title("{0} = {1}".format(self.plotfacet, plot_name))
            
    def get_notebook_code(self, idx):
        view = Kde2DView()
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
class Kde2DPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.view.kde2d'
    view_id = 'edu.mit.synbio.cytoflow.view.kde2d'
    short_name = "2D Kernel Density Estimate"
    
    def get_view(self):
        return Kde2DPluginView()
    
    def get_icon(self):
        return ImageResource('kde_2d')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self

### Serialization
@camel_registry.dumper(Kde2DPluginView, 'kde-2d', version = 2)
def _dump(view):
    return dict(xchannel = view.xchannel,
                xscale = view.xscale,
                ychannel = view.ychannel,
                yscale = view.yscale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params)
    
@camel_registry.dumper(Kde2DPluginView, 'kde-2d', version = 1)
def _dump_v1(view):
    return dict(xchannel = view.xchannel,
                xscale = view.xscale,
                ychannel = view.ychannel,
                yscale = view.yscale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plot_facet,
                subset_list = view.subset_list)
    
@camel_registry.dumper(Kde2DPlotParams, 'kde-2d-params', version = 1)
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

                # DataplotParams
                min_quantile = params.min_quantile,
                max_quantile = params.max_quantile,
                
                # Data2DPlotParams
                xlim = params.xlim,
                ylim = params.ylim,
                
                # 2D KDE params
                shade = params.shade,
                min_alpha = params.min_alpha,
                max_alpha = params.max_alpha,
                n_levels = params.n_levels,
                bw = params.bw,
                gridsize = params.gridsize)
    
@camel_registry.loader('kde-2d', version = any)
def _load(data, version):
    return Kde2DPluginView(**data)


@camel_registry.loader('kde-2d-params', version = any)
def _load_params(data, version):
    return Kde2DPlotParams(**data)