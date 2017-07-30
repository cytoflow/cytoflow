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
Created on Jul 30, 2017

@author: brian
'''

from traits.api import HasStrictTraits, Str, provides
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns
import math
import bottleneck

from warnings import warn

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class BaseView(HasStrictTraits):
    
    xfacet = Str
    yfacet = Str
    huefacet = Str
    huescale = util.ScaleEnum
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """
        Base function for facetted plotting of data (not statistics.)
        
        Parameters
        ----------
            
        legend : bool
            Plot a legend for the color or hue facet?  Defaults to `True`.
            
        sharex, sharey : bool
            If there are multiple subplots, should they share axes?  Defaults
            to `True`.
            
        xlim, ylim : (float, float)
            Set the min and max limits of the plots' x and y axes.
            
        min_quantile, max_quantile : float
            Set the minimum and maximum quantiles of the data to plot.  Can
            be used to exclude outliers; both must be in `[0, 1]`.  
            `min_quantile` has a default of `0.001`, and `max_quantile` has
            a default of `1.0`.
            
        col_wrap : int
            If `xfacet` is set and `yfacet` is not set, you can "wrap" the
            subplots around so that they form a multi-row grid by setting
            `col_wrap` to the number of columns you want. 
        """
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} not in the experiment"
                                    .format(self.xfacet))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment"
                                    .format(self.yfacet))
        
        if self.huefacet and self.huefacet not in experiment.conditions:
            raise util.CytoflowViewError("Hue facet {0} not in the experiment"
                                    .format(self.huefacet))
            
        facets = [x for x in [self.xfacet, self.yfacet, self.huefacet] if x]
        
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError("Can't reuse facets")
        
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except util.CytoflowError as e:
                raise util.CytoflowViewError(str(e)) from e
            except Exception as e:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset)) from e
                
            if len(experiment) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
                

            
        col_wrap = kwargs.pop('col_wrap', None)
        
        if col_wrap and self.yfacet:
            raise util.CytoflowViewError("Can't set yfacet and col_wrap at the same time.")
        
        if col_wrap and not self.xfacet:
            raise util.CytoflowViewError("Must set xfacet to use col_wrap.")
        
        sharex = kwargs.pop("sharex", True)
        sharey = kwargs.pop("sharey", True)

        xscale = kwargs.pop("xscale", None)
        yscale = kwargs.pop("yscale", None)
        
        xlim = kwargs.pop("xlim", None)
        ylim = kwargs.pop("ylim", None)
        
        legend = kwargs.pop('legend', True)
        
        cols = col_wrap if col_wrap else \
               len(experiment[self.xfacet].unique()) if self.xfacet else 1
            
        g = sns.FacetGrid(experiment.data, 
                          size = 6 / cols,
                          aspect = 1.5,
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          col_order = (np.sort(experiment[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(experiment[self.yfacet].unique()) if self.yfacet else None),
                          hue_order = (np.sort(experiment[self.huefacet].unique()) if self.huefacet else None),
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
            
                if util.is_numeric(experiment.data[self.huefacet]) and \
                   len(g.hue_names) > len(current_palette):
    
                    cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
                                                                       n_colors = len(g.hue_names)))                
                    hue_scale = util.scale_factory(self.huescale, 
                                                   experiment, 
                                                   condition = self.huefacet)
                    
                    plot_ax = plt.gca()
    
                    cax, _ = mpl.colorbar.make_axes(plt.gcf().get_axes())
    
                    mpl.colorbar.ColorbarBase(cax, 
                                              cmap = cmap, 
                                              norm = hue_scale.color_norm(), 
                                              label = self.huefacet)
                    plt.sca(plot_ax)
                else:
                    g.add_legend(title = self.huefacet)
        

        # do the plotting on g

@provides(IView)
class Base1DView(BaseView):
    
    channel = Str
    scale = util.ScaleEnum
    
    def plot(self, experiment, **kwargs):
        
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.channel:
            raise util.CytoflowViewError("Must specify a channel")
        
        if self.channel not in experiment.data:
            raise util.CytoflowViewError("Channel {0} not in the experiment"
                                    .format(self.channel))
        
        # get the scale
        scale = kwargs.pop('scale', None)
        if scale is None:
            scale = util.scale_factory(self.scale, experiment, channel = self.channel)
        
        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 1.0) 
        
        if min_quantile < 0.0 or min_quantile > 1:
            raise util.CytoflowViewError("min_quantile must be between 0 and 1")

        if max_quantile < 0.0 or max_quantile > 1:
            raise util.CytoflowViewError("max_quantile must be between 0 and 1")     
        
        if min_quantile >= max_quantile:
            raise util.CytoflowViewError("min_quantile must be less than max_quantile")   
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (experiment[self.channel].quantile(min_quantile),
                    experiment[self.channel].quantile(max_quantile))
        
        super().plot(experiment, xlim = xlim, xscale = scale, **kwargs)
    
@provides(IView)
class Base2DView(BaseView):
    
    xchannel = Str
    xscale = util.ScaleEnum
    ychannel = Str
    yscale = util.ScaleEnum

    def plot(self, experiment, **kwargs):

        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")

        if not self.xchannel:
            raise util.CytoflowViewError("Must specify an xchannel")
        
        if self.xchannel not in experiment.data:
            raise util.CytoflowViewError("Channel {} not in the experiment"
                                    .format(self.xchannel))

        if not self.ychannel:
            raise util.CytoflowViewError("Must specify a ychannel")
        
        if self.ychannel not in experiment.data:
            raise util.CytoflowViewError("Channel {} not in the experiment"
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
            raise util.CytoflowViewError("min_quantile must be between 0 and 1")

        if max_quantile < 0.0 or max_quantile > 1:
            raise util.CytoflowViewError("max_quantile must be between 0 and 1")     
        
        if min_quantile >= max_quantile:
            raise util.CytoflowViewError("min_quantile must be less than max_quantile")   
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (experiment[self.xchannel].quantile(min_quantile),
                    experiment[self.xchannel].quantile(max_quantile))

        ylim = kwargs.pop("ylim", None)
        if ylim is None:
            ylim = (experiment[self.ychannel].quantile(min_quantile),
                    experiment[self.ychannel].quantile(max_quantile))
        
        super().plot(experiment, 
                     xlim = xlim,
                     xscale = xscale, 
                     ylim = ylim,
                     yscale = yscale, 
                     **kwargs)        

    
@provides(IView)
class BaseNDView(BaseView):
    pass
    
    
    