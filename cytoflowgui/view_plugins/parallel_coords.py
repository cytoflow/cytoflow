#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
Parallel Coordinates Plot
-------------------------

Plots a parallel coordinates plot.  PC plots are good for multivariate data; 
each vertical line represents one attribute, and one set of connected line 
segments represents one data point.

.. object:: Channels

    The channels to plot, and their scales.  Drag the blue dot to re-order.
    
.. object:: Add Channel, Remove Channel

    Add or remove a channel
    
.. object:: Horizonal Facet

    Make multiple plots.  Each column has a unique value of this variable.
    
.. object:: Vertical Facet

    Make multiple plots.  Each row has a unique value of this variable.
    
.. object:: Color Facet

    Plot different values of a condition with different colors.

.. object:: Color Scale

    Scale the color palette and the color bar
    
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
  
    flow.ParallelCoordinatesView(channels = ['B1-A', 'V2-A', 'Y2-A', 'FSC-A'],
                                 scale = {'Y2-A' : 'log',
                                          'V2-A' : 'log',
                                          'B1-A' : 'log',
                                          'FSC-A' : 'log'},
                                 huefacet = 'Dox').plot(ex)
'''

from traits.api import (provides, Callable, Str, List, HasTraits, Event, Dict,
                        on_trait_change, Instance)
from traitsui.api import (View, Item, Controller, EnumEditor, HGroup, VGroup, 
                          InstanceEditor, ButtonEditor, TextEditor)
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from cytoflow import ParallelCoordinatesView
import cytoflow.utility as util

from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import (IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin, 
            PluginHelpMixin, DataPlotParams)
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent
from cytoflowgui.vertical_list_editor import VerticalListEditor
from cytoflowgui.util import IterWrapper
from cytoflowgui.workflow import Changed

ParallelCoordinatesView.__repr__ = traits_repr

class _Channel(HasTraits):
    channel = Str
    scale = util.ScaleEnum
    
    # something here screws up traits' change notifications.
    
    def __repr__(self):
        return traits_repr(self)


class ParallelCoordinatesHandler(ViewHandlerMixin, Controller):
    
    add_channel = Event
    remove_channel = Event

    def default_traits_view(self):
        return View(
                    VGroup(
                        Item('channels_list',
                                editor = VerticalListEditor(editor = InstanceEditor(view = self.channel_traits_view()),
                                                            style = 'custom',
                                                            mutable = False),
                                style = 'custom'),
                        Item('handler.add_channel',
                             editor = ButtonEditor(value = True,
                                                   label = "Add a channel")),
                        Item('handler.remove_channel',
                             editor = ButtonEditor(value = True,
                                                   label = "Remove a channel")),
                        show_labels = False),
                    VGroup(
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
                                label = "Color\nFacet"),
                           Item('huescale',
                                label = "Color\nScale"),
                           Item('plotfacet',
                                editor=ExtendableEnumEditor(name='handler.conditions_names',
                                                            extra_items = {"None" : ""}),
                                label = "Tab\nFacet"),
                           label = "2D Histogram",
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
        

    # MAGIC: called when add_control is set
    def _add_channel_fired(self):
        self.model.channels_list.append(_Channel())
        
    def _remove_channel_fired(self):
        if self.model.channels_list:
            self.model.channels_list.pop()   
            
    def channel_traits_view(self):
        return View(HGroup(Item('channel',
                                editor = EnumEditor(name = 'handler.context.channels')),
                           Item('scale')),
                    handler = self)
        
class ParallelCoordinatesPlotParams(DataPlotParams):

    alpha = util.PositiveCFloat(0.02)
    
    def default_traits_view(self):
        base_view = DataPlotParams.default_traits_view(self)
        
        return View(Item('alpha',
                         editor = TextEditor(auto_set = False)),
                    base_view.content)
    

class ParallelCoordinatesPluginView(PluginViewMixin, ParallelCoordinatesView):
    handler_factory = Callable(ParallelCoordinatesHandler)
    plot_params = Instance(ParallelCoordinatesPlotParams, ())
    plotfacet = Str
    
    channels_list = List(_Channel)
    channels = List(Str, transient = True)
    scale = Dict(Str, util.ScaleEnum, transient = True)

    def enum_plots_wi(self, wi):
        if not self.plotfacet:
            return iter([])
        
        if self.plotfacet and self.plotfacet not in wi.result.conditions:
            raise util.CytoflowViewError("Plot facet {0} not in the experiment"
                                    .format(self.huefacet))
        values = np.sort(pd.unique(wi.result[self.plotfacet]))
        return IterWrapper(iter(values), [self.plotfacet])
    
    @on_trait_change('channels_list[], channels_list:+', post_init = True)
    def _channels_changed(self, obj, name, old, new):
        self.changed = (Changed.VIEW, (self, 'channels_list', self.channels_list))
        
    
    def plot(self, experiment, plot_name = None, **kwargs):
        
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
        
        if self.plotfacet and plot_name is not None:
            experiment = experiment.subset(self.plotfacet, plot_name)
            
        self.channels = []
        self.scale = {}
        for channel in self.channels_list:
            self.channels.append(channel.channel)
            self.scale[channel.channel] = channel.scale

        ParallelCoordinatesView.plot(self, experiment, **kwargs)
        
        if self.plotfacet and plot_name is not None:
            plt.title("{0} = {1}".format(self.plotfacet, plot_name))
            
    def get_notebook_code(self, idx):
        view = ParallelCoordinatesView()
        view.copy_traits(self, view.copyable_trait_names())
        
        for channel in self.channels_list:
            view.channels.append(channel.channel)
            view.scale[channel.channel] = channel.scale
            
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        {repr}.plot(ex_{idx}{plot}{plot_params})
        """
        .format(repr = repr(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.plot_names else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))

@provides(IViewPlugin)
class ParallelCoordinatesPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.view.parallel_coords'
    view_id = 'edu.mit.synbio.cytoflow.view.parallel_coords'
    short_name = "Parallel Coordinates Plot"

    def get_view(self):
        return ParallelCoordinatesPluginView()
    
    def get_icon(self):
        return ImageResource('parallel_coords')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
        
### Serialization
@camel_registry.dumper(ParallelCoordinatesPluginView, 'parallel-coords', version = 2)
def _dump(view):
    return dict(channels_list = view.channels_list,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(ParallelCoordinatesPluginView, 'parallel-coords', version = 1)
def _dump_v1(view):
    return dict(channels_list = view.channels_list,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list)
    
@camel_registry.dumper(ParallelCoordinatesPlotParams, 'parallel-coords-params', version = 1)
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
                
                # Parallel coords
                alpha = params.alpha)
    
@camel_registry.loader('parallel-coords', version = any)
def _load(data, version):
    return ParallelCoordinatesPluginView(**data)

@camel_registry.loader('parallel-coords-params', version = any)
def _load_params(data, version):
    return ParallelCoordinatesPlotParams(**data)

@camel_registry.dumper(_Channel, 'parallel-coords-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                scale = channel.scale)
    
@camel_registry.loader('parallel-coords-channel', version = 1)
def _load_channel(data, version):
    return _Channel(**data)