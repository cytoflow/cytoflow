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
from traits.api import HasStrictTraits, Str, provides, Tuple
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns
import pandas as pd

from .i_view import IView
import cytoflow.utility as util

@provides(IView)
class Stats2DView(HasStrictTraits):
    """
    Plot two statistics on a scatter plot.  A point (X,Y) is drawn for every
    pair of elements with the same value of `variable`; the X value is from 
    `xstatistic` and the Y value is from `ystatistic`.
    
    Attributes
    ----------
    name : Str
        The plot's name 
    
    variable : Str
        the name of the conditioning variable
        
    xstatistic : Tuple(Str, Str)
        The statistic to plot on the X axis.  Must have the same indices
        as `ystatistic`.
        
    xscale : Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the X axis
    
    ystatistic : Tuple(Str, Str)
       The statistic to plot on the Y axis.  Must have the same indices
       as `xstatistic`.
        
    yscale : Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the Y axis
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        
    yfacet : Str
        the conditioning variable for vertical subplots
        
    huefacet : 
        the conditioning variable for color.
        
    huescale : Enum("linear", "log", "logicle") (default = "linear")
        scale for the hue facet, if there are a lot of hue values.
        
    x_error_statistic, y_error_statistic : Tuple(Str, Str)
        if specified, draw error bars.  must be the name of a statistic,
        with the same indices as `xstatistic` and `ystatistic`.
    
    subset : Str
        What subset of the data to plot?
        
    Examples
    --------
    
    Assume we want an input-output curve for a repressor that's under the
    control of a Dox-inducible promoter.  We have an "input" channel
    `(Dox --> eYFP, FITC-A channel)` and an output channel 
    `(Dox --> repressor --| eBFP, Pacific Blue channel)` as well as a 
    constitutive expression channel (mKate, PE-Tx-Red-YG-A channel). 
    We have induced several wells with different amounts of Dox.  We want 
    to plot the relationship between the input and output channels (binned by 
    input channel intensity) as we vary Dox, faceted by constitutive channel 
    bin.
    
    >>> cfp_bin_op = flow.BinningOp(name = "CFP_Bin",
    ...                             channel = "PE-Tx-Red-YG-A",
    ...                             scale = "log",
    ...                             bin_width = 0.1)
    >>> ifp_bin_op = flow.BinningOp(name = "IFP_Bin",
    ...                             channel = "Pacific Blue-A",
    ...                             scale = "log",
    ...                             bin_width = 0.1).apply(ex_cfp_binned)
    >>> ifp_mean = flow.ChannelStatisticOp(name = "IFP",
    ...                                    channel = "FITC-A",
    ...                                    by = ["IFP_Bin", "CFP_Bin"],
    ...                                    function = flow.geom_mean)
    >>> ofp_mean = flow.ChannelStatisticOp(name = "OFP",
    ...                                    channel = "Pacific_Blue-A",
    ...                                    by = ["IFP_Bin", "CFP_Bin"],
    ...                                    function = flow.geom_mean)
    >>> ex = cfp_bin_op.apply(ex)
    >>> ex = ifp_bin_op.apply(ex)
    >>> ex = ifp_mean.apply(ex)
    >>> ex = ofp_mean.apply(ex)
    >>> view = flow.Stats2DView(name = "IFP vs OFP",
    ...                         variable = "IFP_Bin",
    ...                         xstatistic = ("IFP", "geom_mean"),
    ...                         ystatistic = ("OFP", "geom_mean"),
    ...                         huefacet = "CFP_Bin").plot(ex_ifp_binned)
    >>> view.plot(ex_binned)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.stats2d"
    friendly_id = "2D Statistics View" 

    # deprecated or removed attributes give warnings & errors, respectively
    by = util.Deprecated(new = 'variable', err_string = "'by' is deprecated, please use 'variable'")
    
    STATS_REMOVED = "{} has been removed. Statistics changed dramatically in 0.5; please see the documentation."
    
    xchannel = util.Removed(err_string = STATS_REMOVED)
    xfunction = util.Removed(err_string = STATS_REMOVED)
    ychannel = util.Removed(err_string = STATS_REMOVED)
    yfunction = util.Removed(err_string = STATS_REMOVED)
        
    name = Str
    variable = Str
    xstatistic = Tuple(Str, Str)
    xscale = util.ScaleEnum
    ystatistic = Tuple(Str, Str)
    yscale = util.ScaleEnum

    xfacet = Str
    yfacet = Str
    huefacet = Str
    huescale = util.ScaleEnum # TODO - make this work
    
    x_error_statistic = Tuple(Str, Str)
    y_error_statistic = Tuple(Str, Str)
    
    subset = Str
    
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce.  The values returned can be passed to "plot".
        """
        
        # TODO - all this is copied from below.  can we abstract it out somehow?
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.variable:
            raise util.CytoflowViewError("variable not set")
            
        if self.variable not in experiment.conditions:
            raise util.CytoflowViewError("variable {0} not in the experiment"
                                    .format(self.variable))
            
        if not self.xstatistic:
            raise util.CytoflowViewError("X statistic not set")
        
        if self.xstatistic not in experiment.statistics:
            raise util.CytoflowViewError("Can't find X statistic {} in experiment"
                                         .format(self.ystatistic))
        else:
            xstat = experiment.statistics[self.xstatistic]

        if not self.ystatistic:
            raise util.CytoflowViewError("Y statistic not set")
        
        if self.ystatistic not in experiment.statistics:
            raise util.CytoflowViewError("Can't find Y statistic {} in experiment"
                                         .format(self.ystatistic))
        else:
            ystat = experiment.statistics[self.ystatistic]  
            
        if not xstat.index.equals(ystat.index):
            raise util.CytoflowViewError("X statistic and Y statistic must have "
                                         "the same indices: {}"
                                         .format(xstat.index.names))
             
        if self.x_error_statistic[0]:
            if self.x_error_statistic not in experiment.statistics:
                raise util.CytoflowViewError("X error statistic not in experiment")
            else:
                x_error_stat = experiment.statistics[self.x_error_statistic]
                
            if not x_error_stat.index.equals(xstat.index):
                raise util.CytoflowViewError("X error statistic doesn't have the "
                                             "same indices as the X statistic")
        else:
            x_error_stat = None

        if self.y_error_statistic[0]:
            if self.y_error_statistic not in experiment.statistics:
                raise util.CytoflowViewError("Y error statistic not in experiment")
            else:
                y_error_stat = experiment.statistics[self.y_error_statistic]
                
            if not y_error_stat.index.equals(ystat.index):
                raise util.CytoflowViewError("Y error statistic doesn't have the "
                                             "same indices as the Y statistic")
        else:
            y_error_stat = None

        data = pd.DataFrame(index = xstat.index)
            
        xname = util.random_string(6)
        data[xname] = xstat
        
        yname = util.random_string(6)
        data[yname] = ystat
                 
        if x_error_stat is not None:
            #x_error_data = x_error_stat.reset_index()
            x_error_name = util.random_string(6)
            data[x_error_name] = x_error_stat
            
        if y_error_stat is not None:
            y_error_name = util.random_string(6)
            data[y_error_name] = y_error_stat
            
        if y_error_stat is not None:
            y_error_data = y_error_stat.reset_index()
            y_error_name = util.random_string()
            data[y_error_name] = y_error_data[y_error_stat.name]
            
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
            
        if not self.variable in experiment.conditions:
            raise util.CytoflowViewError("Variable {} not in experiment"
                                         .format(self.variable))
            
        if not self.variable in data.index.names:
            raise util.CytoflowViewError("Variable {} not in statistic; must be one of {}"
                                         .format(self.variable, data.index.names))

        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {} not in the experiment"
                                         .format(self.xfacet))
        
        if self.xfacet and self.xfacet not in data.index.names:
            raise util.CytoflowViewError("X facet {} not in statistics; must be one of {}"
                                         .format(self.xfacet, data.index.names))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {} not in the experiment"
                                         .format(self.yfacet))
            
        if self.yfacet and self.yfacet not in data.index.names:
            raise util.CytoflowViewError("Y facet {} not in statistics; must be one of {}"
                                         .format(self.yfacet, data.index.names))
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise util.CytoflowViewError("Hue facet {} not in the experiment"
                                         .format(self.huefacet))        

        if self.huefacet and self.huefacet not in data.index.names:
            raise util.CytoflowViewError("Hue facet {} not in statistics; must be one of {}"
                                         .format(self.huefacet, data.index.names))
            
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
        
        if not self.variable:
            raise util.CytoflowViewError("variable not set")
            
        if self.variable not in experiment.conditions:
            raise util.CytoflowViewError("variable {0} not in the experiment"
                                    .format(self.variable))
            
        if not self.xstatistic:
            raise util.CytoflowViewError("X statistic not set")
        
        if self.xstatistic not in experiment.statistics:
            raise util.CytoflowViewError("Can't find X statistic {} in experiment"
                                         .format(self.ystatistic))
        else:
            xstat = experiment.statistics[self.xstatistic]

        if not self.ystatistic:
            raise util.CytoflowViewError("Y statistic not set")
        
        if self.ystatistic not in experiment.statistics:
            raise util.CytoflowViewError("Can't find Y statistic {} in experiment"
                                         .format(self.ystatistic))
        else:
            ystat = experiment.statistics[self.ystatistic]  
            
        if not xstat.index.equals(ystat.index):
            raise util.CytoflowViewError("X statistic and Y statistic must have "
                                         "the same indices: {}"
                                         .format(xstat.index.names))
             
        if self.x_error_statistic[0]:
            if self.x_error_statistic not in experiment.statistics:
                raise util.CytoflowViewError("X error statistic not in experiment")
            else:
                x_error_stat = experiment.statistics[self.x_error_statistic]
                
            if not x_error_stat.index.equals(xstat.index):
                raise util.CytoflowViewError("X error statistic doesn't have the "
                                             "same indices as the X statistic")
        else:
            x_error_stat = None

        if self.y_error_statistic[0]:
            if self.y_error_statistic not in experiment.statistics:
                raise util.CytoflowViewError("Y error statistic not in experiment")
            else:
                y_error_stat = experiment.statistics[self.y_error_statistic]
                
            if not y_error_stat.index.equals(ystat.index):
                raise util.CytoflowViewError("Y error statistic doesn't have the "
                                             "same indices as the Y statistic")
        else:
            y_error_stat = None
            
        col_wrap = kwargs.pop('col_wrap', None)
        
        if col_wrap and self.yfacet:
            raise util.CytoflowViewError("Can't set yfacet and col_wrap at the same time.") 
            
        data = pd.DataFrame(index = xstat.index)
            
        xname = util.random_string(6)
        data[xname] = xstat
        
        yname = util.random_string(6)
        data[yname] = ystat
                 
        if x_error_stat is not None:
            #x_error_data = x_error_stat.reset_index()
            x_error_name = util.random_string(6)
            data[x_error_name] = x_error_stat
            
        if y_error_stat is not None:
            y_error_name = util.random_string(6)
            data[y_error_name] = y_error_stat
            
        if y_error_stat is not None:
            y_error_data = y_error_stat.reset_index()
            y_error_name = util.random_string()
            data[y_error_name] = y_error_data[y_error_stat.name]
            
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
            
        if not self.variable in experiment.conditions:
            raise util.CytoflowViewError("Variable {} not in experiment"
                                         .format(self.variable))
            
        if not self.variable in data.index.names:
            raise util.CytoflowViewError("Variable {} not in statistic; must be one of {}"
                                         .format(self.variable, data.index.names))

        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {} not in the experiment"
                                         .format(self.xfacet))
        
        if self.xfacet and self.xfacet not in data.index.names:
            raise util.CytoflowViewError("X facet {} not in statistics; must be one of {}"
                                         .format(self.xfacet, data.index.names))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {} not in the experiment"
                                         .format(self.yfacet))
            
        if self.yfacet and self.yfacet not in data.index.names:
            raise util.CytoflowViewError("Y facet {} not in statistics; must be one of {}"
                                         .format(self.yfacet, data.index.names))
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise util.CytoflowViewError("Hue facet {} not in the experiment"
                                         .format(self.huefacet))        

        if self.huefacet and self.huefacet not in data.index.names:
            raise util.CytoflowViewError("Hue facet {} not in statistics; must be one of {}"
                                         .format(self.huefacet, data.index.names))
            
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
        
        # sort by the data in the x variable
        data = data.sort_values(by = [xname])
        
        # TODO - account for error bars
        
        xscale = util.scale_factory(self.xscale, experiment, statistic = self.xstatistic)
        yscale = util.scale_factory(self.yscale, experiment, statistic = self.ystatistic)
            
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (xscale.clip(data[xname].min() * 0.9),
                    xscale.clip(data[xname].max() * 1.1))
                      
        ylim = kwargs.pop("ylim", None)
        if ylim is None:
            ylim = (yscale.clip(data[yname].min() * 0.9),
                    yscale.clip(data[yname].max() * 1.1))
                      
        kwargs.setdefault('antialiased', True)
        
        cols = col_wrap if col_wrap else \
               len(data[self.xfacet].unique()) if self.xfacet else 1
               
        sharex = kwargs.pop('sharex', True)
        sharey = kwargs.pop('sharey', True)
               
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
                             sharex = sharex,
                             sharey = sharey,
                             xlim = xlim,
                             ylim = ylim)

        for ax in grid.axes.flatten():
            ax.set_xscale(self.xscale, **xscale.mpl_params)
            ax.set_yscale(self.yscale, **yscale.mpl_params)
        
        # plot the error bars first so the axis labels don't get overwritten
        if x_error_stat:
            grid.map(_x_error_bars, xname, yname, x_error_name)
            
        if y_error_stat:
            grid.map(_y_error_bars, xname, yname, y_error_name)

        grid.map(plt.plot, xname, yname, **kwargs)
        
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
            if util.is_numeric(experiment.data[self.huefacet]) and \
                len(grid.hue_names) > len(current_palette):
                
                plot_ax = plt.gca()
                cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
                                                                   n_colors = len(grid.hue_names)))
                cax, _ = mpl.colorbar.make_axes(plt.gca())
                norm = mpl.colors.Normalize(vmin = np.min(grid.hue_names), 
                                            vmax = np.max(grid.hue_names), 
                                            clip = False)
                mpl.colorbar.ColorbarBase(cax, 
                                          cmap = cmap, 
                                          norm = norm,
                                          label = self.huefacet)
                plt.sca(plot_ax)
            else:
                grid.add_legend(title = self.huefacet)
                
        plt.xlabel(self.xstatistic)
        plt.ylabel(self.ystatistic)
        
        if unused_names and plot_name:
            plt.title("{0} = {1}".format(unused_names, plot_name))


def _x_error_bars(x, y, xerr, ax = None, color = None, **kwargs):
    
    if isinstance(xerr.iloc[0], tuple):
        x_lo = [xe[0] for xe in xerr]
        x_hi = [xe[1] for xe in xerr]
    else:
        x_lo = [x.iloc[i] - xe for i, xe in xerr.reset_index(drop = True).iteritems()]
        x_hi = [x.iloc[i] + xe for i, xe in xerr.reset_index(drop = True).iteritems()]
        
    plt.hlines(y, x_lo, x_hi, color = color, **kwargs)
    
    
def _y_error_bars(x, y, yerr, ax = None, color = None, **kwargs):
    
    if isinstance(yerr.iloc[0], tuple):
        y_lo = [ye[0] for ye in yerr]
        y_hi = [ye[1] for ye in yerr]
    else:
        y_lo = [y.iloc[i] - ye for i, ye in yerr.reset_index(drop = True).iteritems()]
        y_hi = [y.iloc[i] + ye for i, ye in yerr.reset_index(drop = True).iteritems()]
        
    plt.vlines(x, y_lo, y_hi, color = color, **kwargs)
    
    
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