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
cytoflow.views.base_views
-------------------------
'''

from traits.api import HasStrictTraits, Str, Tuple, List, Dict, provides
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns
import pandas as pd

from warnings import warn

import cytoflow.utility as util
from .i_view import IView

class BaseView(HasStrictTraits):
    """
    The base class for facetted plotting.
    
    Attributes
    ----------
    xfacet, yfacet : String
        Set to one of the :attr:`~.Experiment.conditions` in the :class:`.Experiment`, and
        a new row or column of subplots will be added for every unique value
        of that condition.
        
    huefacet : String
        Set to one of the :attr:`~.Experiment.conditions` in the in the :class:`.Experiment`,
        and a new color will be added to the plot for every unique value of 
        that condition.
        
    huescale : {'linear', 'log', 'logicle'}
        How should the color scale for :attr:`huefacet` be scaled?
    """
    
    xfacet = Str
    yfacet = Str
    huefacet = Str
    huescale = util.ScaleEnum
    
    def plot(self, experiment, data, **kwargs):
        """
        Base function for facetted plotting
        
        Parameters
        ----------
        experiment: Experiment
            The :class:`.Experiment` to plot using this view.
            
        legend : bool
            Plot a legend for the color or hue facet?  Defaults to `True`.
            
        sharex, sharey : bool
            If there are multiple subplots, should they share axes?  Defaults
            to `True`.
            
        xlim, ylim : (float, float)
            Set the min and max limits of the plots' x and y axes.

        col_wrap : int
            If `xfacet` is set and `yfacet` is not set, you can "wrap" the
            subplots around so that they form a multi-row grid by setting
            `col_wrap` to the number of columns you want. 

        Other Parameters
        ----------------
        cmap : matplotlib colormap
            If plotting a huefacet with many values, use this color map instead
            of the default.
            
        norm : matplotlib.colors.Normalize
            If plotting a huefacet with many values, use this object for color
            scale normalization.
        """

        col_wrap = kwargs.pop('col_wrap', None)
        
        if col_wrap and self.yfacet:
            raise util.CytoflowViewError('yfacet',
                                         "Can't set yfacet and col_wrap at the same time.")
        
        if col_wrap and not self.xfacet:
            raise util.CytoflowViewError('xfacet',
                                         "Must set xfacet to use col_wrap.")
        
        sharex = kwargs.pop("sharex", True)
        sharey = kwargs.pop("sharey", True)

        xscale = kwargs.pop("xscale", None)
        yscale = kwargs.pop("yscale", None)
        
        xlim = kwargs.pop("xlim", None)
        ylim = kwargs.pop("ylim", None)
        
        legend = kwargs.pop('legend', True)
        
        cols = col_wrap if col_wrap else \
               len(data[self.xfacet].unique()) if self.xfacet else 1
            
        g = sns.FacetGrid(data, 
                          size = 6 / cols,
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
        
        plot_ret = self._grid_plot(experiment = experiment,
                                   grid = g, 
                                   xlim = xlim,
                                   ylim = ylim,
                                   xscale = xscale,
                                   yscale = yscale,
                                   **kwargs)
        
        kwargs.update(plot_ret)
        
        xscale = kwargs.pop("xscale", xscale)
        yscale = kwargs.pop("yscale", yscale)
        
        for ax in g.axes.flatten():
            if xscale:
                ax.set_xscale(xscale.name, **xscale.mpl_params) 
            if yscale:
                ax.set_yscale(yscale.name, **yscale.mpl_params)

        # if we are sharing x axes, make sure the x scale is the same for each
        if sharex:
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
        
        # if we are sharing y axes, make sure the y scale is the same for each
        if sharey:
            fig = plt.gcf()
            fig_y_max = float("-inf")
            
            for ax in fig.get_axes():
                _, ax_y_max = ax.get_ylim()
                if ax_y_max > fig_y_max:
                    fig_y_max = ax_y_max
                    
            for ax in fig.get_axes():
                ax.set_ylim(None, fig_y_max)
            
        # if we have a hue facet and a lot of hues, make a color bar instead
        # of a super-long legend.

        cmap = kwargs.pop('cmap', None)
        norm = kwargs.pop('norm', None)
        
        if legend:
            if cmap and norm:
                plot_ax = plt.gca()
                cax, _ = mpl.colorbar.make_axes(plt.gcf().get_axes())
                mpl.colorbar.ColorbarBase(cax, cmap, norm)
                plt.sca(plot_ax)
            elif self.huefacet:
        
                current_palette = mpl.rcParams['axes.color_cycle']
            
                if util.is_numeric(data[self.huefacet]) and \
                   len(g.hue_names) > len(current_palette):
    
                    cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
                                                                       n_colors = len(g.hue_names)))                
                    hue_scale = util.scale_factory(self.huescale, 
                                                   experiment,
                                                   data = data[self.huefacet].values)
                    
                    plot_ax = plt.gca()
    
                    cax, _ = mpl.colorbar.make_axes(plt.gcf().get_axes())
    
                    mpl.colorbar.ColorbarBase(cax, 
                                              cmap = cmap, 
                                              norm = hue_scale.norm(), 
                                              label = self.huefacet)
                    plt.sca(plot_ax)
                else:
                    g.add_legend(title = self.huefacet)
                    ax = g.axes.flat[0]
                    legend = ax.legend_
                    for lh in legend.legendHandles:
                        lh.set_alpha(0.5)
                    
                    
    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):
        raise NotImplementedError("You must override _grid_plot in a derived class")
        
class BaseDataView(BaseView):
    """
    The base class for data views (as opposed to statistics views).
    """

    subset = Str
    
    def plot(self, experiment, **kwargs):
        """
        Plot some data from an experiment.  This function takes care of
        checking for facet name validity and subsetting, then passes the
        underlying dataframe to `BaseView.plot`

        """

        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError('xfacet',
                                         "X facet {0} not in the experiment"
                                         .format(self.xfacet))
         
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError('yfacet',
                                         "Y facet {0} not in the experiment"
                                         .format(self.yfacet))
         
        if self.huefacet and self.huefacet not in experiment.conditions:
            raise util.CytoflowViewError('huefacet',
                                         "Hue facet {0} not in the experiment"
                                         .format(self.huefacet))
             
        facets = [x for x in [self.xfacet, self.yfacet, self.huefacet] if x]
         
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError(None,
                                         "Can't reuse facets")
         
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except util.CytoflowError as e:
                raise util.CytoflowViewError('subset', str(e)) from e
            except Exception as e:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(self.subset)) from e
                 
            if len(experiment) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no events"
                                             .format(self.subset))
                 
        super().plot(experiment, experiment.data, **kwargs)
        

class Base1DView(BaseDataView):
    """
    A data view that plots data from a single channel.
    
    Attributes
    ----------
    channel : Str
        The channel to view
        
    scale : {'linear', 'log', 'logicle'}
        The scale applied to the data before plotting it.
    """
    
    channel = Str
    scale = util.ScaleEnum
    
    def plot(self, experiment, **kwargs):
        """
        Parameters
        ----------
        min_quantile : float (>0.0 and <1.0, default = 0.001)
            Clip data that is less than this quantile.
            
        max_quantile : float (>0.0 and <1.0, default = 1.00)
            Clip data that is greater than this quantile.
            
        xlim : (float, float)
            Set the range of the plot's x axis.
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
        
        if not self.channel:
            raise util.CytoflowViewError('channel',
                                         "Must specify a channel")
        
        if self.channel not in experiment.data:
            raise util.CytoflowViewError('channel',
                                         "Channel {0} not in the experiment"
                                         .format(self.channel))
        
        # get the scale
        scale = kwargs.pop('scale', None)
        if scale is None:
            scale = util.scale_factory(self.scale, experiment, channel = self.channel)
        
        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 1.0) 
        
        if min_quantile < 0.0 or min_quantile > 1:
            raise util.CytoflowViewError('min_quantile',
                                         "min_quantile must be between 0 and 1")

        if max_quantile < 0.0 or max_quantile > 1:
            raise util.CytoflowViewError('max_quantile',
                                         "max_quantile must be between 0 and 1")     
        
        if min_quantile >= max_quantile:
            raise util.CytoflowViewError('min_quantile',
                                         "min_quantile must be less than max_quantile")   
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (experiment[self.channel].quantile(min_quantile),
                    experiment[self.channel].quantile(max_quantile))
            
        xlim = [scale.clip(x) for x in xlim]
        
        super().plot(experiment, xlim = xlim, xscale = scale, **kwargs)
    

class Base2DView(BaseDataView):
    """
    A data view that plots data from two channels.
    
    Attributes
    ----------
    xchannel, ychannel : Str
        The channels to view
        
    xscale, yscale : {'linear', 'log', 'logicle'} (default = 'linear')
        The scales applied to the data before plotting it.
    """
    
    xchannel = Str
    xscale = util.ScaleEnum
    ychannel = Str
    yscale = util.ScaleEnum

    def plot(self, experiment, **kwargs):
        """
        Parameters
        ----------
        min_quantile : float (>0.0 and <1.0, default = 0.001)
            Clip data that is less than this quantile.
            
        max_quantile : float (>0.0 and <1.0, default = 1.00)
            Clip data that is greater than this quantile.
            
        xlim, ylim : (float, float)
            Set the range of the plot's axis.
        """

        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")

        if not self.xchannel:
            raise util.CytoflowViewError('xchannel',
                                         "Must specify an xchannel")
        
        if self.xchannel not in experiment.data:
            raise util.CytoflowViewError('xchannel',
                                         "Channel {} not in the experiment"
                                    .format(self.xchannel))

        if not self.ychannel:
            raise util.CytoflowViewError('ychannel',
                                         "Must specify a ychannel")
        
        if self.ychannel not in experiment.data:
            raise util.CytoflowViewError('ychannel',
                                         "Channel {} not in the experiment"
                                    .format(self.ychannel))
        
        # get the scale
        xscale = kwargs.pop('xscale', None)
        if xscale is None:
            xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)

        yscale = kwargs.pop('yscale', None)
        if yscale is None:
            yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
        
        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 1.0) 
        
        if min_quantile < 0.0 or min_quantile > 1:
            raise util.CytoflowViewError('min_quantile',
                                         "min_quantile must be between 0 and 1")

        if max_quantile < 0.0 or max_quantile > 1:
            raise util.CytoflowViewError('max_quantile',
                                         "max_quantile must be between 0 and 1")     
        
        if min_quantile >= max_quantile:
            raise util.CytoflowViewError('min_quantile',
                                         "min_quantile must be less than max_quantile")   
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (experiment[self.xchannel].quantile(min_quantile),
                    experiment[self.xchannel].quantile(max_quantile))
            
        xlim = [xscale.clip(x) for x in xlim]

        ylim = kwargs.pop("ylim", None)
        if ylim is None:
            ylim = (experiment[self.ychannel].quantile(min_quantile),
                    experiment[self.ychannel].quantile(max_quantile))
            
        ylim = [yscale.clip(y) for y in ylim]
        
        super().plot(experiment, 
                     xlim = xlim,
                     xscale = xscale, 
                     ylim = ylim,
                     yscale = yscale, 
                     **kwargs)        

class BaseNDView(BaseDataView):
    """
    A data view that plots data from one or more channels.
    
    Attributes
    ----------
    channels : List(Str)
        The channels to view

    scale : Dict(Str : {"linear", "logicle", "log"})
        Re-scale the data in the specified channels before plotting.  If a 
        channel isn't specified, assume that the scale is linear.
    """
    
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)

    def plot(self, experiment, **kwargs):
        """
        Parameters
        ----------
        min_quantile : float (>0.0 and <1.0, default = 0.001)
            Clip data that is less than this quantile.
            
        max_quantile : float (>0.0 and <1.0, default = 1.00)
            Clip data that is greater than this quantile.
            
        lim : Dict(Str : (float, float))
            Set the range of each channel's axis.  If unspecified, assume
            that the limits are the minimum and maximum of the clipped data
        """

        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")

        if len(self.channels) == 0:
            raise util.CytoflowOpError('channels',
                                       "Must set at least one channel")

        for c in self.channels:
            if c not in experiment.data:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not found in the experiment"
                                      .format(c))
                
        for c in self.scale:
            if c not in self.channels:
                raise util.CytoflowOpError('scale',
                                           "Scale set for channel {0}, but it isn't "
                                           "in 'channels'"
                                           .format(c))
       
        
        # get the scale
        scale = {}
        for c in self.channels:
            if c in self.scale:
                scale[c] = util.scale_factory(self.scale[c], experiment, channel = c)
            else:
                scale[c] = util.scale_factory(util.get_default_scale(), experiment, channel = c)
        
        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 1.0) 
        
        if min_quantile < 0.0 or min_quantile > 1:
            raise util.CytoflowViewError('min_quantile',
                                         "min_quantile must be between 0 and 1")

        if max_quantile < 0.0 or max_quantile > 1:
            raise util.CytoflowViewError('max_quantile',
                                         "max_quantile must be between 0 and 1")     
        
        if min_quantile >= max_quantile:
            raise util.CytoflowViewError('min_quantile',
                                         "min_quantile must be less than max_quantile")   
            
        lim = kwargs.pop("lim", {})
        
        for c in self.channels:
            if c not in lim:
                lim[c] = (experiment[c].quantile(min_quantile),
                          experiment[c].quantile(max_quantile))
                
            lim[c] = [scale[c].clip(x) for x in lim[c]]
    
        
        super().plot(experiment, 
                     lim = lim,
                     scale = scale,
                     **kwargs)        

    

@provides(IView)
class BaseStatisticsView(BaseView):
    """
    The base class for statisticxs views (as opposed to data views).
    
    Attributes
    ----------
    variable : str
        The condition that varies when plotting this statistic: used for the
        x axis of line plots, the bar groups in bar plots, etc.
        
    subset : str
        An expression that specifies the subset of the statistic to plot.
        
    xscale, yscale : {'linear', 'log', 'logicle'}
        The scales applied to the data before plotting it.
    """
    
    # deprecated or removed attributes give warnings & errors, respectively
    by = util.Deprecated(new = 'variable', err_string = "'by' is deprecated, please use 'variable'")
    
    variable = Str
    subset = Str

    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    
    def enum_plots(self, experiment, data):
        """
        Enumerate the named plots we can make from this set of statistics.
        """
        
        if not self.variable:
            raise util.CytoflowViewError('variable',
                                         "variable not set")
            
        if self.variable not in experiment.conditions:
            raise util.CytoflowViewError('variable',
                                         "variable {0} not in the experiment"
                                    .format(self.variable))
            
        data, facets, names = self._subset_data(data)

        by = list(set(names) - set(facets))
        
        class plot_enum(object):
            
            def __init__(self, data, by):
                self.by = by
                self._iter = None
                self._returned = False
                
                if by:
                    self._iter = data.groupby(by).__iter__()
                
            def __iter__(self):
                return self
            
            def __next__(self):
                if self._iter:
                    return next(self._iter)[0]
                else:
                    if self._returned:
                        raise StopIteration
                    else:
                        self._returned = True
                        return None
            
        return plot_enum(data.reset_index(), by)
    
    def plot(self, experiment, data, plot_name = None, **kwargs):
        """
        Plot some data from a statistic.
        
        This function takes care of checking for facet name validity and 
        subsetting, then passes the dataframe to `BaseView.plot`
        """
        
        if not self.variable:
            raise util.CytoflowViewError('variable',
                                         "variable not set")
            
        if self.variable not in experiment.conditions:
            raise util.CytoflowViewError('variable',
                                         "variable {0} not in the experiment"
                                    .format(self.variable))
            
        data, facets, names = self._subset_data(data)

        unused_names = list(set(names) - set(facets))

        if plot_name is not None and not unused_names:
            raise util.CytoflowViewError('plot_name',
                                         "You specified a plot name, but all "
                                         "the facets are already used")
        
        if unused_names:
            groupby = data.groupby(unused_names)

            if plot_name is None:
                raise util.CytoflowViewError('plot_name',
                                             "You must use facets {} in either the "
                                             "plot variables or the plot name. "
                                             "Possible plot names: {}"
                                             .format(unused_names, list(groupby.groups.keys())))

            if plot_name not in set(groupby.groups.keys()):
                raise util.CytoflowViewError('plot_name',
                                             "Plot {} not from plot_enum; must "
                                             "be one of {}"
                                             .format(plot_name, list(groupby.groups.keys())))
                
            data = groupby.get_group(plot_name)
        
        # FacetGrid needs a "long" data set
        data.reset_index(inplace = True)
        super().plot(experiment, data, **kwargs)
        
    def _subset_data(self, data):
        
        if self.subset:
            try:
                # TODO - either sanitize column names, or check to see that
                # all conditions are valid Python variables
                data = data.query(self.subset)
            except Exception as e:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(self.subset)) from e
                
            if len(data) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no values"
                                             .format(self.subset))
                
        names = list(data.index.names)
        
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                warn("Only one value for level {}; dropping it.".format(name),
                     util.CytoflowViewWarning)
                try:
                    data.index = data.index.droplevel(name)
                except AttributeError as e:
                    raise util.CytoflowViewError(None,
                                                 "Must have more than one "
                                                 "value to plot.") from e
                
        names = list(data.index.names)

        if self.xfacet and self.xfacet not in data.index.names:
            raise util.CytoflowViewError('xfacet',
                                         "X facet {} not in statistics; must be one of {}"
                                         .format(self.xfacet, data.index.names))

        
        if self.yfacet and self.yfacet not in data.index.names:
            raise util.CytoflowViewError('yfacet',
                                         "Y facet {} not in statistics; must be one of {}"
                                         .format(self.yfacet, data.index.names))
            
        if self.huefacet and self.huefacet not in data.index.names:
            raise util.CytoflowViewError('huefacet',
                                         "Hue facet {} not in statistics; must be one of {}"
                                         .format(self.huefacet, data.index.names))
            
            
        facets = [x for x in [self.variable, self.xfacet, self.yfacet, self.huefacet] if x]
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError(None, "Can't reuse facets")
        
        return data, facets, names

class Base1DStatisticsView(BaseStatisticsView):
    """
    The base class for 1-dimensional statistic views -- ie, the :attr:`variable`
    attribute is on the x axis, and the statistic value is on the y axis.
    
    Attributes
    ----------
    statistic : (str, str)
        The name of the statistic to plot.  Must be a key in the  
        :attr:`~Experiment.statistics` attribute of the :class:`~.Experiment`
        being plotted.
        
    error_statistic : (str, str)
        The name of the statistic used to plot error bars.  Must be a key in the
        :attr:`~Experiment.statistics` attribute of the :class:`~.Experiment`
        being plotted.
    """
    
    REMOVED_ERROR = "Statistics changed dramatically in 0.5; please see the documentation"
    by = util.Removed(err_string = REMOVED_ERROR)
    yfunction = util.Removed(err_string = REMOVED_ERROR)
    ychannel = util.Removed(err_string = REMOVED_ERROR)
    channel = util.Removed(err_string = REMOVED_ERROR)
    function = util.Removed(err_string = REMOVED_ERROR)
    error_bars = util.Removed(err_string = REMOVED_ERROR)
    
    xvariable = util.Deprecated(new = "variable")
    
    statistic = Tuple(Str, Str)
    error_statistic = Tuple(Str, Str)
    
    def enum_plots(self, experiment):
        data = self._make_data(experiment)
        return super().enum_plots(experiment, data)
    
    def plot(self, experiment, plot_name = None, **kwargs):       
        data = self._make_data(experiment)
        
        if not self.variable:
            raise util.CytoflowViewError('variable',
                                         "variable not set")
            
        if self.variable not in experiment.conditions:
            raise util.CytoflowViewError('variable',
                                         "variable {0} not in the experiment"
                                    .format(self.variable))
            
        if util.is_numeric(experiment[self.variable]):
            xscale = util.scale_factory(self.xscale, experiment, condition = self.variable)
        else:
            xscale = None 
        
        yscale = util.scale_factory(self.yscale, 
                                    experiment, 
                                    statistic = self.statistic, 
                                    error_statistic = self.error_statistic)
            
        super().plot(experiment, 
                     data, 
                     plot_name, 
                     xscale = xscale, 
                     yscale = yscale, 
                     **kwargs)
        
    def _make_data(self, experiment):
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.statistic:
            raise util.CytoflowViewError('statistic', "Statistic not set")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic',
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
        else:
            stat = experiment.statistics[self.statistic]
            
        if not util.is_numeric(stat):
            raise util.CytoflowViewError('statistic',
                                         "Statistic must be numeric")
            
        if self.error_statistic[0]:
            if self.error_statistic not in experiment.statistics:
                raise util.CytoflowViewError('error_statistic',
                                             "Can't find the error statistic in the experiment")
            else:
                error_stat = experiment.statistics[self.error_statistic]
        else:
            error_stat = None
         
        if error_stat is not None:

            try:
                error_stat.index = error_stat.index.reorder_levels(stat.index.names)
                error_stat.sort_index(inplace = True)
            except AttributeError:
                pass
            
            if not stat.index.equals(error_stat.index):
                raise util.CytoflowViewError('error_statistic',
                                             "Data statistic and error statistic "
                                             " don't have the same index.")
               
            if stat.name == error_stat.name:
                raise util.CytoflowViewError('error_statistic',
                                             "Data statistic and error statistic can "
                                             "not have the same name.")
               
        data = pd.DataFrame(index = stat.index)
        data[stat.name] = stat
        
        if error_stat is not None:
            data[error_stat.name] = error_stat
            
        return data

class Base2DStatisticsView(BaseStatisticsView):
    """
    The base class for 2-dimensional statistic views -- ie, the :attr:`variable`
    attribute varies independently, and the corresponding values from the x and
    y statistics are plotted on the x and y axes.
    
    Attributes
    ----------
    xstatistic, ystatistic : (str, str)
        The name of the statistics to plot.  Must be a keys in the  
        :attr:`~Experiment.statistics` attribute of the :class:`~.Experiment`
        being plotted.
        
    x_error_statistic, y_error_statistic : (str, str)
        The name of the statistics used to plot error bars.  Must be keys in the
        :attr:`~Experiment.statistics` attribute of the :class:`~.Experiment`
        being plotted.
    """

    STATS_REMOVED = "{} has been removed. Statistics changed dramatically in 0.5; please see the documentation."
    
    xchannel = util.Removed(err_string = STATS_REMOVED)
    xfunction = util.Removed(err_string = STATS_REMOVED)
    ychannel = util.Removed(err_string = STATS_REMOVED)
    yfunction = util.Removed(err_string = STATS_REMOVED)
    
    xstatistic = Tuple(Str, Str)
    ystatistic = Tuple(Str, Str)
    x_error_statistic = Tuple(Str, Str)
    y_error_statistic = Tuple(Str, Str)
    
    def enum_plots(self, experiment):
        data = self._make_data(experiment)
        return super().enum_plots(experiment, data)
    
    def plot(self, experiment, plot_name = None, **kwargs):
        data = self._make_data(experiment)

        xscale = util.scale_factory(self.xscale, 
                                    experiment, 
                                    statistic = self.xstatistic, 
                                    error_statistic = self.x_error_statistic)
        
        yscale = util.scale_factory(self.yscale, 
                                    experiment, 
                                    statistic = self.ystatistic, 
                                    error_statistic = self.y_error_statistic)
            
        super().plot(experiment, 
                     data, 
                     plot_name, 
                     xscale = xscale, 
                     yscale = yscale, 
                     **kwargs)
        
    def _make_data(self, experiment):
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
        
        if not self.xstatistic:
            raise util.CytoflowViewError('xstatistic',
                                         "X Statistic not set")
        
        if self.xstatistic not in experiment.statistics:
            raise util.CytoflowViewError('xstatistic',
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.xstatistic))
        else:
            xstat = experiment.statistics[self.xstatistic]
            
        if not util.is_numeric(xstat):
            raise util.CytoflowViewError('xstatistic',
                                         "X statistic must be numeric")
            
        if self.x_error_statistic[0]:
            if self.x_error_statistic not in experiment.statistics:
                raise util.CytoflowViewError('x_error_statistic',
                                             "Can't find the X error statistic in the experiment")
            else:
                x_error_stat = experiment.statistics[self.x_error_statistic]
        else:
            x_error_stat = None
            
        if x_error_stat is not None:
               
            try:
                x_error_stat.index = x_error_stat.index.reorder_levels(xstat.index.names)
                x_error_stat.sort_index(inplace = True)
            except AttributeError:
                pass
            
            if not xstat.index.equals(x_error_stat.index):
                raise util.CytoflowViewError('x_error_statistic',
                                             "Data statistic and error statistic "
                                             " don't have the same index.")
               
            if xstat.name == x_error_stat.name:
                raise util.CytoflowViewError('x_error_statistic',
                                             "Data statistic and error statistic can "
                                             "not have the same name.")
            
        if not self.ystatistic:
            raise util.CytoflowViewError('ystatistic',
                                         "Y statistic not set")
        
        if self.ystatistic not in experiment.statistics:
            raise util.CytoflowViewError('ystatistic',
                                         "Can't find the Y statistic {} in the experiment"
                                         .format(self.ystatistic))
        else:
            ystat = experiment.statistics[self.ystatistic]
            
        if not util.is_numeric(ystat):
            raise util.CytoflowViewError('ystatistic',
                                         "Y statistic must be numeric")
        
        if self.y_error_statistic[0]:
            if self.y_error_statistic not in experiment.statistics:
                raise util.CytoflowViewError('y_error_statistic',
                                             "Can't find the Y error statistic in the experiment")
            else:
                y_error_stat = experiment.statistics[self.y_error_statistic]
        else:
            y_error_stat = None
         
        if y_error_stat is not None:
            
            try:
                y_error_stat.index = y_error_stat.index.reorder_levels(ystat.index.names)
                y_error_stat.sort_index(inplace = True)
            except AttributeError:
                pass
            
            if not ystat.index.equals(y_error_stat.index):
                raise util.CytoflowViewError('y_error_statistic',
                                             "Data statistic and error statistic "
                                             " don't have the same index.")
               
            if ystat.name == y_error_stat.name:
                raise util.CytoflowViewError('y_error_statistic',
                                             "Data statistic and error statistic can "
                                             "not have the same name.")

        if xstat.name == ystat.name:
            raise util.CytoflowViewError('ystatistic',
                                         "X and Y statistics can "
                                         "not have the same name.")
               
        try:
            ystat.index = ystat.index.reorder_levels(xstat.index.names)
            ystat.sort_index(inplace = True)
        except AttributeError:
            pass
        
        intersect_idx = xstat.index.intersection(ystat.index)
        xstat = xstat.reindex(intersect_idx)
        xstat.sort_index(inplace = True)
        ystat = ystat.reindex(intersect_idx)
        ystat.sort_index(inplace = True)
             
        if self.x_error_statistic[0]:
            if self.x_error_statistic not in experiment.statistics:
                raise util.CytoflowViewError('x_error_statistic',
                                             "X error statistic not in experiment")
            else:
                x_error_stat = experiment.statistics[self.x_error_statistic]
                
            if set(x_error_stat.index.names) != set(xstat.index.names):
                raise util.CytoflowViewError('x_error_statistic',
                                             "X error statistic doesn't have the "
                                             "same indices as the X statistic")
            
            try:
                x_error_stat.index = x_error_stat.index.reorder_levels(xstat.index.names)
                x_error_stat.sort_index(inplace = True)
            except AttributeError:
                pass
            
            x_error_stat = x_error_stat.reindex(intersect_idx)
            x_error_stat.sort_index(inplace = True)
            
            if not x_error_stat.index.equals(xstat.index):
                raise util.CytoflowViewError('x_error_statistic',
                                             "X error statistic doesn't have the "
                                             "same indices as the X statistic")                
        else:
            x_error_stat = None
            
        if self.y_error_statistic[0]:
            if self.y_error_statistic not in experiment.statistics:
                raise util.CytoflowViewError('y_error_statistic',
                                             "Y error statistic not in experiment")
            else:
                y_error_stat = experiment.statistics[self.y_error_statistic]
                
            if set(y_error_stat.index.names) != set(ystat.index.names):
                raise util.CytoflowViewError('y_error_statistic',
                                             "Y error statistic doesn't have the "
                                             "same indices as the Y statistic")
                
            try:
                y_error_stat.index = y_error_stat.index.reorder_levels(ystat.index.names)
                y_error_stat.sort_index(inplace = True)
            except AttributeError:
                pass
            
            y_error_stat = y_error_stat.reindex(intersect_idx)
            y_error_stat.sort_index(inplace = True)
            
            if not y_error_stat.index.equals(ystat.index):
                raise util.CytoflowViewError('y_error_statistic',
                                             "Y error statistic doesn't have the "
                                             "same values as the Y statistic")   
        else:
            y_error_stat = None
            
        data = pd.DataFrame(index = xstat.index)
        data[xstat.name] = xstat
        data[ystat.name] = ystat
        
        if x_error_stat is not None:
            data[x_error_stat.name] = x_error_stat
            
        if y_error_stat is not None:
            data[y_error_stat.name] = y_error_stat
            
        return data



