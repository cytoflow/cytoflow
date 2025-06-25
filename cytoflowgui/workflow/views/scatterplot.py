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
cytoflowgui.workflow.views.scatterplot
--------------------------------------

"""

from textwrap import dedent

from traits.api import provides, Enum, Instance

from cytoflow import ScatterplotView
import cytoflow.utility as util

from cytoflowgui.workflow.serialization import camel_registry, cytoflow_class_repr, traits_str
from .view_base import IWorkflowView, WorkflowFacetView, Data2DPlotParams, SCATTERPLOT_MARKERS

ScatterplotView.__repr__ = cytoflow_class_repr

class ScatterplotPlotParams(Data2DPlotParams):

    alpha = util.PositiveCFloat(0.25)
    s = util.PositiveCFloat(2)
    marker = Enum(SCATTERPLOT_MARKERS)
    
@provides(IWorkflowView)    
class ScatterplotWorkflowView(WorkflowFacetView, ScatterplotView):
    plot_params = Instance(ScatterplotPlotParams, ())
            
    def get_notebook_code(self, idx):
        view = ScatterplotView()
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        {repr}.plot(ex_{idx}{plot}{plot_params})
        """
        .format(repr = repr(view),
                idx = idx,
                plot = ".subset(" + repr(self.plotfacet) + ", " + repr(self.current_plot) + ")" if self.current_plot else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))
        
        
### Serialization

@camel_registry.dumper(ScatterplotWorkflowView, 'scatterplot', version = 2)
def _dump_v2(view):
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
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(ScatterplotWorkflowView, 'scatterplot', 1)
def _dump_v1(view):
    return dict(xchannel = view.xchannel,
                xscale = view.xscale,
                ychannel = view.ychannel,
                yscale = view.yscale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list)
    
@camel_registry.dumper(ScatterplotPlotParams, 'scatterplot-params', version = 2)
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
                
                # Data2DPlotParams
                xlim = params.xlim,
                ylim = params.ylim,
                
                # Scatterplot params
                alpha = params.alpha,
                s = params.s,
                marker = params.marker )
    
@camel_registry.dumper(ScatterplotPlotParams, 'scatterplot-params', version = 1)
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
                
                # Data2DPlotParams
                xlim = params.xlim,
                ylim = params.ylim,
                
                # Scatterplot params
                alpha = params.alpha,
                s = params.s,
                marker = params.marker )
    
@camel_registry.loader('scatterplot', version = any)
def _load(data, version):
    return ScatterplotWorkflowView(**data)

@camel_registry.loader('scatterplot-params', version = any)
def _load_params(data, version):
    return ScatterplotPlotParams(**data)