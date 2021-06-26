#!/usr/bin/env python3.8
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

from textwrap import dedent

from traits.api import (HasTraits, provides, Str, Instance, List, Dict,
                        Enum, Property, observe)


from cytoflow import RadvizView
import cytoflow.utility as util

from cytoflowgui.workflow.serialization import camel_registry, traits_repr, traits_str
from .view_base import IWorkflowView, WorkflowFacetView, DataPlotParams
from .scatterplot import SCATTERPLOT_MARKERS

RadvizView.__repr__ = traits_repr

    
class RadvizPlotParams(DataPlotParams):
    alpha = util.PositiveCFloat(0.25)
    s = util.PositiveCFloat(2)
    marker = Enum(SCATTERPLOT_MARKERS)
    

class Channel(HasTraits):
    channel = Str
    scale = util.ScaleEnum
        
    def __repr__(self):
        return traits_repr(self)


@provides(IWorkflowView)
class RadvizWorkflowView(WorkflowFacetView, RadvizView):
    plot_params = Instance(RadvizPlotParams, ())
    
    channels_list = List(Channel)
    channels = Property(List(Str), 
                        observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    scale = Property(Dict(Str, util.ScaleEnum),
                     observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
            
    def get_notebook_code(self, idx):
        view = RadvizView()
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
        
    @observe('[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    def _channels_updated(self, event):
        self.changed = 'channels_list'
        
    def _get_channels(self):
        return [c.channel for c in self.channels_list]
    
    def _get_scale(self):
        return {c.channel : c.scale for c in self.channels_list}
    

### Serialization
@camel_registry.dumper(RadvizWorkflowView, 'radviz', version = 2)
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
    
@camel_registry.dumper(RadvizWorkflowView, 'radviz', version = 1)
def _dump_v1(view):
    return dict(channels_list = view.channels_list,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list)
    
@camel_registry.loader('radviz', version = any)
def _load(data, version):
    return RadvizWorkflowView(**data)
    
@camel_registry.dumper(RadvizPlotParams, 'radviz-params', version = 1)
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
                
                # radviz params
                alpha = params.alpha,
                s = params.s,
                marker = params.marker )
    
@camel_registry.loader('radviz-params', version = any)
def _load_params(data, version):
    return RadvizPlotParams(**data)

@camel_registry.dumper(Channel, 'radviz-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                scale = channel.scale)
    
@camel_registry.loader('radviz-channel', version = 1)
def _load_channel(data, version):
    return Channel(**data)
