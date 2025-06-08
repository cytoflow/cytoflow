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
cytoflow.views.base_views
-------------------------

Base classes for views.

I found, as I wrote a bunch of views, that I was also writing a bunch of shared
boiler-plate code.  This led to more bugs and a harder-to-maintain codebase.
So, I extracted the copied code in a short hierarchy of reusable base classes:

`BaseView` -- implements a view with row, column and hue facets.
After setting up the facet grid, it calls the derived class's 
``_grid_plot`` to actually do the plotting.  `BaseView.plot` also
has parameters to set the plot style, legend, axis labels, etc.
  
`BaseDataView` -- implements a view that plots an `Experiment`'s
data (as opposed to a statistic.)  Includes functionality for subsetting
the data before plotting, and determining axis limits and scales.
  
`Base1DView` -- implements a 1-dimensional data view.  See 
`HistogramView` for an example.
  
`Base2DView` -- implements a 2-dimensional data view.  See
`ScatterplotView` for an example.
  
`BaseNDView` -- implements an N-dimensional data view.  See
`RadvizView` for an example.
  
`BaseStatisticsView` -- implements a view that plots a statistic from
an `Experiment` (as opposed to the underlying data.)  These views
have a "primary" `BaseStatisticsView.variable`, and can be subset
as well.
  
`Base1DStatisticsView` -- implements a view that plots one dimension
of a statistic.  See `BarChartView` for an example.
  
