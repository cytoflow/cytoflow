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

from traits.api import HasStrictTraits, Tuple, Str, provides
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns
import pandas as pd

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class Stats1DView(HasStrictTraits):
    """
    Plot a statistic.  The value of the statistic will be plotted on the
    Y axis; a numeric conditioning variable must be chosen for the X axis.
    Every variable in the statistic must be specified as either the `variable`
    or one of the plot facets.
    
    Attributes
    ----------
    name : Str
        The plot's name 
        
    statistic : Tuple(Str, Str)
        The statistic to plot.  The first element is the name of the module that
        added the statistic, and the second element is the name of the statistic.
    
    variable : Str
        the name of the conditioning variable to put on the X axis.  Must be
        numeric (float or int).
        
    xscale : Enum("linear", "log") (default = "linear")
        The scale to use on the X axis
        
    yscale : Enum("linear", "log", "logicle") (default = "linear")
        The scale to use on the Y axis
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        
    yfacet : Str
        the conditioning variable for vertical subplots
        
    huefacet : 
        the conditioning variable for color.
        
    huescale :
        the scale to use on the "hue" axis, if there are many values of
        the hue facet.
        
    error_statistic : Tuple(Str, Str)
        A statistic to use to draw error bars; the bars are +- the value of
        the statistic.
        
    subset : String
        Passed to pandas.DataFrame.query(), to get a subset of the statistic
        before we plot it.

        
    Examples
    --------
    
    Assume we want a Dox induction curve in a transient transfection experiment.  
    We have induced several wells with different amounts of Dox and the output
    of the Dox-inducible channel is "Pacific Blue-A".  We have a constitutive
    expression channel in "PE-Tx-Red-YG-A". We want to bin all the data by
    constitutive expression level, then plot the dose-response (geometric mean)
    curve in each bin. 
    
    >>> ex_bin = flow.BinningOp(name = "CFP_Bin",
    ...                         channel = "PE-Tx-Red-YG-A",
    ...                         scale = "log",
    ...                         bin_width = 0.1).apply(ex)
    >>> ex_stat = flow.ChannelStatisticOp(name = "DoxCFP",
    ...                                   by = ["Dox", "CFP_Bin"],
    ...                                   channel = "Pacific Blue-A",
    ...                                   function = flow.geom_mean).apply(ex_bin)
    >>> view = flow.Stats1DView(name = "Dox vs IFP",
    ...                         statistic = ("DoxCFP", "geom_mean"),
    ...                         variable = "Dox",
    ...                         xscale = "log",
    ...                         huefacet = "CFP_Bin").plot(ex_stat)
    >>> view.plot(ex_stat)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.stats1d"
    friendly_id = "1D Statistics View" 
    
    REMOVED_ERROR = "Statistics have changed dramatically in 0.5; please see the documentation"
    by = util.Removed(err_string = REMOVED_ERROR)
    yfunction = util.Removed(err_string = REMOVED_ERROR)
    ychannel = util.Removed(err_string = REMOVED_ERROR)
    xvariable = util.Deprecated(new = "variable")
    
    name = Str
    statistic = Tuple(Str, Str)
    variable = Str
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    xfacet = Str
    yfacet = Str
    huefacet = Str
    huescale = util.ScaleEnum # TODO - make this actually work
    
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
        """Plot a chart"""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.statistic:
            raise util.CytoflowViewError("Statistic not set")
        
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
        
        if self.subset:
            try:
                # TODO - either sanitize column names, or check to see that
                # all conditions are valid Python variables
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
            raise util.CytoflowViewError("X variable not set")
            
        if self.variable not in experiment.conditions:
            raise util.CytoflowViewError("X variable {0} not in the experiment"
                                    .format(self.variable))
                        
        if self.variable not in names:
            raise util.CytoflowViewError("X variable {} is not a statistic index; "
                                         "must be one of {}".format(self.variable, names))
                
        if experiment.conditions[self.variable].dtype.kind not in "biufc": 
            raise util.CytoflowViewError("X variable {0} isn't numeric"
                                    .format(self.variable))
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} not in the experiment")
        
        if self.xfacet and self.xfacet not in names:
            raise util.CytoflowViewError("X facet {} is not a statistic index; "
                                         "must be one of {}".format(self.xfacet, names))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment")
        
        if self.yfacet and self.yfacet not in names:
            raise util.CytoflowViewError("Y facet {} is not a statistic index; "
                                         "must be one of {}".format(self.yfacet, names))
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise util.CytoflowViewError("Hue facet {0} not in the experiment")   
        
        if self.huefacet and self.huefacet not in names:
            raise util.CytoflowViewError("Hue facet {} is not a statistic index; "
                                         "must be one of {}".format(self.huefacet, names))  
            
        col_wrap = kwargs.pop('col_wrap', None)
        
        if col_wrap and self.yfacet:
            raise util.CytoflowViewError("Can't set yfacet and col_wrap at the same time.") 
        
        if col_wrap and not self.xfacet:
            raise util.CytoflowViewError("Must set xfacet to use col_wrap.")
            
        facets = filter(lambda x: x, [self.variable, self.xfacet, self.yfacet, self.huefacet])
        
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
        
        kwargs.setdefault('antialiased', True)  
        
        cols = col_wrap if col_wrap else \
               len(data[self.xfacet].unique()) if self.xfacet else 1
                  
        grid = sns.FacetGrid(data,
                             size = (6 / cols),
                             aspect = 1.5,
                             col = (self.xfacet if self.xfacet else None),
                             row = (self.yfacet if self.yfacet else None),
                             hue = (self.huefacet if self.huefacet else None),
                             col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                             row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                             hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                             col_wrap = col_wrap,
                             legend_out = False,
                             sharex = False,
                             sharey = False)
        
        xscale = util.scale_factory(self.xscale, experiment, condition = self.variable) 
        yscale = util.scale_factory(self.yscale, experiment, statistic = self.statistic)
        
        for ax in grid.axes.flatten():
            ax.set_xscale(self.xscale, **xscale.mpl_params)
            ax.set_yscale(self.yscale, **yscale.mpl_params)

        # plot the error bars first so the axis labels don't get overwritten
        if error_stat is not None:
            grid.map(_error_bars, self.variable, stat.name, error_name, **kwargs)
        
        grid.map(plt.plot, self.variable, stat.name, **kwargs)
        
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
        
        # if we have a hue facet and a lot of hues, make a color bar instead
        # of a super-long legend.
        
        if self.huefacet:
            current_palette = mpl.rcParams['axes.color_cycle']
            if util.is_numeric(experiment.data[self.huefacet]) and \
               len(grid.hue_names) > len(current_palette):
                
                plot_ax = plt.gca()
                cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
                                                                   n_colors = len(grid.hue_names)))
                cax, kw = mpl.colorbar.make_axes(plt.gca())
                norm = mpl.colors.Normalize(vmin = np.min(grid.hue_names), 
                                            vmax = np.max(grid.hue_names), 
                                            clip = False)
                mpl.colorbar.ColorbarBase(cax, 
                                          cmap = cmap, 
                                          norm = norm,
                                          label = self.huefacet, 
                                          **kw)
                plt.sca(plot_ax)
            else:
                grid.add_legend(title = self.huefacet)
                
        if unused_names and plot_name:
            plt.title("{0} = {1}".format(unused_names, plot_name))
                
        plt.ylabel(self.statistic)
                
def _error_bars(x, y, yerr, ax = None, color = None, **kwargs):
    
    if isinstance(yerr.iloc[0], tuple):
        lo = [ye[0] for ye in yerr]
        hi = [ye[1] for ye in yerr]
    else:
        lo = [y.iloc[i] - ye for i, ye in yerr.reset_index(drop = True).iteritems()]
        hi = [y.iloc[i] + ye for i, ye in yerr.reset_index(drop = True).iteritems()]

    plt.vlines(x, lo, hi, color = color, **kwargs)
    

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
    
    s = flow.Stats1DView()
    s.by = "Dox"
    s.ychannel = "Y2-A"
    s.yfunction = np.mean
    s.huefacet = "Y2-A+"
    
    plt.ioff()
    s.plot(ex2)
    plt.show()