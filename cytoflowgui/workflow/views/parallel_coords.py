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
cytoflowgui.workflow.views.parallel_coords
------------------------------------------

"""

from textwrap import dedent

from traits.api import provides, Str, Instance, List, Dict, Property, observe

from cytoflow import ParallelCoordinatesView
import cytoflow.utility as util

from ..serialization import camel_registry, cytoflow_class_repr, traits_str
from .view_base import IWorkflowView, WorkflowFacetView, DataPlotParams, Channel

ParallelCoordinatesView.__repr__ = cytoflow_class_repr


class ParallelCoordinatesPlotParams(DataPlotParams):
    alpha = util.PositiveCFloat(0.02)
    
    
@provides(IWorkflowView)
class ParallelCoordinatesWorkflowView(WorkflowFacetView, ParallelCoordinatesView):
    plot_params = Instance(ParallelCoordinatesPlotParams, ())
    
    channels_list = List(Channel)
    channels = Property(List(Str), 
                        observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    scale = Property(Dict(Str, util.ScaleEnum),
                     observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
            
    def get_notebook_code(self, idx):
        view = ParallelCoordinatesView()
        view.copy_traits(self, view.copyable_trait_names())
            
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        {repr}.plot(ex_{idx}{plot}{plot_params})
        """
        .format(repr = repr(view),
                idx = idx,
                plot = ".subset(" + repr(self.plotfacet) + ", " + repr(self.current_plot) + ")" if self.current_plot else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))
        
        
    @observe('[channels_list:items,channels_list:items:channel,channels_list:items:scale]')
    def _channels_updated(self, event):
        self.changed = 'channels_list'
        
    def _get_channels(self):
        return [c.channel for c in self.channels_list]
    
    def _get_scale(self):
        return {c.channel : c.scale for c in self.channels_list}
    
    
### Serialization
@camel_registry.dumper(ParallelCoordinatesWorkflowView, 'parallel-coords', version = 2)
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
    
@camel_registry.dumper(ParallelCoordinatesWorkflowView, 'parallel-coords', version = 1)
def _dump_v1(view):
    return dict(channels_list = view.channels_list,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list)
    
@camel_registry.dumper(ParallelCoordinatesPlotParams, 'parallel-coords-params', version = 2)
def _dump_params_v2(params):
    return dict(
                # BasePlotParams
                title = params.title,
                xlabel = params.xlabel,
                ylabel = params.ylabel,
                huelabel = params.huelabel,
                col_wrap = params.col_wrap,
                sns_style = params.sns_style,
                sns_context = params.sns_context,
                palette = params.palette,
                legend = params.legend,
                sharex = params.sharex,
                sharey = params.sharey,
                despine = params.despine,

                # DataplotParams
                min_quantile = params.min_quantile,
                max_quantile = params.max_quantile,
                
                # Parallel coords
                alpha = params.alpha)
    
@camel_registry.dumper(ParallelCoordinatesPlotParams, 'parallel-coords-params', version = 1)
def _dump_params_v1(params):
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
    return ParallelCoordinatesWorkflowView(**data)

@camel_registry.loader('parallel-coords-params', version = any)
def _load_params(data, version):
    return ParallelCoordinatesPlotParams(**data)

@camel_registry.dumper(Channel, 'parallel-coords-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                scale = channel.scale)
    
@camel_registry.loader('parallel-coords-channel', version = 1)
def _load_channel(data, version):
    return Channel(**data)