`Base2DStatisticsView` -- implements a view that plots two dimensions
of a statistic.  See `Stats2DView` for an example.
"""

from traits.api import HasStrictTraits, Str, List, Dict, provides
import matplotlib as mpl
import matplotlib.pyplot as plt

import seaborn as sns
from natsort import natsorted

from warnings import warn

import cytoflow
import cytoflow.utility as util
from .i_view import IView

class BaseView(HasStrictTraits):
    """
    The base class for facetted plotting.
    
    Attributes
    ----------
    xfacet : String
        Set to one of the `Experiment.conditions` in the `Experiment`, and
        a new column of subplots will be added for every unique value
        of that condition.
        
    yfacet : String
        Set to one of the `Experiment.conditions` in the `Experiment`, and
        a new row of subplots will be added for every unique value
        of that condition.
        
    huefacet : String
        Set to one of the `Experiment.conditions` in the in the `Experiment`,
        and a new color will be added to the plot for every unique value of 
        that condition.
        
    huescale : {'linear', 'log', 'logicle'}
        How should the color scale for `huefacet` be scaled?
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
            The `Experiment` to plot using this view.
            
        title : str
            Set the plot title
            
        xlabel : str
            Set the X axis label
        
        ylabel : str
            Set the Y axis label
            
        huelabel : str
            Set the label for the hue facet (in the legend)
            
        legend : bool
            Plot a legend for the color or hue facet?  Defaults to `True`.
            
        sharex : bool
            If there are multiple subplots, should they share X axes?  Defaults
            to `True`.
            
        sharey : bool
            If there are multiple subplots, should they share Y axes?  Defaults
            to `True`.

        row_order : list
            Override the row facet value order with the given list.
            If a value is not given in the ordering, it is not plotted.
            Defaults to a "natural ordering" of all the values.

        col_order : list
            Override the column facet value order with the given list.
            If a value is not given in the ordering, it is not plotted.
            Defaults to a "natural ordering" of all the values.
            
        hue_order : list
            Override the hue facet value order with the given list.
            If a value is not given in the ordering, it is not plotted.
            Defaults to a "natural ordering" of all the values.
            
        height : float
            The height of *each row* in inches.  Default = 3.0
            
        aspect : float
            The aspect ratio *of each subplot*.  Default = 1.5

        col_wrap : int
            If `xfacet` is set and `yfacet` is not set, you can "wrap" the
            subplots around so that they form a multi-row grid by setting
            this to the number of columns you want. 
            
        sns_style : {"darkgrid", "whitegrid", "dark", "white", "ticks"}
            Which ``seaborn`` style to apply to the plot?  Default is ``whitegrid``.
            
        sns_context : {"notebook", "paper", "talk", "poster"}
            Which ``seaborn`` context to use?  Controls the scaling of plot 
            elements such as tick labels and the legend.  Default is ``notebook``.
            
        palette : palette name, list, or dict
            Colors to use for the different levels of the hue variable. 
            Should be something that can be interpreted by
            `seaborn.color_palette`, or a dictionary mapping hue levels to 
            matplotlib colors.
            
        despine : Bool
            Remove the top and right axes from the plot?  Default is ``True``.

        Other Parameters
        ----------------
        cmap : matplotlib colormap
            If plotting a huefacet with many values, use this color map instead
            of the default.
            
        norm : matplotlib.colors.Normalize
            If plotting a huefacet with many values, use this object for color
            scale normalization.

        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")

        col_wrap = kwargs.pop('col_wrap', None)
        
        if col_wrap is not None and self.yfacet:
            raise util.CytoflowViewError('yfacet',
                                         "Can't set yfacet and col_wrap at the same time.")
        
        if col_wrap is not None and not self.xfacet:
            raise util.CytoflowViewError('xfacet',
                                         "Must set xfacet to use col_wrap.")
            
        if col_wrap is not None and col_wrap < 2:
            raise util.CytoflowViewError(None,
                                         "col_wrap must be None or > 1")
        
        title = kwargs.pop("title", None)
        xlabel = kwargs.pop("xlabel", None)       
        ylabel = kwargs.pop("ylabel", None)
        huelabel = kwargs.pop("huelabel", self.huefacet)
        if huelabel == "": huelabel = self.huefacet
        
        sharex = kwargs.pop("sharex", True)
        sharey = kwargs.pop("sharey", True)
        
        height = kwargs.pop("height", 3)
        aspect = kwargs.pop("aspect", 1.5)
        
        legend = kwargs.pop('legend', True)
        legend_out = kwargs.pop('legend_out', False)

        despine = kwargs.pop('despine', False)
        palette = kwargs.pop('palette', None)
        margin_titles = kwargs.pop('margin_titles', False)
               
        if cytoflow.RUNNING_IN_GUI:
            sns_style = kwargs.pop('sns_style', 'whitegrid')
            sns_context = kwargs.pop('sns_context', 'notebook')
            sns.set_style(sns_style, rc = {"xtick.bottom": True, "ytick.left": True})
            sns.set_context(sns_context)
        else:
            if 'sns_style' in kwargs:
                kwargs.pop('sns_style')
                warn("'sns_style' is ignored when not running in the GUI. Feel free to change the seaborn global settings.",
                     util.CytoflowViewWarning)
                
            if 'sns_context' in kwargs:
                kwargs.pop('sns_context')
                warn("'sns_context' is ignored when not running in the GUI. Feel free to change the seaborn global settings.",
                     util.CytoflowViewWarning)
                
            
        col_order = kwargs.pop("col_order", (natsorted(data[self.xfacet].unique()) if self.xfacet else None))
        row_order = kwargs.pop("row_order", (natsorted(data[self.yfacet].unique()) if self.yfacet else None))
        hue_order = kwargs.pop("hue_order", (natsorted(data[self.huefacet].unique()) if self.huefacet else None))
        g = sns.FacetGrid(data, 
                          height = height,
                          aspect = aspect,
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          col_order = col_order,
                          row_order = row_order,
                          hue_order = hue_order,
                          col_wrap = col_wrap,
                          legend_out = legend_out,
                          sharex = sharex,
                          sharey = sharey,
                          despine = despine,
                          palette = palette, 
                          margin_titles = margin_titles)
        
        plot_ret = self._grid_plot(experiment = experiment, grid = g, **kwargs)
        
        kwargs.update(plot_ret)
        
        xscale = kwargs.pop("xscale", None)
        yscale = kwargs.pop("yscale", None)
        xlim = kwargs.pop("xlim", None)
        ylim = kwargs.pop("ylim", None)
        
        for ax in g.axes.flatten():
            if xscale:
                ax.set_xscale(xscale.name, **xscale.get_mpl_params(ax.get_xaxis())) 
            if yscale:
                ax.set_yscale(yscale.name, **yscale.get_mpl_params(ax.get_yaxis()))
            if xlim != None and xlim != (None, None):
                ax.set_xlim(xlim)
            if ylim != None and ylim != (None, None):
                ax.set_ylim(ylim)

        # if we are sharing x axes, make sure the x limits are the same for each
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
        
        # if we are sharing y axes, make sure the y limits are the same for each
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
        legend_data = kwargs.pop('legend_data', None)
        
        if legend:
            if cmap and norm:
                plot_ax = plt.gca()
                cax, _ = mpl.colorbar.make_axes(plt.gcf().get_axes())
                mpl.colorbar.ColorbarBase(cax, 
                                          cmap = cmap, 
                                          norm = norm)
                plt.sca(plot_ax)
            elif self.huefacet:
        
                current_palette = mpl.rcParams['axes.prop_cycle']
            
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
                                              label = huelabel)
                    plt.sca(plot_ax)
                else:
                    g.add_legend(title = huelabel, legend_data = legend_data)
                    ax = g.axes.flat[0]
                    legend = ax.legend_
                    self._update_legend(legend)
                        
        if title:
            plt.suptitle(title, y = 1.02)
            
        if xlabel == "":
            xlabel = None
            
        if ylabel == "":
            ylabel = None
            
        g.set_axis_labels(xlabel, ylabel)
      
    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):
        raise NotImplementedError("You must override _grid_plot in a derived class")
    
    def _update_legend(self, legend):
        pass  # no-op
        
