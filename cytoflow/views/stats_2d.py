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
from .base_views import Base2DStatisticsView

@provides(IView)
class Stats2DView(Base2DStatisticsView):
    """
    Plot two statistics on a scatter plot.  A point (X,Y) is drawn for every
    pair of elements with the same value of `variable`; the X value is from 
    `xfeature` and the Y value is from `yfeature`.
    
    Attributes
    ----------

        
    Examples
    --------
    
    .. plot::
        :context: close-figs
        
        Make a little data set.
    
        >>> import cytoflow as flow
        >>> import pandas as pd
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
        
        >>> ch_op = flow.ChannelStatisticOp(name = 'MeanSDByDox',
        ...                     channel = 'Y2-A',
        ...                     function = lambda x: pd.Series({'Geo.Mean' : flow.geom_mean(x),
        ...                                                     'Geo.SD' : flow.geom_sd(x)}), 
        ...                     by = ['Dox'])
        >>> ex2 = ch_op.apply(ex)
        
    Plot the statistics
    
    .. plot::
        :context: close-figs
        
        >>> flow.Stats2DView(variable = 'Dox',
        ...                  statistic = 'MeanSDByDox',
        ...                  xfeature = 'Geo.Mean',
        ...                  xscale = 'log',
        ...                  yfeature = 'Geo.SD',
        ...                  yscale = 'log').plot(ex2)
    """
    
    # traits   
    id = Constant("cytoflow.view.stats2d")
    friendly_id = Constant("2D Statistics View")
            
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
        xscale = kwargs.pop('xscale')
        yscale = kwargs.pop('yscale')
        
        capsize = kwargs.pop('capsize', None)
        
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            
            xlim = (data[self.xfeature].min(), data[self.xfeature].max())
            if self.xerror_low and self.xerror_high:
                xlim = (data[self.xerror_low].min(), data[self.xerror_high].max())
            
            span = xlim[1] - xlim[0]
            xlim = (xlim[0] - 0.05 * span, xlim[1] + 0.05 * span)
            xlim = (xscale.clip(xlim[0]), xscale.clip(xlim[1]))
                      
        ylim = kwargs.pop("ylim", None)
        if ylim is None:
            
            ylim = (data[self.yfeature].min(), data[self.yfeature].max())
            if self.yerror_low and self.yerror_high:
                ylim = (data[self.yerror_low].min(), data[self.yerror_high].max())
            
            span = ylim[1] - ylim[0]
            ylim = (ylim[0] - 0.05 * span, ylim[1] + 0.05 * span)
            ylim = (yscale.clip(ylim[0]), yscale.clip(ylim[1]))
        
        # plot the error bars first so the axis labels don't get overwritten
        if self.xerror_low and self.xerror_high:
            grid.map(_x_error_bars, self.xfeature, self.yfeature, self.xerror_low, 
                     self.xerror_high, capsize = capsize)
            
        if self.yerror_low and self.yerror_high:
            grid.map(_y_error_bars, self.xfeature, self.yfeature, self.yerror_low,
                     self.yerror_high, capsize = capsize)

        grid.map(plt.plot, self.xfeature, self.yfeature, **kwargs)
        
        return dict(xscale = xscale,
                    xlim = xlim,
                    yscale = yscale,
                    ylim = ylim)


def _y_error_bars(x, y, yerr_low, yerr_high, ax = None, color = None, errwidth = None, capsize = None, **kwargs):
    
    if errwidth is not None:
        kwargs.setdefault("lw", errwidth)
    else:
        kwargs.setdefault("lw", mpl.rcParams["lines.linewidth"] * 1.8)

    if capsize is not None:
        kwargs['marker'] = '_'
        kwargs['markersize'] = capsize * 2
        kwargs['markeredgewidth'] = kwargs['lw']
        
    for x_i, lo_i, hi_i in zip(x, yerr_low, yerr_high):
        plt.plot((x_i, x_i), (lo_i, hi_i), color = color, **kwargs)
    
def _x_error_bars(x, y, xerr_low, xerr_high, ax = None, color = None, errwidth = None, capsize = None, **kwargs):

    
    if errwidth is not None:
        kwargs.setdefault("lw", errwidth)
    else:
        kwargs.setdefault("lw", mpl.rcParams["lines.linewidth"] * 1.8)
        
    if capsize is not None:
        kwargs['marker'] = '|'
        kwargs['markersize'] = capsize * 2
        kwargs['markeredgewidth'] = kwargs['lw']

        
    for y_i, lo_i, hi_i in zip(y, xerr_low, xerr_high):
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