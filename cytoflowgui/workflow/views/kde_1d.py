#!/usr/bin/env python3.8
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

from textwrap import dedent

from traits.api import provides, Enum, Bool, Instance

from cytoflow import Kde1DView
import cytoflow.utility as util

from cytoflowgui.workflow.serialization import camel_registry, traits_repr, traits_str
from .view_base import IWorkflowView, WorkflowView, Data1DPlotParams, LINE_STYLES

Kde1DView.__repr__ = traits_repr

class Kde1DPlotParams(Data1DPlotParams):

    shade = Bool(True)
    alpha = util.PositiveCFloat(0.25)
    kernel = Enum(['gaussian','tophat','epanechnikov','exponential','linear','cosine'])
    bw = Enum(['scott', 'silverman'])
    gridsize = util.PositiveCInt(100, allow_zero = False)
    linestyle = Enum(LINE_STYLES)
    linewidth = util.PositiveCFloat(2, allow_zero = True)
    
    
    
@provides(IWorkflowView)
class Kde1DWorkflowView(WorkflowView, Kde1DView):
    plot_params = Instance(Kde1DPlotParams, ())
            
    def get_notebook_code(self, idx):
        view = Kde1DView()
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        {repr}.plot(ex_{idx}{plot}{plot_params})
        """
        .format(repr = repr(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.plot_names else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))


    
### Serialization
@camel_registry.dumper(Kde1DWorkflowView, 'kde-1d', version = 2)
def _dump(view):
    return dict(channel = view.channel,
                scale = view.scale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(Kde1DWorkflowView, 'kde-1d', version = 1)
def _dump_v1(view):
    return dict(channel = view.channel,
                scale = view.scale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list)
    
    
@camel_registry.dumper(Kde1DPlotParams, 'kde-1d-params', version = 1)
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
                
                # Data1DPlotParams
                lim = params.lim,
                orientation = params.orientation,
                
                # KDE params
                shade = params.shade,
                alpha = params.alpha, 
                kernel = params.kernel,
                bw = params.bw,
                gridsize = params.gridsize,
                linestyle = params.linestyle,
                linewidth = params.linewidth)
    
@camel_registry.loader('kde-1d', version = any)
def _load(data, version):
    return Kde1DWorkflowView(**data)

@camel_registry.loader('kde-1d-params', version = any)
def _load_params(data, version):
    return Kde1DPlotParams(**data)