class BaseDataView(BaseView):
    """
    The base class for data views (as opposed to statistics views).
    
    Attributes
    ----------
    subset : str
        An expression that specifies the subset of the statistic to plot.
        Passed unmodified to `pandas.DataFrame.query`.
    """

    subset = Str
    
    def plot(self, experiment, **kwargs):
        """
        Plot some data from an experiment.  This function takes care of
        checking for facet name validity and subsetting, then passes the
        underlying dataframe to `BaseView.plot`
        
        Parameters
        ----------
        min_quantile : float (>0.0 and <1.0, default = 0.001)
            Clip data that is less than this quantile.
            
        max_quantile : float (>0.0 and <1.0, default = 1.00)
            Clip data that is greater than this quantile.
        
        Other Parameters
        ----------------
        lim : Dict(Str : (float, float))
            Set the range of each channel's axis.  If unspecified, assume
            that the limits are the minimum and maximum of the clipped data.
            Required.
            
        scale : Dict(Str : IScale)
            Scale the data on each axis.  Required.
            
        """
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")

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
            
        lim = kwargs.get('lim')
        scale = kwargs.get('scale')
            
        for c in lim.keys():
            if lim[c] is None:
                lim[c] = (experiment[c].quantile(min_quantile),
                          experiment[c].quantile(max_quantile))
            elif isinstance(lim[c], list) or isinstance(lim[c], tuple):
                if len(lim[c]) != 2:
                    raise util.CytoflowError('lim',
                                             'Length of lim\[{}\] must be 2'
                                             .format(c))
                if lim[c][0] is None:
                    lim[c] = (experiment[c].quantile(min_quantile),
                           lim[c][1])
                      
                if lim[c][1] is None:
                    lim[c] = (lim[c][0],
                           experiment[c].quantile(max_quantile))
                 
            else:
                raise util.CytoflowError('lim',
                                         "lim\[{}\] is an unknown data type"
                                         .format(c))
 
            lim[c] = [scale[c].clip(x) for x in lim[c]]
            
             
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
                 
        super().plot(experiment, 
                     experiment.data, 
                     **kwargs)
        

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
        lim : (float, float)
            Set the range of the plot's data axis.
            
        orientation : {'vertical', 'horizontal'}
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

        lim = kwargs.pop("lim", None)

        super().plot(experiment,
                     lim = {self.channel : lim},
                     scale = {self.channel : scale},
                     **kwargs)
    

