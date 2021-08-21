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

"""
cytoflowgui.workflow.views.histogram
------------------------------------

"""

from textwrap import dedent

from traits.api import provides, Enum, Bool, Instance

from cytoflow import HistogramView
import cytoflow.utility as util

from cytoflowgui.workflow.serialization import camel_registry, traits_repr, traits_str
from .view_base import IWorkflowView, WorkflowFacetView, Data1DPlotParams, LINE_STYLES

HistogramView.__repr__ = traits_repr
        

class HistogramPlotParams(Data1DPlotParams):
    num_bins = util.PositiveCInt(None, allow_none = True)
    histtype = Enum(['stepfilled', 'step', 'bar'])
    linestyle = Enum(LINE_STYLES)
    linewidth = util.PositiveCFloat(None, allow_none = True, allow_zero = True)
    density = Bool(False)
    alpha = util.PositiveCFloat(0.5, allow_zero = True)
    
    
@provides(IWorkflowView)
class HistogramWorkflowView(WorkflowFacetView, HistogramView):
    plot_params = Instance(HistogramPlotParams, ())
            
    def get_notebook_code(self, idx):
        view = HistogramView()
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        {repr}.plot(ex_{idx}{plot}{plot_params})
        """
        .format(repr = repr(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.current_plot else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))

    
@camel_registry.dumper(HistogramWorkflowView, 'histogram', version = 2)
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
    
    
@camel_registry.dumper(HistogramWorkflowView, 'histogram', version = 1)
def _dump_v1(view):
    return dict(channel = view.channel,
                scale = view.scale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list)
    
    
@camel_registry.dumper(HistogramPlotParams, 'histogram-params', version = 1)
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
                
                # Data1DPlotParams
                lim = params.lim,
                orientation = params.orientation,
                
                # Histogram
                num_bins = params.num_bins,
                histtype = params.histtype,
                linestyle = params.linestyle,
                linewidth = params.linewidth,
                normed = params.density)
    
    
@camel_registry.dumper(HistogramPlotParams, 'histogram-params', version = 2)
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
                
                # Histogram
                num_bins = params.num_bins,
                histtype = params.histtype,
                linestyle = params.linestyle,
                linewidth = params.linewidth,
                density = params.density)
    
    
@camel_registry.dumper(HistogramPlotParams, 'histogram-params', version = 3)
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
                
                # Histogram
                num_bins = params.num_bins,
                histtype = params.histtype,
                linestyle = params.linestyle,
                linewidth = params.linewidth,
                density = params.density,
                alpha = params.alpha)
    
    
@camel_registry.loader('histogram', version = any)
def _load(data, version):
    return HistogramWorkflowView(**data)


@camel_registry.loader('histogram-params', version = 1)
def _load_params_v1(data, version):
    data['density'] = data['normed']
    del data['normed']
    return HistogramPlotParams(**data)


@camel_registry.loader('histogram-params', version = 2)
def _load_params_v2(data, version):
    return HistogramPlotParams(**data)


@camel_registry.loader('histogram-params', version = 3)
def _load_params(data, version):
    return HistogramPlotParams(**data)

