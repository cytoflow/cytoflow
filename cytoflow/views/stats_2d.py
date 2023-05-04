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
cytoflow.views.stats_2d
-----------------------

Plots two statistics on a scatter plot.

`Stats2DView` -- the `IView` class that makes the plot.
"""

from traits.api import provides, Constant
import matplotlib.pyplot as plt

import numpy as np
import matplotlib as mpl

import cytoflow.utility as util

from .i_view import IView
from .view_kwargs import try_get_kwarg
from .base_views import Base2DStatisticsView

@provides(IView)
class Stats2DView(Base2DStatisticsView):
    """
    Plot two statistics on a scatter plot.  A point (X,Y) is drawn for every
    pair of elements with the same value of `variable`; the X value is from 
    `xstatistic` and the Y value is from `ystatistic`.
    
    Attributes
    ----------

        
    Examples
    --------
    
    .. plot::
        :context: close-figs
        
        Make a little data set.
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
    
    Create two new statistics
    
    .. plot::
        :context: close-figs
        
        >>> ch_op = flow.ChannelStatisticOp(name = 'MeanByDox',
        ...                     channel = 'Y2-A',
        ...                     function = flow.geom_mean,
        ...                     by = ['Dox'])
        >>> ex2 = ch_op.apply(ex)
        >>> ch_op_2 = flow.ChannelStatisticOp(name = 'SdByDox',
        ...                       channel = 'Y2-A',
        ...                       function = flow.geom_sd,
        ...                       by = ['Dox'])
        >>> ex3 = ch_op_2.apply(ex2)
        
    Plot the statistics
    
    .. plot::
        :context: close-figs
        
        >>> flow.Stats2DView(variable = 'Dox',
        ...                  xstatistic = ('MeanByDox', 'geom_mean'),
        ...                  xscale = 'log',
        ...                  ystatistic = ('SdByDox', 'geom_sd'),
        ...                  yscale = 'log').plot(ex3)
    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.stats2d")
    friendly_id = Constant("2D Statistics View")
   
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce.  The values returned can be passed to `plot`.
        """
                
        return super().enum_plots(experiment)
            
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot a chart of two statistics' values as a common variable changes.
        
        Parameters
        ----------
        
        color : a matplotlib color
            The color to plot with.  Overridden if `huefacet` is not ``None``
            
        linestyle : {'solid' | 'dashed', 'dashdot', 'dotted' | (offset, on-off-dash-seq) | '-' | '--' | '-.' | ':' | 'None' | ' ' | ''}
            
        marker : a matplotlib marker style
            See http://matplotlib.org/api/markers_api.html#module-matplotlib.markers
            
        markersize : int
            The marker size in points
            
        markerfacecolor : a matplotlib color
            The color to make the markers.  Overridden (?) if `huefacet` is not ``None``
            
        alpha : the alpha blending value, from 0.0 (transparent) to 1.0 (opaque)
        
        Notes
        -----
        
        Other ``kwargs`` are passed to `matplotlib.pyplot.plot <https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.plot.html>`_
        
        """

        super().plot(experiment, plot_name, **kwargs)


    def _grid_plot(self, experiment, grid, **kwargs):

        data = grid.data
        xstat = experiment.statistics[self.xstatistic]
        xname = xstat.name
        ystat = experiment.statistics[self.ystatistic]
        yname = ystat.name
        
        if self.x_error_statistic[0]:
            x_error_stat = experiment.statistics[self.x_error_statistic]
            x_error_name = x_error_stat.name
        else:
            x_error_stat = None

        if self.y_error_statistic[0]:
            y_error_stat = experiment.statistics[self.y_error_statistic]
            y_error_name = y_error_stat.name
        else:
            y_error_stat = None
            
        xscale = try_get_kwarg(kwargs,'xscale')
        yscale = try_get_kwarg(kwargs,'yscale')
        
        capsize = try_get_kwarg(kwargs,'capsize', None)
        
        xlim = try_get_kwarg(kwargs,"xlim", None)
        if xlim is None:
            xlim = (xscale.clip(data[xname].min() * 0.9),
                    xscale.clip(data[xname].max() * 1.1))
            
            if x_error_stat is not None:
                try: 
                    xlim = (xscale.clip(min([x[0] for x in data[x_error_name]]) * 0.9),
                            xscale.clip(max([x[1] for x in data[x_error_name]]) * 1.1))
                except (TypeError, IndexError):
                    xlim = (xscale.clip((data[xname].min() - data[x_error_name].min()) * 0.9), 
                            xscale.clip((data[xname].max() + data[x_error_name].max()) * 1.1))
                      
        ylim = try_get_kwarg(kwargs,"ylim", None)
        if ylim is None:
            ylim = (yscale.clip(data[yname].min() * 0.9),
                    yscale.clip(data[yname].max() * 1.1))
            
            if y_error_stat is not None:
                try: 
                    ylim = (yscale.clip(min([x[0] for x in data[y_error_name]]) * 0.9),
                            yscale.clip(max([x[1] for x in data[y_error_name]]) * 1.1))
                except (TypeError, IndexError):
                    ylim = (yscale.clip((data[yname].min() - data[y_error_name].min()) * 0.9), 
                            yscale.clip((data[yname].max() + data[y_error_name].max()) * 1.1))
        
        # plot the error bars first so the axis labels don't get overwritten
        if x_error_stat is not None:
            grid.map(_x_error_bars, xname, yname, x_error_name, capsize = capsize)
            
        if y_error_stat is not None:
            grid.map(_y_error_bars, xname, yname, y_error_name, capsize = capsize)

        grid.map(plt.plot, xname, yname, **kwargs)
        
        return dict(xscale = xscale,
                    xlim = xlim,
                    yscale = yscale,
                    ylim = ylim)