class Base2DView(BaseDataView):
    """
    A data view that plots data from two channels.
    
    Attributes
    ----------
    xchannel : Str
        The channel to view on the X axis
    
    ychannel : Str
        The channel to view on the Y axis
        
    xscale : {'linear', 'log', 'logicle'} (default = 'linear')
        The scales applied to the `xchannel` data before plotting it.
        
    yscale : {'linear', 'log', 'logicle'} (default = 'linear')
        The scales applied to the `ychannel` data before plotting it.
    """
    
    xchannel = Str
    xscale = util.ScaleEnum
    ychannel = Str
    yscale = util.ScaleEnum

    def plot(self, experiment, **kwargs):
        """
        Parameters
        ----------  
        xlim : (float, float)
            Set the range of the plot's X axis.
            
        ylim : (float, float)
            Set the range of the plot's Y axis.
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
            
        xlim = kwargs.pop('xlim', None)
        ylim = kwargs.pop('ylim', None)

        super().plot(experiment, 
                     lim = {self.xchannel : xlim,
                            self.ychannel : ylim},
                     scale = {self.xchannel : xscale,
                              self.ychannel : yscale},
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
            
        if len(self.channels) != len(set(self.channels)):
            raise util.CytoflowOpError('channels', 
                                       "Must not duplicate channels")

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

        lim = kwargs.pop("lim", {})
        for c in self.channels:
            if c not in lim:
                lim[c] = None
        
        super().plot(experiment, 
                     lim = lim,
                     scale = scale,
                     **kwargs)        


@provides(IView)
class BaseStatisticsView(BaseView):
    """
    The base class for statistics views (as opposed to data views).
    
    Attributes
    ----------
    
    statistic : Str
        The statistic to plot. Must be a key in `Experiment.statistics`.
    
    xfacet : String
        Set to one of the index levels in the statistic being plotted, and 
        a new column of subplots will be added for every unique value
        of that index level.
        
    yfacet : String
        Set to one of the index levels in the statistic being plotted, and 
        a new row of subplots will be added for every unique value
        of that index level.
        
    huefacet : String
        Set to one of the index levels in the statistic being plotted, and 
        a new colored artist (line, bar, etc) will be added for every unique value
        of that index level.
        
    subset : str
        An expression that specifies the subset of the statistic to plot.
        Passed unmodified to `pandas.DataFrame.query`.

    """
    
    statistic = util.ChangedStr(err_string = "Statistics have changed dramatically -- see the documentation for updates.")   
    subset = Str
    
    def enum_plots(self, experiment):
        """
        Enumerate the named plots we can make from this set of statistics.
        
        Returns
        -------
        iterator
            An iterator across the possible plot names. The iterator ALSO has an instance
            attribute called ``by``, which holds a list of the facets that are
            not yet set (and thus need to be specified in the plot name.)
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
            
        data = self._get_stat(experiment)
        data = self._subset_data(data)
        facets = self._get_facets(experiment)
        by = list(set(data.index.names) - set(facets))
        
        class plot_enum(object):
            
            def __init__(self, data, by):
                self.by = by
                self._iter = None
                self._returned = False
                
                if by:
                    self._iter = data.groupby(by, observed = True).groups.keys().__iter__()
                
            def __iter__(self):
                return self
            
            def __next__(self):
                if self._iter:
                    return next(self._iter)
                else:
                    if self._returned:
                        raise StopIteration
                    else:
                        self._returned = True
                        return None
            
        return plot_enum(data.reset_index(), by)
    
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot some data from a statistic.
        
        This function takes care of checking for facet name validity and 
        subsetting, then passes the dataframe to `BaseView.plot`
        
        Parameters
        ----------
        plot_name : str
            If this `IView` can make multiple plots, ``plot_name`` is
            the name of the plot to make.  Must be one of the values retrieved
            from `enum_plots`.

        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
            
        data = self._get_stat(experiment)
        data = self._subset_data(data)
        facets = self._get_facets(data)

        unused_names = list(set(data.index.names) - set(facets))

        if plot_name is not None and not unused_names:
            raise util.CytoflowViewError('plot_name',
                                         "You specified a plot name, but all "
                                         "the facets are already used")
        
        if unused_names:
            groupby = data.groupby(unused_names, observed = True)

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
                
            data = groupby.get_group(plot_name if util.is_list_like(plot_name) else (plot_name,))
        
        # FacetGrid needs a "long" data set
        super().plot(experiment, data.reset_index(), **kwargs)
        
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

        return data
    
    def _get_facets(self, data):
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
            
        facets = [x for x in [self.xfacet, self.yfacet, self.huefacet] if x]
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError(None, "Can't reuse facets")
        
        return facets
        


