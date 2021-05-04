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
2D Statistics Plot
------------------

Plot two statistics on a scatter plot.  A point (X,Y) is drawn for every
pair of elements with the same value of **Variable**; the X value is from 
** X statistic** and the Y value is from **Y statistic**.

.. object:: X Statistic

    Which statistic to plot on the X axis.

.. object:: Y Statistic

    Which statistic to plot on the Y axis.  Must have the same indices as
    **X Statistic**.

.. object:: X Scale, Y Scale

    How to scale the X and Y axes.
    
.. object:: Variable

    The statistic variable to put on the plot.

.. object:: Horizontal Facet

    Make muliple plots, with each column representing a subset of the statistic
    with a different value for this variable.
        
.. object:: Vertical Facet

    Make multiple plots, with each row representing a subset of the statistic
    with a different value for this variable.
    
.. object:: Color Facet

    Make lines on the plot with different colors; each color represents a subset
    of the statistic with a different value for this variable.
    
.. object:: Color Scale

    If **Color Facet** is a numeric variable, use this scale for the color
    bar.
    
.. object:: X Error Statistic

    A statistic to use to make error bars in the X direction.  Must have the 
    same indices as the statistic in **X Statistic**.

.. object:: Y Error Statistic

    A statistic to use to make error bars in the Y direction.  Must have the 
    same indices as the statistic in **Y Statistic**.
    
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

    ch_op = flow.ChannelStatisticOp(name = 'MeanByDox',
                        channel = 'Y2-A',
                        function = flow.geom_mean,
                        by = ['Dox'])
    ex2 = ch_op.apply(ex)
    ch_op_2 = flow.ChannelStatisticOp(name = 'SdByDox',
                          channel = 'Y2-A',
                          function = flow.geom_sd,
                          by = ['Dox'])
    ex3 = ch_op_2.apply(ex2)
    
    flow.Stats2DView(variable = 'Dox',
                     xstatistic = ('MeanByDox', 'geom_mean'),
                     xscale = 'log',
                     ystatistic = ('SdByDox', 'geom_sd'),
                     yscale = 'log').plot(ex3)
"""

from textwrap import dedent

from traits.api import provides, Instance, Enum

from cytoflow import Stats2DView
import cytoflow.utility as util

from cytoflowgui.workflow.serialization import camel_registry, traits_repr, traits_str
from .view_base import IWorkflowView, WorkflowStatisticsView, Stats2DPlotParams as _Stats2DPlotParams, LINE_STYLES, SCATTERPLOT_MARKERS

Stats2DView.__repr__ = traits_repr


class Stats2DPlotParams(_Stats2DPlotParams):
    linestyle = Enum(LINE_STYLES)
    marker = Enum(SCATTERPLOT_MARKERS)
    markersize = util.PositiveCFloat(6, allow_zero = False)
    capsize = util.PositiveCFloat(None, allow_none = True, allow_zero = False)
    alpha = util.PositiveCFloat(1.0)


@provides(IWorkflowView)
class Stats2DWorkflowView(WorkflowStatisticsView, Stats2DView):
    plot_params = Instance(Stats2DPlotParams, ())
    
    def get_notebook_code(self, idx):
        view = Stats2DView()
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

@camel_registry.dumper(Stats2DWorkflowView, 'stats-2d', version = 2)
def _dump(view):
    return dict(xstatistic = view.xstatistic,
                xscale = view.xscale,
                ystatistic = view.ystatistic,
                yscale = view.yscale,
                variable = view.variable,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                x_error_statistic = view.x_error_statistic,
                y_error_statistic = view.y_error_statistic,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(Stats2DWorkflowView, 'stats-2d', version = 1)
def _dump_v1(view):
    return dict(xstatistic = view.xstatistic,
                xscale = view.xscale,
                ystatistic = view.ystatistic,
                yscale = view.yscale,
                variable = view.variable,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                x_error_statistic = view.x_error_statistic,
                y_error_statistic = view.y_error_statistic,
                subset_list = view.subset_list)


@camel_registry.loader('stats-2d', version = any)
def _load(data, version):
    data['xstatistic'] = tuple(data['xstatistic'])
    data['ystatistic'] = tuple(data['ystatistic'])
    data['x_error_statistic'] = tuple(data['x_error_statistic'])
    data['y_error_statistic'] = tuple(data['y_error_statistic'])

    return Stats2DWorkflowView(**data)

@camel_registry.dumper(Stats2DPlotParams, 'stats-2d-params', version = 1)
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
                
                # Base2DStatisticsView
                xlim = params.xlim,
                ylim = params.ylim,
                
                # Stats 2D View
                linestyle = params.linestyle,
                marker = params.marker,
                markersize = params.markersize,
                capsize = params.capsize,
                alpha = params.alpha)

@camel_registry.loader('stats-2d-params', version = any)
def _load_params(data, version):
    return Stats2DPlotParams(**data)
