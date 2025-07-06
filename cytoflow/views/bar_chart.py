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
cytoflow.views.bar_chart
------------------------

Plot a bar chart from a statistic.

`BarChartView` -- the `IView` class that makes the plot.
"""

from traits.api import provides, Constant

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import cytoflow.utility as util
from .i_view import IView
from .base_views import Base1DStatisticsView

@provides(IView)
class BarChartView(Base1DStatisticsView):
    """
    Plots a bar chart of some summary statistic
    
    Attributes
    ----------
    
    Examples
    --------
    
    Make a little data set.
    
    .. plot::
        :context: close-figs
            
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
        
    Add a threshold gate
    
    .. plot::
        :context: close-figs
    
        >>> ex2 = flow.ThresholdOp(name = 'Threshold',
        ...                        channel = 'Y2-A',
        ...                        threshold = 2000).apply(ex)
        
    Add a statistic
    
    .. plot::
        :context: close-figs

        >>> ex3 = flow.ChannelStatisticOp(name = "ByDox",
        ...                               channel = "Y2-A",
        ...                               by = ['Dox', 'Threshold'],
        ...                               function = len).apply(ex2) 
    
    Plot the bar chart
    
    .. plot::
        :context: close-figs
        
        >>> flow.BarChartView(statistic = "ByDox",
        ...                   variable = "Dox",
        ...                   feature = 'Y2-A',
        ...                   huefacet = "Threshold").plot(ex3)
        
    """
    
    # traits   
    id = Constant("cytoflow.view.barchart")
    friendly_id = Constant("Bar Chart") 
        
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce.  The values returned can be passed to "plot".
        """
                
        return super().enum_plots(experiment)
        
        
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot a bar chart
        
        Parameters
        ----------
            
        color : a matplotlib color
            Sets the colors of all the bars, even if there is a hue facet
            
        errwidth : scalar
            The width of the error bars, in points
            
        errcolor : a matplotlib color
            The color of the error bars
            
        capsize : scalar
            The size of the error bar caps, in points
            
        Notes
        -----
        
        Other ``kwargs`` are passed to `matplotlib.axes.Axes.bar <https://matplotlib.org/devdocs/api/_as_gen/matplotlib.axes.Axes.bar.html>`_

        """

        super().plot(experiment, plot_name, **kwargs)
        
    def _grid_plot(self, experiment, grid, cmap, **kwargs):
                 
        # because the bottom of a bar chart is "0", masking out bad
        # values on a log scale doesn't work.  we must clip instead.
        orientation = kwargs.pop('orientation', 'vertical')
        
        # statistic scale
        scale = kwargs.pop('scale')
        
        if scale.name == "log":
            scale.mode = "clip"
            
        # limits
        lim = kwargs.pop('lim', None)
                      
        if orientation == 'vertical':
            map_args = [self.variable, self.feature]
        else:
            map_args = [self.feature, self.variable]
        
        if self.huefacet:
            map_args.append(self.huefacet)  
        
        if self.error_low and self.error_high:
            map_args.append(self.error_low)
            map_args.append(self.error_high)
            
        print(kwargs)
                        
        grid.map_dataframe(_barplot, 
                           *map_args,
                           feature = self.feature,
                           variable = self.variable,
                           huefacet = self.huefacet if self.huefacet else None,
                           error_low = self.error_low if self.error_low else None,
                           error_high = self.error_high if self.error_high else None,
                           orientation = orientation,
                           grid = grid,
                           **kwargs)
        
        if orientation == 'horizontal':
            return dict(xscale = scale,
                        xlim = lim)
        else:
            return dict(yscale = scale,
                        ylim = lim)
            
def _barplot(*args, data, feature, variable, huefacet, error_low, error_high, orientation, grid, **kwargs):
    """ 
    A custom barchart function.  This is assembled from pieces cobbled
    together from seaborn v0.7.1.
    """

    # figure out the categories from the GRID data
    variable_categories = list(grid.data[variable].unique())
    # hue_categories = list(grid.data[huefacet].unique()) if huefacet else []

    # plot the bars
    width = kwargs.pop('width', 0.8)

    ax = plt.gca()    
    err_kws = {}
    errwidth = kwargs.pop('errwidth', None)
    if errwidth:
        err_kws['lw'] = errwidth
    else:
        err_kws['lw'] = mpl.rcParams["lines.linewidth"]
         
    errcolor = kwargs.pop('errcolor', '0.2')
    capsize = kwargs.pop('capsize', None)

    # Get the right matplotlib function depending on the orientation
    barfunc = ax.bar if orientation == "vertical" else ax.barh
    
    # Figure out the bar offset  
    barpos = [variable_categories.index(data[variable].iat[i]) for i in range(len(data))]
    
    if huefacet:
        hue_names = grid.hue_names
        hue_level = data[huefacet].iloc[0]
        hue_idx = hue_names.index(hue_level)
        hue_offsets = np.linspace(0, width - (width / len(hue_names)), len(hue_names))
        hue_offsets -= hue_offsets.mean()
        nested_width = width / len(hue_names) * 0.98
    
        offpos = barpos + hue_offsets[hue_idx]
        barfunc(offpos,
                data[feature], 
                nested_width,
                align="center",
                **kwargs)
    
        if error_low and error_high:
            interval_low = data[error_low]
            interval_high = data[error_high]
            errcolors = [errcolor] * len(offpos)
            _draw_confints(ax,
                           offpos,
                           data[data[huefacet] == hue_level][feature],
                           interval_low,
                           interval_high,
                           errcolors,
                           orientation,
                           errwidth = errwidth,
                           capsize = capsize)
    
    else:
        barfunc(barpos, data[feature], width, align="center", **kwargs)
         
        if error_low and error_high:
            interval_low = data[error_low]
            interval_high = data[error_high]
            errcolors = [errcolor] * len(barpos)
            _draw_confints(ax,
                           barpos,
                           data[feature],
                           interval_low,
                           interval_high,
                           errcolors,
                           orientation,
                           errwidth = errwidth,
                           capsize = capsize)

    if orientation == "vertical":
        ax.set_xticks(np.arange(len(variable_categories)))
        ax.set_xticklabels(variable_categories)
    else:
        ax.set_yticks(np.arange(len(variable_categories)))
        ax.set_yticklabels(variable_categories)
 
    if orientation == "vertical":
        ax.xaxis.grid(False)
        ax.set_xlim(-.5, len(variable_categories) - .5)
    else:
        ax.yaxis.grid(False)
        ax.set_ylim(-.5, len(variable_categories) - .5)  
            

def _draw_confints(ax, at_group, stat, int_low, int_high, colors, 
                   orient, errwidth=None, capsize=None, **kws):
 
    if errwidth is not None:
        kws.setdefault("lw", errwidth)
    else:
        kws.setdefault("lw", mpl.rcParams["lines.linewidth"] * 1.8)
 
    for at, lo, hi, color in zip(at_group,
                                 int_low,
                                 int_high,
                                 colors):
        if orient == "vertical":
            if capsize is not None:
                kws['marker'] = '_'
                kws['markersize'] = capsize * 2
                kws['markeredgewidth'] = kws['lw']
            ax.plot([at, at], [lo, hi], color=color, **kws)
        else:
            if capsize is not None:
                kws['marker'] = '|'
                kws['markersize'] = capsize * 2
                kws['markeredgewidth'] = kws['lw']
            ax.plot([lo, hi], [at, at], color=color, **kws)


util.expand_class_attributes(BarChartView)
util.expand_method_parameters(BarChartView, BarChartView.plot)