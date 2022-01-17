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
cytoflowgui.workflow.views.stats_1d
-----------------------------------

"""

from textwrap import dedent

from traits.api import provides, Instance, Tuple, Enum, Bool

from cytoflow import Stats1DView
import cytoflow.utility as util

from cytoflowgui.workflow.serialization import camel_registry, traits_repr, traits_str
from .view_base import IWorkflowView, WorkflowByView, Stats1DPlotParams as _Stats1DPlotParams, LINE_STYLES, SCATTERPLOT_MARKERS

Stats1DView.__repr__ = traits_repr


class Stats1DPlotParams(_Stats1DPlotParams):
    variable_lim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    linestyle = Enum(LINE_STYLES)
    marker = Enum(SCATTERPLOT_MARKERS)
    markersize = util.PositiveCFloat(6, allow_zero = False)
    capsize = util.PositiveCFloat(0, allow_zero = True)
    alpha = util.PositiveCFloat(1.0)
    shade_error = Bool(False)
    shade_alpha = util.PositiveCFloat(0.2)
    
    
@provides(IWorkflowView)
class Stats1DWorkflowView(WorkflowByView, Stats1DView):
    plot_params = Instance(Stats1DPlotParams, ())
    
    def get_notebook_code(self, idx):
        view = Stats1DView()
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        {repr}.plot(ex_{idx}{plot}{plot_params})
        """
        .format(repr = repr(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.current_plot else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))
        
        
### Serialization
@camel_registry.dumper(Stats1DWorkflowView, 'stats-1d', version = 2)
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
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    

@camel_registry.dumper(Stats1DWorkflowView, 'stats-1d', version = 1)
def _dump_v1(view):
    return dict(statistic = view.statistic,
                variable = view.variable,
                xscale = view.xscale,
                yscale = view.yscale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                error_statistic = view.error_statistic,
                subset_list = view.subset_list)
    
@camel_registry.loader('stats-1d', version = 1)
def _load_v1(data, version):

    xscale = data.pop('xscale')
    yscale = data.pop('yscale')
    
    data['statistic'] = tuple(data['statistic'])
    data['error_statistic'] = tuple(data['error_statistic'])

    return Stats1DWorkflowView(scale = yscale,
                             variable_scale = xscale,
                             **data)

@camel_registry.loader('stats-1d', version = 2)
def _load(data, version):
    return Stats1DWorkflowView(**data)

@camel_registry.dumper(Stats1DPlotParams, 'stats-1d-params', version = 1)
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
    return Stats1DPlotParams(**data)
