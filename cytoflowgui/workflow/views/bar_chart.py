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
Bar Chart
---------

Plots a bar chart of a statistic.

Each variable in the statistic (ie, each variable chosen in the statistic
operation's **Group By**) must be set as **Variable** or as a facet.

.. object:: Statistic

    Which statistic to plot.
    
.. object:: Variable

    The statistic variable to use as the major bar groups.
    
.. object:: Scale

    How to scale the statistic plot.
    
.. object:: Horizontal Facet

    Make muliple plots, with each column representing a subset of the statistic
    with a different value for this variable.
        
.. object:: Vertical Facet

    Make multiple plots, with each row representing a subset of the statistic
    with a different value for this variable.
    
.. object:: Hue Facet

    Make multiple bars with different colors; each color represents a subset
    of the statistic with a different value for this variable.
    
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

    ex2 = flow.ThresholdOp(name = 'Threshold',
                           channel = 'Y2-A',
                           threshold = 2000).apply(ex)

    ex3 = flow.ChannelStatisticOp(name = "ByDox",
                                  channel = "Y2-A",
                                  by = ['Dox', 'Threshold'],
                                  function = len).apply(ex2) 
    
    flow.BarChartView(statistic = ("ByDox", "len"),
                      variable = "Dox",
                      huefacet = "Threshold").plot(ex3)
"""

from textwrap import dedent

from traits.api import provides, Instance

from cytoflow import BarChartView
import cytoflow.utility as util

from cytoflowgui.workflow.serialization import camel_registry, traits_repr, traits_str
from .view_base import IWorkflowView, WorkflowByView, Stats1DPlotParams

BarChartView.__repr__ = traits_repr


class BarChartPlotParams(Stats1DPlotParams):
    errwidth = util.PositiveCFloat(None, allow_none = True, allow_zero = False)
    capsize = util.PositiveCFloat(None, allow_none = True, allow_zero = False)
    
    
@provides(IWorkflowView)
class BarChartWorkflowView(WorkflowByView, BarChartView):
    plot_params = Instance(BarChartPlotParams, ())
    
    def get_notebook_code(self, idx):
        view = BarChartView()
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
@camel_registry.dumper(BarChartWorkflowView, 'bar-chart', version = 2)
def _dump(view):
    return dict(statistic = view.statistic,
                variable = view.variable,
                scale = view.scale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                error_statistic = view.error_statistic,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(BarChartWorkflowView, 'bar-chart', version = 1)
def _dump_v1(view):
    return dict(statistic = view.statistic,
                variable = view.variable,
                yscale = view.yscale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                error_statistic = view.error_statistic,
                subset_list = view.subset_list)
    
@camel_registry.dumper(BarChartPlotParams, 'barchart-params', version = 1)
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
                
                # BarChartView
                errwidth = params.errwidth,
                capsize = params.capsize)
    
@camel_registry.loader('bar-chart', version = 1)
def _load_v1(data, version):
    data['scale'] = data.pop('yscale')
    data['statistic'] = tuple(data['statistic'])
    data['error_statistic'] = tuple(data['error_statistic'])

    return BarChartWorkflowView(**data)

@camel_registry.loader('bar-chart', version = 2)
def _load_v2(data, version):
    return BarChartWorkflowView(**data)

@camel_registry.loader('barchart-params', version = any)
def _load_params(data, version):
    return BarChartPlotParams(**data)

