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

from traits.api import HasStrictTraits, Str, provides, Callable, Enum
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class Stats1DView(HasStrictTraits):
    """
    Divide the data up by `by`, then plot a line plot of `by`
    on the x axis with a summary statistic `yfunction` of the same data in 
    `ychannel` on the y axis. 
    
    Attributes
    ----------
    name : Str
        The plot's name 
    
    xvariable : Str
        the name of the conditioning variable to put on the X axis
        
    xscale : Enum("linear", "log") (default = "linear")
        The scale to use on the X axis

    ychannel : Str
        Apply `yfunction` to `ychannel` for each value of `by`
        
    yscale : Enum("linear", "log", "logicle") (default = "linear")
        The scale to use on the Y axis
        
    yfunction : Callable (list-like --> float)
        What summary function to apply to `ychannel`
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        
    yfacet : Str
        the conditioning variable for vertical subplots
        
    huefacet : 
        the conditioning variable for color.
        
    y_error_bars : Str
        draw error bars?  if the name of a condition, subdivide each data
        set further by the condition, apply 'yfunction' to each subset, then
        apply `y_error_function` to the values and plot them as error bars.
        if `data`, then apply `y_error_function` to the same data subsets that
        `function` was applied to and plot those as error bars.    
        
    y_error_function : Callable (list-like --> (float, float))
        for each group/subgroup subset, call this function to compute the 
        error bars.  whether it is called on the data or the summary function
        is determined by the value of `y_error_bars`
        
    subset : Str
        a string passed to Experiment.query() to subset the data before 
        we plot it.
        
    Examples
    --------
    
    Assume we want a Dox induction curve in a transient transfection experiment.  
    We have induced several wells with different amounts of Dox and the output
    of the Dox-inducible channel is "Pacific Blue-A".  We have a constitutive
    expression channel in "PE-Tx-Red-YG-A". We want to bin all the data by
    constitutive expression level, then plot the dose-response (geometric mean)
    curve in each bin. 
    
    >>> ex_binned = flow.BinningOp(name = "CFP_Bin",
    ...                            channel = "PE-Tx-Red-YG-A",
    ...                            scale = "log",
    ...                            bin_width = 0.1).apply(ex)
    >>> view = Stats1DView(name = "Dox vs IFP",
    ...                    xchannel = "Dox",
    ...                    ychannel = "Pacific Blue-A",
    ...                    huefacet = "CFP_Bin",
    ...                    yfunction = flow.geom_mean)
    >>> view.plot(ex_binned)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.stats1d"
    friendly_id = "1D Statistics View" 
    
    name = Str
    xvariable = Str
    xscale = Enum("linear", "log")
    ychannel = Str
    yscale = util.ScaleEnum
    yfunction = Callable
    xfacet = Str
    yfacet = Str
    huefacet = Str
    
    y_error_bars = Str
    y_error_function = Callable

    subset = Str
    
    def plot(self, experiment, **kwargs):
        """Plot a bar chart"""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.xvariable:
            raise util.CytoflowViewError("X variable not set")
            
        if self.xvariable not in experiment.conditions:
            raise util.CytoflowViewError("X variable {0} not in the experiment"
                                    .format(self.xvariable))
        
        if not (experiment.conditions[self.xvariable] == "float" or
                experiment.conditions[self.xvariable] == "int"):
            raise util.CytoflowViewError("X variable {0} isn't numeric"
                                    .format(self.xvariable))

        if not self.ychannel:
            raise util.CytoflowViewError("Y channel isn't set.")
        
        if self.ychannel not in experiment.data:
            raise util.CytoflowViewError("Y channel {0} isn't in the experiment"
                                    .format(self.ychannel))
        
        if not self.yfunction:
            raise util.CytoflowViewError("Y summary function isn't set")
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} not in the experiment")
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment")
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise util.CytoflowViewError("Hue facet {0} not in the experiment")        
        
        if self.y_error_bars and self.y_error_bars != 'data' \
                             and self.y_error_bars not in experiment.conditions:
            raise util.CytoflowViewError("y_error_bars must be either 'data' or "
                                         "a condition in the experiment") 
            
        if self.y_error_bars and not self.y_error_function:
            raise util.CytoflowViewError("didn't set an error function")
                
        kwargs.setdefault('antialiased', True)

        if self.subset:
            try:
                data = experiment.query(self.subset).data.reset_index()
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                            
            if len(data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
            
        group_vars = [self.xvariable]
        if self.xfacet:
            group_vars.append(self.xfacet)
        if self.yfacet:
            group_vars.append(self.yfacet)
        if self.huefacet:
            group_vars.append(self.huefacet)
            
        g = data.groupby(by = group_vars)
        plot_data = g[self.ychannel].aggregate(self.yfunction).reset_index()
  
        # compute the error statistic
        if self.y_error_bars:
            if self.y_error_bars == 'data':
                # compute the error statistic on the same subsets as the summary
                # statistic
                error_stat = g[self.ychannel].aggregate(self.y_error_function).reset_index()
            else:
                # subdivide the data set further by the error_bars condition
                err_vars = list(group_vars)
                err_vars.append(self.y_error_bars)
                
                # apply the summary statistic to each subgroup
                data_g = data.groupby(by = err_vars)
                data_stat = data_g[self.ychannel].aggregate(self.yfunction).reset_index()
                
                # apply the error function to the summary statistics
                err_g = data_stat.groupby(by = group_vars)
                error_stat = err_g[self.ychannel].aggregate(self.y_error_function).reset_index()
        
            y_err_name = util.random_string(6)
            plot_data[y_err_name] = error_stat[self.ychannel]
        
  
        grid = sns.FacetGrid(plot_data,
                             size = 6,
                             aspect = 1.5,
                             col = (self.xfacet if self.xfacet else None),
                             row = (self.yfacet if self.yfacet else None),
                             hue = (self.huefacet if self.huefacet else None),
                             col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                             row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                             hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                             legend_out = False,
                             sharex = False,
                             sharey = False)
            
        yscale = util.scale_factory(self.yscale, experiment, self.ychannel)
        
        for ax in grid.axes.flatten():
            ax.set_xscale(self.xscale)
            ax.set_yscale(self.yscale, **yscale.mpl_params)

        # plot the error bars first so the axis labels don't get overwritten
        if self.y_error_bars:
            grid.map(_error_bars, self.xvariable, self.ychannel, y_err_name)
        
        grid.map(plt.plot, self.xvariable, self.ychannel, **kwargs)
        
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
        
        # if we have a hue facet and a lot of hues, make a color bar instead
        # of a super-long legend.
        
        if self.huefacet:
            current_palette = mpl.rcParams['axes.color_cycle']
            if (experiment.conditions[self.huefacet] == "int" or 
                experiment.conditions[self.huefacet] == "float") and \
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