class Base1DStatisticsView(BaseStatisticsView):
    """
    The base class for 1-dimensional statistic views -- ie, the `variable`
    attribute is on the x axis, and the statistic value is on the y axis.
    
    Attributes
    ----------

    variable : Str
        The condition that varies when plotting this statistic: used for the
        x axis of line plots, the bar groups in bar plots, etc. Must be a level
        in the statistic's index.
        
    feature : Str
        The column in the statistic to plot (often a channel name.)
        
    error_low : Str
        The name of the column used to plot low extent error bars. If 
        `error_low` is set, `error_high` must be set as well.
        
    error_high : Str
        The name of the column used to plot high extent error bars. If 
        `error_high` is set, `error_low` must be set as well.
        
    scale : {'linear', 'log', 'logicle'}
        The scale applied to the data before plotting it.
    """
    
    variable = Str
    feature = Str    
    error_low = Str
    error_high = Str
    
    scale = util.ScaleEnum
    
    error_statistic = util.Removed(err_string = "Statistics have changed dramatically -- use 'error_low' and 'error_high' instead of 'error_statistic'")
    
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Parameters
        ----------
        orientation : {'vertical', 'horizontal'}
        
        lim : (float, float)
            Set the range of the plot's axis.
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
            
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
                       
        stat = self._get_stat(experiment)
                       
        if not self.variable:
            raise util.CytoflowViewError('variable',
                                         "variable not set")
            
        if self.variable not in experiment.conditions:
            raise util.CytoflowViewError('variable',
                                         "variable {0} not in the experiment"
                                    .format(self.variable))
        
        scale = util.scale_factory(self.scale, 
                                   experiment, 
                                   statistic = self.statistic, 
                                   features = [self.feature] 
                                                + ([self.error_high] if self.error_high else []) 
                                                + ([self.error_low] if self.error_low else []))
                    
        super().plot(experiment, 
                     stat, 
                     plot_name = plot_name, 
                     scale = scale, 
                     **kwargs)
        
    def _get_stat(self, experiment):
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.statistic:
            raise util.CytoflowViewError('statistic', "Statistic not set")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic',
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
            
        stat = experiment.statistics[self.statistic]
        
        if self.feature not in stat:
            raise util.CytoflowViewError('feature',
                                         "Can't find feature {} in statistic {}. "
                                         "Possible features: {}"
                                         .format(self.feature, self.statistic, stat.columns.to_list()))
            
        if self.error_low:
            if self.error_low not in experiment.statistics[self.statistic]:
                raise util.CytoflowViewError('error_low',
                                             "Can't find the error feature {} in statistic {}. "
                                             "Possible features: {}"
                                             .format(self.error_low, self.statistic, stat.columns.to_list()))
                
            if not self.error_high:
                raise util.CytoflowViewError('error_high',
                                             "If error_low is set, error_high must be set too.")
                
        if self.error_high:
            if self.error_high not in experiment.statistics[self.statistic]:
                raise util.CytoflowViewError('error_low',
                                             "Can't find the error feature {} in statistic {}. "
                                             "Possible features: {}"
                                             .format(self.error_high, self.statistic, stat.columns.to_list()))
                
            if not self.error_low:
                raise util.CytoflowViewError('error_low',
                                             "If error_high is set, error_low must be set too.")
                
        return stat
    
    def _get_facets(self, data):
        if not self.variable:
            raise util.CytoflowViewError('variable',
                                         "Must set a variable")
                                          
        if self.variable not in data.index.names:
            raise util.CytoflowViewError('variable',
                                         "Variable {} not in statistics; must be one of {}"
                                         .format(self.xfacet, data.index.names))
            
        facets = super()._get_facets(data) + [self.variable]
        
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError(None, "Can't reuse facets")
        
        return facets