def _y_error_bars(x, y, yerr, ax = None, color = None, errwidth = None, capsize = None, **kwargs):
    
    if errwidth is not None:
        kwargs.setdefault("lw", errwidth)
    else:
        kwargs.setdefault("lw", mpl.rcParams["lines.linewidth"] * 1.8)
    
    if isinstance(yerr.iloc[0], tuple):
        lo = [ye[0] for ye in yerr]
        hi = [ye[1] for ye in yerr]
    else:
        lo = [y.iloc[i] - ye for i, ye in yerr.reset_index(drop = True).items()]
        hi = [y.iloc[i] + ye for i, ye in yerr.reset_index(drop = True).items()]
        
    if capsize is not None:
        kwargs['marker'] = '_'
        kwargs['markersize'] = capsize * 2
        kwargs['markeredgewidth'] = kwargs['lw']
        
    for x_i, lo_i, hi_i in zip(x, lo, hi):
        plt.plot((x_i, x_i), (lo_i, hi_i), color = color, **kwargs)
    
def _x_error_bars(x, y, xerr, ax = None, color = None, errwidth = None, capsize = None, **kwargs):

    
    if errwidth is not None:
        kwargs.setdefault("lw", errwidth)
    else:
        kwargs.setdefault("lw", mpl.rcParams["lines.linewidth"] * 1.8)
    
    if isinstance(xerr.iloc[0], tuple):
        lo = [xe[0] for xe in xerr]
        hi = [xe[1] for xe in xerr]
    else:
        lo = [x.iloc[i] - xe for i, xe in xerr.reset_index(drop = True).items()]
        hi = [x.iloc[i] + xe for i, xe in xerr.reset_index(drop = True).items()]

    if capsize is not None:
        kwargs['marker'] = '|'
        kwargs['markersize'] = capsize * 2
        kwargs['markeredgewidth'] = kwargs['lw']

        
    for y_i, lo_i, hi_i in zip(y, lo, hi):
        plt.plot((lo_i, hi_i), (y_i, y_i), color = color, **kwargs)
    
util.expand_class_attributes(Stats2DView)
util.expand_method_parameters(Stats2DView, Stats2DView.plot)
    
if __name__ == '__main__':
    import cytoflow as flow
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])
    
    thresh = flow.ThresholdOp()
    thresh.name = "Y2-A+"
    thresh.channel = 'Y2-A'
    thresh.threshold = 2005.0

    ex2 = thresh.apply(ex)
    
    s = flow.Stats2DView()
    s.variable = "Dox"
    s.xchannel = "V2-A"
    s.xfunction = np.mean
    s.ychannel = "Y2-A"
    s.yfunction = np.mean
    s.huefacet = "Y2-A+"

    
    plt.ioff()
    s.plot(ex2)
    plt.show()