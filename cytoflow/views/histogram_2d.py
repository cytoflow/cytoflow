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

"""
Created on Apr 19, 2015

@author: brian
"""

from __future__ import division, absolute_import

import warnings

from traits.api import HasStrictTraits, provides, Str, Int

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import Colormap
from scipy.interpolate import griddata

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class Histogram2DView(HasStrictTraits):
    """
    Plots a 2-d histogram.  
    
    Attributes
    ----------
    
    name : Str
        The name of the plot, for visualization (and the plot title)
        
    xchannel : Str
        The channel to plot on the X axis
        
    ychannel : Str
        The channel to plot on the Y axis
        
    xfacet : Str
        The conditioning variable for multiple plots (horizontal)
        
    yfacet = Str
        The conditioning variable for multiple plots (vertical)
        
    huefacet = Str
        The conditioning variable for multiple plots (color)
        
    huescale = Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the color bar, if there is one plotted

    subset = Str
        A string passed to pandas.DataFrame.query() to subset the data before
        we plot it.
        
    smoothed = Bool(False)
        Smooth the histogram with a cubic spline

    """
    
    id = 'edu.mit.synbio.cytoflow.view.histogram2d'
    friend_id = "2D Histogram"
    
    name = Str
    xchannel = Str
    ychannel = Str
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    xfacet = Str
    yfacet = Str
    huefacet = Str
    huescale = util.ScaleEnum
    subset = Str
    
    _max_bins = Int(100)
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.xchannel:
            raise util.CytoflowViewError("X channel not specified")
        
        if self.xchannel not in experiment.data:
            raise util.CytoflowViewError("X channel {0} not in the experiment"
                                    .format(self.xchannel))
            
        if not self.ychannel:
            raise util.CytoflowViewError("Y channel not specified")
        
        if self.ychannel not in experiment.data:
            raise util.CytoflowViewError("Y channel {0} not in the experiment")
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} not in the experiment")
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment")
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise util.CytoflowViewError("Hue facet {0} not in the experiment")
        
        facets = filter(lambda x: x, [self.xfacet, self.yfacet, self.huefacet])
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError("Can't reuse facets")
        
        col_wrap = kwargs.pop('col_wrap', None)
        
        if col_wrap and self.yfacet:
            raise util.CytoflowViewError("Can't set yfacet and col_wrap at the same time.") 
        
        if col_wrap and not self.xfacet:
            raise util.CytoflowViewError("Must set xfacet to use col_wrap.")

        if self.subset:
            try: 
                data = experiment.query(self.subset).data.reset_index()
            except:
                raise util.CytoflowViewError("Subset string \'{0}\' not valid")
                            
            if len(data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
            
        xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)
        yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)

        kwargs['xscale'] = xscale
        kwargs['yscale'] = yscale
        
        scaled_xdata = xscale(data[self.xchannel])
        data = data[~np.isnan(scaled_xdata)]
        scaled_xdata = scaled_xdata[~np.isnan(scaled_xdata)]

        scaled_ydata = yscale(data[self.ychannel])
        data = data[~np.isnan(scaled_ydata)]
        scaled_ydata = scaled_ydata[~np.isnan(scaled_ydata)]
        

        # find good bin counts
        num_xbins = util.num_hist_bins(scaled_xdata)
        num_ybins = util.num_hist_bins(scaled_ydata)
        
        # there are situations where this produces an unreasonable estimate.
        if num_xbins > self._max_bins:
            warnings.warn("Capping X bins to {}! To increase this limit, "
                          "change _max_bins"
                          .format(self._max_bins))
            num_xbins = self._max_bins
            
        if num_ybins > self._max_bins:
            warnings.warn("Capping Y bins to {}! To increase this limit, "
                          "change _max_bins"
                          .format(self._max_bins))
            num_ybins = self._max_bins
      
        kwargs.setdefault('smoothed', False)
        if kwargs['smoothed']:
            num_xbins /= 2
            num_ybins /= 2
                
        _, xedges, yedges = np.histogram2d(scaled_xdata, 
                                           scaled_ydata, 
                                           bins = (num_xbins, num_ybins))

        kwargs['xedges'] = xscale.inverse(xedges)
        kwargs['yedges'] = yscale.inverse(yedges)
        
        kwargs.setdefault('antialiased', True)
        
        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 0.999) 
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (data[self.xchannel].quantile(min_quantile),
                    data[self.xchannel].quantile(max_quantile))
                      
        ylim = kwargs.pop("ylim", None)
        if ylim is None:
            ylim = (data[self.ychannel].quantile(min_quantile),
                    data[self.ychannel].quantile(max_quantile))
            
        sharex = kwargs.pop('sharex', True)
        sharey = kwargs.pop('sharey', True)

        cols = col_wrap if col_wrap else \
               len(data[self.xfacet].unique()) if self.xfacet else 1

        g = sns.FacetGrid(data,
                          size = (6 / cols),
                          aspect = 1.5, 
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                          col_wrap = col_wrap,
                          sharex = sharex,
                          sharey = sharey,
                          xlim = xlim,
                          ylim = ylim)
         
        for ax in g.axes.flatten():
            ax.set_xscale(self.xscale, **xscale.mpl_params)
            ax.set_yscale(self.yscale, **yscale.mpl_params)
        
        g.map(_hist2d, self.xchannel, self.ychannel, **kwargs)
            
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

        # if we have a hue facet and a lot of hues, make a color bar instead
        # of a super-long legend.
        
        if self.huefacet:
            current_palette = mpl.rcParams['axes.color_cycle']
            if util.is_numeric(experiment.data[self.huefacet]) and \
               len(g.hue_names) > len(current_palette):
                
                plot_ax = plt.gca()
                cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
                                                                   n_colors = len(g.hue_names)))
                cax, _ = mpl.colorbar.make_axes(plt.gca())
                hue_scale = util.scale_factory(self.huescale, 
                                               experiment, 
                                               condition = self.huefacet)
                mpl.colorbar.ColorbarBase(cax, 
                                          cmap = cmap, 
                                          norm = hue_scale.color_norm(),
                                          label = self.huefacet)
                plt.sca(plot_ax)
            else:
                g.add_legend(title = self.huefacet)
        

