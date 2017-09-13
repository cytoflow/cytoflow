#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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

'''
cytoflow.views.bar_chart
------------------------
'''

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
        
        >>> flow.BarChartView(statistic = ("ByDox", "len"),
        ...                   variable = "Dox",
        ...                   huefacet = "Threshold").plot(ex3)
        
    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.barchart")
    friendly_id = Constant("Bar Chart") 
    
    orientation = util.Removed(err_string = "`orientation` is now a parameter to `plot`")
    
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
        
        orientation : {'vertical', 'horizontal'}
            Sets the orientation to vertical (the default) or horizontal
            
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
        
    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):
                 
        # because the bottom of a bar chart is "0", masking out bad
        # values on a log scale doesn't work.  we must clip instead.
        orient = kwargs.pop('orientation', 'vertical')
        
        # Base1DStatistic uses xscale for the variable and yscale for
        # the statistic.
        
        if yscale.name == "log":
            yscale.mode = "clip"
                
        # set the scale for each set of axes; can't just call plt.xscale() 
        for ax in grid.axes.flatten():
            if orient == 'horizontal':
                ax.set_xscale(yscale.name, **yscale.mpl_params)  
            elif orient == 'vertical':
                ax.set_yscale(yscale.name, **yscale.mpl_params)
            else:
                raise util.CytoflowViewError("'orient' param must be 'h' or 'v'")  
                
        stat = experiment.statistics[self.statistic]
        map_args = [self.variable, stat.name]
        
        if self.huefacet:
            map_args.append(self.huefacet)  
        
        if self.error_statistic[0]:
            error_stat = experiment.statistics[self.error_statistic]
            map_args.append(error_stat.name)
        else:
            error_stat = None
                        
        grid.map(_barplot, 
                 *map_args,
                 view = self,
                 stat_name = stat.name,
                 error_name = error_stat.name if error_stat else None,
                 orient = orient,
                 grid = grid,
                 **kwargs)
        
        return {}
            
def _barplot(*args, view, stat_name, error_name, orient, grid, **kwargs):
    """ 
    A custom barchart function.  This is assembled from pieces cobbled
    together from seaborn v0.7.1.
    """
  
    data = pd.DataFrame({s.name: s for s in args})
    
    categories = util.categorical_order(data[view.variable])
 
    # plot the bars
    width = kwargs.pop('width', 0.8)
    ax = kwargs.pop('ax', None)

    if ax is None:
        ax = plt.gca()
    
    err_kws = {}
    errwidth = kwargs.pop('errwidth', None)
    if errwidth:
        err_kws['lw'] = errwidth
    else:
        err_kws['lw'] = mpl.rcParams["lines.linewidth"] * 1.8
         
    errcolor = kwargs.pop('errcolor', '0.2')
    capsize = kwargs.pop('capsize', None)

    # Get the right matplotlib function depending on the orientation
    barfunc = ax.bar if orient == "vertical" else ax.barh
    barpos = np.arange(len(categories))
    
    if view.huefacet:
        hue_names = grid.hue_names
        hue_level = data[view.huefacet].iloc[0]
        hue_idx = hue_names.index(hue_level)
        hue_offsets = np.linspace(0, width - (width / len(hue_names)), len(hue_names))
        hue_offsets -= hue_offsets.mean()
        nested_width = width / len(hue_names) * 0.98
        
        offpos = barpos + hue_offsets[hue_idx]
        barfunc(offpos,
                data[stat_name], 
                nested_width,
                align="center",
                **kwargs)
                
        if error_name:
            confint = data[error_name]
            errcolors = [errcolor] * len(offpos)
            _draw_confints(ax,
                           offpos,
                           data[data[view.huefacet] == hue_level][stat_name],
                           confint,
                           errcolors,
                           orient,
                           errwidth = errwidth,
                           capsize = capsize)
                
    else:
        barfunc(barpos, data[stat_name], width, align="center", **kwargs)
         
        if error_name:
            confint = data[error_name]
            errcolors = [errcolor] * len(barpos)
            _draw_confints(ax,
                           barpos,
                           data[stat_name],
                           confint,
                           errcolors,
                           orient,
                           errwidth = errwidth,
                           capsize = capsize)

    # do axes
#     if view.orientation == "vertical":
#         xlabel, ylabel = view.variable, stat_name
#     else:
#         xlabel, ylabel = stat_name, view.variable
# 
#     if xlabel is not None:
#         ax.set_xlabel(xlabel)
#     if ylabel is not None:
#         ax.set_ylabel(ylabel)

    if orient == "vertical":
        ax.set_xticks(np.arange(len(categories)))
        ax.set_xticklabels(categories)
    else:
        ax.set_yticks(np.arange(len(categories)))
        ax.set_yticklabels(categories)
 
    if orient == "vertical":
        ax.xaxis.grid(False)
        ax.set_xlim(-.5, len(categories) - .5)
    else:
        ax.yaxis.grid(False)
        ax.set_ylim(-.5, len(categories) - .5)  
            
    return ax 


def _draw_confints(ax, at_group, stat, confints, colors, 
                   orient, errwidth=None, capsize=None, **kws):
 
    if errwidth is not None:
        kws.setdefault("lw", errwidth)
    else:
        kws.setdefault("lw", mpl.rcParams["lines.linewidth"] * 1.8)
         
    if isinstance(confints.iloc[0], tuple):
        ci_lo = [x[0] for x in confints]
        ci_hi = [x[1] for x in confints]
    else:
        ci_lo = [stat.iloc[i] - x for i, x in confints.reset_index(drop = True).items()]
        ci_hi = [stat.iloc[i] + x for i, x in confints.reset_index(drop = True).items()]
 
    for at, lo, hi, color in zip(at_group,
                                 ci_lo,
                                 ci_hi,
                                 colors):
        if orient == "v":
            ax.plot([at, at], [lo, hi], color=color, **kws)
            if capsize is not None:
                ax.plot([at - capsize / 2, at + capsize / 2],
                        [lo, lo], color=color, **kws)
                ax.plot([at - capsize / 2, at + capsize / 2],
                        [hi, hi], color=color, **kws)
        else:
            ax.plot([lo, hi], [at, at], color=color, **kws)
            if capsize is not None:
                ax.plot([lo, lo],
                        [at - capsize / 2, at + capsize / 2],
                        color=color, **kws)
                ax.plot([hi, hi],
                        [at - capsize / 2, at + capsize / 2],
                        color=color, **kws)

util.expand_class_attributes(BarChartView)
util.expand_method_parameters(BarChartView, BarChartView.plot)