class Base2DStatisticsView(BaseStatisticsView):
    """
    The base class for 2-dimensional statistic views -- ie, the `variable`
    attribute varies independently, and the corresponding values from the x and
    y statistics are plotted on the x and y axes.
    
    Attributes
    ----------
    
    variable : Str
        The condition that varies when plotting this statistic: used for the
        x axis of line plots, the bar groups in bar plots, etc. Must be a level
        in the statistic's index.
        
    xfeature : Str
        The name of the column to plot on the X axis.
        
    xerror_low : Str
        The name of the column containing the low values for the X error bars.
        If `xerror_low` is set, `xerror_high` must be set as well.
        
    xerror_high : Str
        The name of the column containing the high values for the X error bars.
        If `xerror_high` is set, `xerror_low` must be set as well.
        
    yfeature : Str
        The name of the column to plot on the Y axis.
        
    yerror_low : Str
        The name of the column containing the low values for the Y error bars.
        If `yerror_low` is set, `yerror_high` must be set as well.
        
    yerror_high : Str
        The name of the column containing the high values for the Y error bars.
        If `yerror_high` is set, `yerror_low` must be set as well.
        
    xscale : {'linear', 'log', 'logicle'}
        The scale applied to X axis.
        
    yscale : {'linear', 'log', 'logicle'}
        The scale applied to Y axis.
    """
    
    xstatistic = util.Removed(err_string = "Statistics have changed dramatically -- use 'statistic' and 'xfeature' instead of 'xstatistic'")
    ystatistic = util.Removed(err_string = "Statistics have changed dramatically -- use 'statistic' and 'yfeature' instead of 'ystatistic'")
    x_error_statistic = util.Removed(err_string = "Statistics have changed dramatically -- use 'xerror_low' and 'xerror_high' instead of 'x_error_statistic'")
    y_error_statistic = util.Removed(err_string = "Statistics have changed dramatically -- use 'yerror_low' and 'yerror_high' instead of 'y_error_statistic'")
    
    statistic = Str
    variable = Str
    xfeature = Str
    xerror_low = Str
    xerror_high = Str
    
    yfeature = Str
    yerror_low = Str
    yerror_high = Str
    
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Parameters
        ----------
        xlim : (float, float)
            Set the range of the plot's X axis.
            
        ylim : (float, float)
            Set the range of the plot's Y axis.
        """
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")

        if not self.variable:
            raise util.CytoflowViewError('variable',
                                         "variable not set")
            
        if self.variable not in experiment.conditions:
            raise util.CytoflowViewError('variable',
                                         "variable {0} not in the experiment"
                                    .format(self.variable))
        
        data = self._get_stat(experiment)

        xscale = util.scale_factory(self.xscale, 
                                    experiment, 
                                    statistic = self.statistic, 
                                    features = [self.xfeature]  
                                                + ([self.xerror_low] if self.xerror_low else [])
                                                + ([self.xerror_high] if self.xerror_high else []))
        
        yscale = util.scale_factory(self.yscale, 
                                    experiment, 
                                    statistic = self.statistic,
                                    features = [self.yfeature]  
                                                + ([self.yerror_low] if self.yerror_low else [])
                                                + ([self.yerror_high] if self.yerror_high else []))
            
        super().plot(experiment, 
                     data, 
                     plot_name, 
                     xscale = xscale, 
                     yscale = yscale, 
                     **kwargs)
        
    def _get_stat(self, experiment):
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.statistic:
            raise util.CytoflowViewError('statistic', "Statistic not set")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic',
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
            
        stat = experiment.statistics[self.statistic]
        
        if self.xfeature not in stat:
            raise util.CytoflowViewError('xfeature',
                                         "Can't find feature {} in statistic {}. "
                                         "Possible features: {}"
                                         .format(self.xfeature, self.statistic, stat.columns.to_list()))
            
        if self.yfeature not in stat:
            raise util.CytoflowViewError('yfeature',
                                         "Can't find feature {} in statistic {}. "
                                         "Possible features: {}"
                                         .format(self.yfeature, self.statistic, stat.columns.to_list()))
            
        if self.xerror_low:
            if self.xerror_low not in experiment.statistics[self.statistic]:
                raise util.CytoflowViewError('xerror_low',
                                             "Can't find the x error feature {} in statistic {}. "
                                             "Possible features: {}"
                                             .format(self.xerror_low, self.statistic, stat.columns.to_list()))
                
            if not self.xerror_high:
                raise util.CytoflowViewError('xerror_high',
                                             "If xerror_low is set, xerror_high must be set too.")
                
        if self.xerror_high:
            if self.xerror_high not in experiment.statistics[self.statistic]:
                raise util.CytoflowViewError('xerror_high',
                                             "Can't find the error feature {} in statistic {}. "
                                             "Possible features: {}"
                                             .format(self.xerror_high, self.statistic, stat.columns.to_list()))
                
            if not self.xerror_low:
                raise util.CytoflowViewError('xerror_low',
                                             "If xerror_high is set, xerror_low must be set too.")
                
        if self.yerror_low:
            if self.yerror_low not in experiment.statistics[self.statistic]:
                raise util.CytoflowViewError('yerror_low',
                                             "Can't find the y error feature {} in statistic {}. "
                                             "Possible features: {}"
                                             .format(self.yerror_low, self.statistic, stat.columns.to_list()))
                
            if not self.yerror_high:
                raise util.CytoflowViewError('yerror_high',
                                             "If yerror_low is set, yerror_high must be set too.")
                
        if self.yerror_high:
            if self.yerror_high not in experiment.statistics[self.statistic]:
                raise util.CytoflowViewError('yerror_high',
                                             "Can't find the error feature {} in statistic {}. "
                                             "Possible features: {}"
                                             .format(self.yerror_high, self.statistic, stat.columns.to_list()))
                
            if not self.yerror_low:
                raise util.CytoflowViewError('yerror_low',
                                             "If yerror_high is set, yerror_low must be set too.")
                
        return stat
    
    def _get_facets(self, data):
        if not self.variable:
            raise util.CytoflowViewError('variable',
                                         "Must set a variable")
                                          
        if self.variable not in data.index.names:
            raise util.CytoflowViewError('variable',
                                         "Variable {} not in statistics; must be one of {}"
                                         .format(self.xfacet, data.index.names))
            
        facets = super()._get_facets(data) + [self.variable]
        
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError(None, "Can't reuse facets")
        
        return facets