def _hist2d(x, y, xedges = None, yedges = None, xscale = None, yscale = None, smoothed = False, **kwargs):

    ax = plt.gca()
    
    x = xscale(x)
    y = yscale(y)    
    h, _, _ = np.histogram2d(x, y, 
                             bins = (xscale(xedges), 
                                     yscale(yedges)))
    X, Y = np.meshgrid(xedges[1:], yedges[1:])
    
    if smoothed:
        grid_x, grid_y = np.mgrid[xscale(xedges[0]):xscale(xedges[-1]):100j, 
                                  yscale(yedges[0]):yscale(yedges[-1]):100j]
        
        loc = [(x, y) for x in xscale(xedges[1:]) for y in yscale(yedges[1:])]
         
        h = griddata(loc, h.flatten(), (grid_x, grid_y), method = "linear", fill_value = 0)
         
        X, Y = xscale.inverse(grid_x), yscale.inverse(grid_y)
    else:
        h = h.T

    color = kwargs.pop("color")   
    ax.pcolormesh(X, Y, h, cmap = AlphaColormap("AlphaColor", color), **kwargs)
        
    return ax

class AlphaColormap(Colormap):        
    def __init__(self, name, color, min_alpha = 0.0, max_alpha = 1.0, N=256):
        Colormap.__init__(self, name, N)
        self._color = color
        self._min_alpha = min_alpha
        self._max_alpha = max_alpha
        
    def _init(self):
        self._lut = np.ones((self.N + 3, 4), np.float)
        self._lut[:-3, 0] = self._color[0]
        self._lut[:-3, 1] = self._color[1]
        self._lut[:-3, 2] = self._color[2]
        self._lut[:-3, 3] = np.linspace(self._min_alpha, self._max_alpha, num = self.N, dtype = np.float)
        self._isinit = True
        self._set_extremes()    