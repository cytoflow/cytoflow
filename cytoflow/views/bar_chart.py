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

from traits.api import HasStrictTraits, Str, provides, Tuple, Enum
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
    
    statistic : Tuple(Str, Str)
        the statistic we're plotting
        
    scale : Enum("linear", "log", "logicle") (default = "linear")
        The scale to use on the Y axis.
        
    variable : Str
        the name of the conditioning variable to group the chart's bars
        
    error_statistic : Tuple(Str, Str)
        if specified, a statistic to draw error bars.  if values are numeric,
        the bars are drawn +/- the value.  if the values are tuples, then
        the first element is the low error and the second element is the
        high error.
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        
    yfacet : Str
        the conditioning variable for vertical subplots
        
    huefacet : Str
        the conditioning variable to make multiple bar colors
        
    orientation : Enum("horizontal", "vertical")
        do we plot the bar chart horizontally or vertically?
        TODO - waiting on seaborn v0.6
        
    subset : String
        Passed to pandas.DataFrame.query(), to get a subset of the statistic
        before we plot it.
        
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
    
    REMOVED_ERROR = "Statistics have changed dramatically in 0.5; please see the documentation"
    channel = util.Removed(err_string = REMOVED_ERROR)
    function = util.Removed(err_string = REMOVED_ERROR)
    error_bars = util.Removed(err_string = REMOVED_ERROR)
    
    by = util.Deprecated(new = 'variable')
        
    name = Str
    statistic = Tuple(Str, Str)
    scale = util.ScaleEnum
    variable = Str
    orientation = Enum("vertical", "horizontal")
    
    xfacet = Str
    yfacet = Str
    huefacet = Str
    
    error_statistic = Tuple(Str, Str)
    subset = Str
            
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce.  The values returned can be passed to "plot".
        """
        
        # TODO - all this is copied from below.  can we abstract it out somehow?
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError("Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
        else:
            stat = experiment.statistics[self.statistic]
            
        if self.error_statistic[0]:
            if self.error_statistic not in experiment.statistics:
                raise util.CytoflowViewError("Can't find the error statistic in the experiment")
            else:
                error_stat = experiment.statistics[self.error_statistic]
        else:
            error_stat = None
         
        if error_stat is not None:
            if not stat.index.equals(error_stat.index):
                raise util.CytoflowViewError("Data statistic and error statistic "
                                             " don't have the same index.")

        data = pd.DataFrame(index = stat.index)
        
        data[stat.name] = stat
                
        if error_stat is not None:
            error_name = util.random_string(6)
            data[error_name] = error_stat 
        else:
            error_name = None
            
        if self.subset:
            try:
                data = data.query(self.subset)
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                
            if len(data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no values"
                                        .format(self.subset))
            
        names = list(data.index.names)
        
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                warn("Only one value for level {}; dropping it.".format(name),
                     util.CytoflowViewWarning)
                data.index = data.index.droplevel(name)
                
        names = list(data.index.names)
                        
        if not self.variable:
            raise util.CytoflowViewError("variable not specified")
        
        if not self.variable in data.index.names:
            raise util.CytoflowViewError("Variable {} isn't in the statistic; "
                                         "must be one of {}"
                                         .format(self.variable, data.index.names))
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} isn't in the experiment"
                                    .format(self.xfacet))
            
        if self.xfacet and self.xfacet not in data.index.names:
            raise util.CytoflowViewError("X facet {} is not a statistic index; "
                                         "must be one of {}".format(self.xfacet, data.index.names))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} isn't in the experiment"
                                    .format(self.yfacet))

        if self.yfacet and self.yfacet not in data.index.names:
            raise util.CytoflowViewError("Y facet {} is not a statistic index; "
                                         "must be one of {}".format(self.yfacet, data.index.names))

        if self.huefacet and self.huefacet not in experiment.conditions:
            raise util.CytoflowViewError("Hue facet {0} isn't in the experiment"
                                    .format(self.huefacet))
            
        if self.huefacet and self.huefacet not in data.index.names:
            raise util.CytoflowViewError("Hue facet {} is not a statistic index; "
                                         "must be one of {}".format(self.huefacet, data.index.names)) 
            
        facets = filter(lambda x: x, [self.variable, self.xfacet, self.yfacet, self.huefacet])
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError("Can't reuse facets")
        
        by = list(set(names) - set(facets))
        
        class plot_enum(object):
            
            def __init__(self, experiment, by):
                self._iter = None
                self._returned = False
                
                if by:
                    self._iter = experiment.data.groupby(by).__iter__()
                
            def __iter__(self):
                return self
            
            def next(self):
                if self._iter:
                    return self._iter.next()[0]
                else:
                    if self._returned:
                        raise StopIteration
                    else:
                        self._returned = True
                        return None
            
        return plot_enum(experiment, by)

        
    def plot(self, experiment, plot_name = None, **kwargs):
        """Plot a bar chart"""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError("Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
        else:
            stat = experiment.statistics[self.statistic]
            
        if self.error_statistic[0]:
            if self.error_statistic not in experiment.statistics:
                raise util.CytoflowViewError("Can't find the error statistic in the experiment")
            else:
                error_stat = experiment.statistics[self.error_statistic]
        else:
            error_stat = None
         
        if error_stat is not None:
            if not stat.index.equals(error_stat.index):
                raise util.CytoflowViewError("Data statistic and error statistic "
                                             " don't have the same index.")

        data = pd.DataFrame(index = stat.index)
        
        data[stat.name] = stat
                
        if error_stat is not None:
            error_name = util.random_string(6)
            data[error_name] = error_stat 
        else:
            error_name = None
            
        if self.subset:
            try:
                data = data.query(self.subset)
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                
            if len(data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no values"
                                        .format(self.subset))
            
        names = list(data.index.names)
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                warn("Only one value for level {}; dropping it.".format(name),
                     util.CytoflowViewWarning)
                data.index = data.index.droplevel(name)
                
        names = list(data.index.names)
                        
        if not self.variable:
            raise util.CytoflowViewError("variable not specified")
        
        if not self.variable in names:
            raise util.CytoflowViewError("Variable {} isn't in the statistic; "
                                         "must be one of {}"
                                         .format(self.variable, names))
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} isn't in the experiment"
                                    .format(self.xfacet))
            
        if self.xfacet and self.xfacet not in names:
            raise util.CytoflowViewError("X facet {} is not a statistic index; "
                                         "must be one of {}".format(self.xfacet, names))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} isn't in the experiment"
                                    .format(self.yfacet))

        if self.yfacet and self.yfacet not in names:
            raise util.CytoflowViewError("Y facet {} is not a statistic index; "
                                         "must be one of {}".format(self.yfacet, names))

        if self.huefacet and self.huefacet not in experiment.conditions:
            raise util.CytoflowViewError("Hue facet {0} isn't in the experiment"
                                    .format(self.huefacet))
            
        if self.huefacet and self.huefacet not in names:
            raise util.CytoflowViewError("Hue facet {} is not a statistic index; "
                                         "must be one of {}".format(self.huefacet, names)) 
            
        col_wrap = kwargs.pop('col_wrap', None)
        
        if col_wrap and self.yfacet:
            raise util.CytoflowViewError("Can't set yfacet and col_wrap at the same time.") 
        
        if col_wrap and not self.xfacet:
            raise util.CytoflowViewError("Must set xfacet to use col_wrap.")
            
        facets = filter(lambda x: x, [self.variable, self.xfacet, self.yfacet, self.huefacet])
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError("Can't reuse facets")
        
        unused_names = list(set(names) - set(facets))

        if unused_names and plot_name is None:
            for plot in self.enum_plots(experiment):
                self.plot(experiment, plot, **kwargs)
            return

        data.reset_index(inplace = True)
        
        if plot_name is not None:
            if plot_name is not None and not unused_names:
                raise util.CytoflowViewError("Plot {} not from plot_enum"
                                             .format(plot_name))
                               
            groupby = data.groupby(unused_names)

            if plot_name not in set(groupby.groups.keys()):
                raise util.CytoflowViewError("Plot {} not from plot_enum"
                                             .format(plot_name))
                
            data = groupby.get_group(plot_name)
            data.reset_index(drop = True, inplace = True)
        
        cols = col_wrap if col_wrap else \
               len(data[self.xfacet].unique()) if self.xfacet else 1
          
        g = sns.FacetGrid(data, 
                          size = (6 / cols),
                          aspect = 1.5,
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          col_wrap = col_wrap,
                          legend_out = False,
                          sharex = True,
                          sharey = True)
        
        scale = util.scale_factory(self.scale, experiment, statistic = self.statistic)
                
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
                
        map_args = [self.variable, stat.name]
        
        if self.huefacet:
            map_args.append(self.huefacet)  
        
        if error_stat is not None:
            map_args.append(error_name)
            
        g.map(_barplot, 
              *map_args,
              view = self,
              stat_name = stat.name,
              error_name = error_name,
              **kwargs)

        # if we have an xfacet, make sure the y scale is the same for each
        fig = plt.gcf()
        fig_y_min = float("inf")
        fig_y_max = float("-inf")
        for ax in fig.get_axes():
            ax_y_min, ax_y_max = ax.get_ylim()
            if ax_y_min < fig_y_min:
                fig_y_min = ax_y_min
            if ax_y_max > fig_y_max:
                fig_y_max = ax_y_max
                
        for ax in fig.get_axes():
            ax.set_ylim(fig_y_min, fig_y_max)
            
        # if we have a yfacet, make sure the x scale is the same for each
        fig = plt.gcf()
        fig_x_min = float("inf")
        fig_x_max = float("-inf")
        
        for ax in fig.get_axes():
            ax_x_min, ax_x_max = ax.get_xlim()
            if ax_x_min < fig_x_min:
                fig_x_min = ax_x_min
            if ax_x_max > fig_x_max:
                fig_x_max = ax_x_max
        
        for ax in fig.get_axes():
            ax.set_xlim(fig_x_min, fig_x_max)
        
        if self.huefacet:
            labels = np.sort(data[self.huefacet].unique())
            labels = [str(x) for x in labels]
            g.add_legend(title = self.huefacet, label_order = labels)
            
        if self.orientation == 'horizontal':
            plt.sca(fig.get_axes()[0])
            plt.xlabel(self.statistic)
        else:
            plt.sca(fig.get_axes()[0])
            plt.ylabel(self.statistic)
            
        if unused_names and plot_name:
            plt.title("{0} = {1}".format(unused_names, plot_name))
            
# in Py3k i could have named arguments after *args, but not in py2.  :-(
def _barplot(*args, **kwargs):
    """ 
    A custom barchart function.  This is assembled from pieces cobbled
    together from seaborn v0.7.1.
    """
         
    data = pd.DataFrame({s.name: s for s in args})
    view = kwargs.pop('view')
    stat_name = kwargs.pop('stat_name', None)
    error_name = kwargs.pop('error_name', None)

    # discard the 'color' we were passed by FacetGrid
    kwargs.pop('color', None)
 
    categories = util.categorical_order(data[view.variable])
    
    # figure out the colors
    if view.huefacet:
        hue_names = util.categorical_order(data[view.huefacet])
        n_colors = len(hue_names)
    else:
        hue_names = None
        n_colors = len(data)
        
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
                    data[data[view.huefacet] == hue_level][stat_name], 
                    nested_width,
                    color=colors[j], 
                    align="center",
                    label=hue_level, 
                    **kwargs)
                
            if error_name:
                confint = data[data[view.huefacet] == hue_level][error_name]
                errcolors = [errcolor] * len(offpos)
                _draw_confints(ax,
                               offpos,
                               data[data[view.huefacet] == hue_level][stat_name],
                               confint,
                               errcolors,
                               view.orientation,
                               errwidth = errwidth,
                               capsize = capsize)
                
    else:
        barfunc(barpos, data[stat_name], width,
                color=colors, align="center", **kwargs)
        
        if error_name:
            confint = data[error_name]
            errcolors = [errcolor] * len(barpos)
            _draw_confints(ax,
                           barpos,
                           data[stat_name],
                           confint,
                           errcolors,
                           view.orientation,
                           errwidth = errwidth,
                           capsize = capsize)

    # do axes
    if view.orientation == "vertical":
        xlabel, ylabel = view.variable, stat_name
    else:
        xlabel, ylabel = stat_name, view.variable

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
