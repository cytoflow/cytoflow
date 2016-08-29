#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

from __future__ import division, absolute_import

from warnings import warn

from traits.api import HasStrictTraits, Str, provides, Callable, Property, Enum
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class BarChartView(HasStrictTraits):
    """Plots a bar chart of some summary statistic
    
    Attributes
    ----------
    name : Str
        The bar chart's name 
    
    channel : Str
        the name of the channel we're summarizing 
        
    scale : Enum("linear", "log", "logicle") (default = "linear")
        The scale to use on the Y axis.
        
    variable : Str
        the name of the conditioning variable to group the chart's bars

    function : Callable (1D numpy.ndarray --> float)
        per facet, call this function to summarize the data.  takes a single
        parameter, a 1-dimensional numpy.ndarray, and returns a single float. 
        useful suggestions: np.mean, cytoflow.geom_mean
        
    error_bars : Str
        Draw error bars?  If the name of a condition, subdivide each data set
        further by the condition, apply `function` to each subset, then 
        apply `error_function` (below) to the values of `function` and plot
        that as the error bars.  If `data`, then apply `error_function` to
        the same data subsets that `function` was applied to, and plot those
        as error bars.
        
    error_function : Callable (list-like --> float or (float, float))
        for each group/subgroup subset, call this function to compute the 
        error bars.  must return a single float or a (low, high) tuple.  whether
        it is called on the data or the summary function is determined by the 
        value of *error_bars*
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        
    yfacet : Str
        the conditioning variable for vertical subplots
        
    huefacet : Str
        the conditioning variable to make multiple bar colors
        
    orientation : Enum("horizontal", "vertical")
        do we plot the bar chart horizontally or vertically?
        TODO - waiting on seaborn v0.6

    subset : Str
        a string passed to pandas.DataFrame.query() to subset the data before 
        we plot it.
        
    Examples
    --------
    >>> bar = flow.BarChartView()
    >>> bar.name = "Bar Chart"
    >>> bar.channel = 'Y2-A'
    >>> bar.variable = 'Y2-A+'
    >>> bar.huefacet = 'Dox'
    >>> bar.function = len
    >>> bar.plot(ex)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.barchart"
    friendly_id = "Bar Chart" 
    
    name = Str
    channel = Str
    scale = util.ScaleEnum
    by = Property
    variable = Str
    function = Callable
    orientation = Enum("vertical", "horizontal")
    xfacet = Str
    yfacet = Str
    huefacet = Str
    error_bars = Str
    error_function = Callable
    subset = Str
    
    def _get_by(self):
        warn("'by' is deprecated; please use 'variable'",
             util.CytoflowViewWarning)
        return self.variable
 
    def _set_by(self, val):
        warn("'by' is deprecated; please use 'variable'",
             util.CytoflowViewWarning)
        self.variable = val
        
    def plot(self, experiment, **kwargs):
        """Plot a bar chart"""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")

        if not self.channel:
            raise util.CytoflowViewError("Channel not specified")
        
        if self.channel not in experiment.data:
            raise util.CytoflowViewError("Channel {0} isn't in the experiment"
                                    .format(self.channel))
        
        if not self.variable:
            raise util.CytoflowViewError("variable not specified")
        
        if not self.variable in experiment.conditions:
            raise util.CytoflowViewError("Variable {0} isn't in the experiment")
        
        if not self.function:
            raise util.CytoflowViewError("Function not specified")
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} isn't in the experiment"
                                    .format(self.xfacet))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} isn't in the experiment"
                                    .format(self.yfacet))

        if self.huefacet and self.huefacet not in experiment.conditions:
            raise util.CytoflowViewError("Hue facet {0} isn't in the experiment"
                                    .format(self.huefacet))
            
        if self.error_bars and self.error_bars != "data" \
                           and self.error_bars not in experiment.conditions:
            raise util.CytoflowViewError("error_bars must be either 'data' or "
                                         "a condition in the experiment")            
        
        if self.error_bars and not self.error_function:
            raise util.CytoflowViewError("didn't set an error function")
        
        if self.subset:
            try:
                data = experiment.query(self.subset).data.reset_index()
            except:
                raise util.CytoflowViewError("Subset string {0} isn't valid"
                                        .format(self.subset))
                            
            if len(data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
            
        # get the scale
        scale = util.scale_factory(self.scale, experiment, self.channel)
                        
        g = sns.FacetGrid(data, 
                          size = 6,
                          aspect = 1.5,
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          legend_out = False,
                          sharex = False,
                          sharey = False)
                
        # because the bottom of a bar chart is "0", masking out bad
        # values on a log scale doesn't work.  we must clip instead.
        if self.scale == "log":
            scale.mode = "clip"
                
        # set the scale for each set of axes; can't just call plt.xscale() 
        for ax in g.axes.flatten():
            if self.orientation == 'horizontal':
                ax.set_xscale(self.scale, **scale.mpl_params)  
            else:
                ax.set_yscale(self.scale, **scale.mpl_params)  
                
        map_args = [self.channel, self.variable]
        if self.huefacet:
            map_args.append(self.huefacet)
        if self.error_bars and self.error_bars != "data":
            map_args.append(self.error_bars)
            
        g.map(_barplot, 
              *map_args,
              view = self,
              **kwargs)
        
        if self.huefacet:
            labels = np.sort(data[self.huefacet].unique())
            labels = [str(x) for x in labels]
            g.add_legend(title = self.huefacet, label_order = labels)
            
# in Py3k i could have named arguments after *args, but not in py2.  :-(
def _barplot(*args, **kwargs):
    """ 
    A custom barchart function.  This is assembled from pieces cobbled
    together from seaborn v0.7.1.
    """
     
    data = pd.DataFrame({s.name: s for s in args})
    view = kwargs.pop('view')

    # discard the 'color' we were passed by FacetGrid
    kwargs.pop('color', None)
 
    # group the data and compute the summary statistic
    group_vars = [view.variable]
    if view.huefacet: group_vars.append(view.huefacet)
    
    g = data.groupby(by = group_vars)
    statistic = g[view.channel].aggregate(view.function).reset_index()
    categories = util.categorical_order(statistic[view.variable])
    
    # compute the error statistic
    if view.error_bars:
        if view.error_bars == 'data':
            # compute the error statistic on the same subsets as the summary
            # statistic
            error_stat = g[view.channel].aggregate(view.error_function).reset_index()
        else:
            # subdivide the data set further by the error_bars condition
            err_vars = list(group_vars)
            err_vars.append(view.error_bars)
            
            # apply the summary statistic to each subgroup
            data_g = data.groupby(by = err_vars)
            data_stat = data_g[view.channel].aggregate(view.function).reset_index()
            
            # apply the error function to the summary statistics
            err_g = data_stat.groupby(by = group_vars)
            error_stat = err_g[view.channel].aggregate(view.error_function).reset_index()
    
    # figure out the colors
    if view.huefacet:
        hue_names = util.categorical_order(data[view.huefacet])
        n_colors = len(hue_names)
    else:
        hue_names = None
        n_colors = len(statistic) 
        
    current_palette = mpl.rcParams['axes.color_cycle']
    if n_colors <= len(current_palette):
        colors = sns.color_palette(n_colors = n_colors)
    else:
        colors = sns.husl_palette(n_colors, l=.7)
    
    colors = sns.color_palette(colors)
 
    # plot the bars
    width = kwargs.pop('width', 0.8)
    ax = kwargs.pop('ax', None)
    
    err_kws = {}
    errwidth = kwargs.pop('errwidth', None)
    if errwidth:
        err_kws['lw'] = errwidth
    else:
        err_kws['lw'] = mpl.rcParams["lines.linewidth"] * 1.8
        
    errcolor = kwargs.pop('errcolor', '0.2')
    capsize = kwargs.pop('capsize', None)

    if ax is None:
        ax = plt.gca()

    # Get the right matplotlib function depending on the orientation
    barfunc = ax.bar if view.orientation == "vertical" else ax.barh
    barpos = np.arange(len(categories))
    
    if view.huefacet:
        hue_offsets = np.linspace(0, width - (width / n_colors), n_colors)
        hue_offsets -= hue_offsets.mean()
        nested_width = width / len(hue_names) * 0.98
        for j, hue_level in enumerate(hue_names):
            offpos = barpos + hue_offsets[j]
            barfunc(offpos,
                    statistic[statistic[view.huefacet] == hue_level][view.channel], 
                    nested_width,
                    color=colors[j], 
                    align="center",
                    label=hue_level, 
                    **kwargs)
                
            if view.error_bars:
                confint = error_stat[error_stat[view.huefacet] == hue_level][view.channel]
                errcolors = [errcolor] * len(offpos)
                _draw_confints(ax,
                               offpos,
                               statistic[statistic[view.huefacet] == hue_level][view.channel],
                               confint,
                               errcolors,
                               view.orientation,
                               errwidth = errwidth,
                               capsize = capsize)
                
    else:
        barfunc(barpos, statistic[view.channel], width,
                color=colors, align="center", **kwargs)
        
        if view.error_bars:
            confint = error_stat[view.channel]
            errcolors = [errcolor] * len(barpos)
            _draw_confints(ax,
                           barpos,
                           statistic[view.channel],
                           confint,
                           errcolors,
                           view.orientation,
                           errwidth = errwidth,
                           capsize = capsize)

    # do axes
    if view.orientation == "vertical":
        xlabel, ylabel = view.variable, view.channel
    else:
        xlabel, ylabel = view.channel, view.variable

    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)

    if view.orientation == "vertical":
        ax.set_xticks(np.arange(len(categories)))
        ax.set_xticklabels(categories)
    else:
        ax.set_yticks(np.arange(len(categories)))
        ax.set_yticklabels(categories)

    if view.orientation == "vertical":
        ax.xaxis.grid(False)
        ax.set_xlim(-.5, len(categories) - .5)
    else:
        ax.yaxis.grid(False)
        ax.set_ylim(-.5, len(categories) - .5)

#     if hue_names is not None:
#         leg = ax.legend(loc="best")
#         if view.huefacet is not None:
#             leg.set_title(view.huefacet)
#  
#             # Set the title size a roundabout way to maintain
#             # compatability with matplotlib 1.1
#             try:
#                 title_size = mpl.rcParams["axes.labelsize"] * .85
#             except TypeError:  # labelsize is something like "large"
#                 title_size = mpl.rcParams["axes.labelsize"]
#             prop = mpl.font_manager.FontProperties(size=title_size)
#             leg._legend_title_box._text.set_font_properties(prop)   
            
    return ax 


def _draw_confints(ax, at_group, stat, confints, colors, 
                   orientation, errwidth=None, capsize=None, **kws):

    if errwidth is not None:
        kws.setdefault("lw", errwidth)
    else:
        kws.setdefault("lw", mpl.rcParams["lines.linewidth"] * 1.8)
        
    if isinstance(confints.iloc[0], tuple):
        ci_lo = [x[0] for x in confints]
        ci_hi = [x[1] for x in confints]
    else:
        ci_lo = [stat.iloc[i] - x for i, x in confints.reset_index(drop = True).iteritems()]
        ci_hi = [stat.iloc[i] + x for i, x in confints.reset_index(drop = True).iteritems()]

    for at, lo, hi, color in zip(at_group,
                                 ci_lo,
                                 ci_hi,
                                 colors):
        if orientation == "vertical":
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
