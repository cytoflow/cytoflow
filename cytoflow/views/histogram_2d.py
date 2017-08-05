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

"""
Created on Apr 19, 2015

@author: brian
"""

import warnings

from traits.api import provides, Str

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Colormap
from scipy.ndimage.filters import gaussian_filter

import cytoflow.utility as util
from .i_view import IView
from .base_views import Base2DView

@provides(IView)
class Histogram2DView(Base2DView):
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
x

    """
    
    id = 'edu.mit.synbio.cytoflow.view.histogram2d'
    friend__id = "2D Histogram"
    
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
        
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted density plot view of a channel
        
        Parameters
        ----------
        xbins : int
            The number of bins on the x axis
            
        ybins : int
            The number of bins on the y axis.
            
        max_bins : int
            Sometimes the number of bins estimated by the plot function is
            unreasonable.  This caps the maximum number.  Defaults to 100.
            
        smoothed : bool
            Should the resulting mesh be smoothed?
            
        smoothed_sigma : int
            The standard deviation of the smoothing kernel.  default = 1.
            
        Other Parameters
        ----------------
        Other `kwargs` are passed to matplotlib.axes.Axes.pcolormesh_.
        
        .. _matplotlib.axes.Axes.pcolormesh: https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.pcolormesh.html
    
        See Also
        --------
        BaseView.plot : common parameters for data views
        
        """
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):

        scaled_xdata = xscale(experiment[self.xchannel])
        scaled_xdata = scaled_xdata[~np.isnan(scaled_xdata)]

        scaled_ydata = yscale(experiment[self.ychannel])
        scaled_ydata = scaled_ydata[~np.isnan(scaled_ydata)]
        
        # find good bin counts
        num_xbins = kwargs.pop('xbins', util.num_hist_bins(scaled_xdata))
        num_ybins = kwargs.pop('ybins', util.num_hist_bins(scaled_ydata))
        
        max_bins = kwargs.pop('max_bins', 100)
        
        # there are situations where this produces an unreasonable estimate.
        if num_xbins > max_bins:
            warnings.warn("Capping X bins to {}! To increase this limit, "
                          "change max_bins"
                          .format(max_bins))
            num_xbins = max_bins
            
        if num_ybins > max_bins:
            warnings.warn("Capping Y bins to {}! To increase this limit, "
                          "change max_bins"
                          .format(max_bins))
            num_ybins = max_bins
      
        kwargs.setdefault('smoothed', False)

        xbins = xscale.inverse(np.linspace(xscale(xlim[0]), xscale(xlim[1]), num_xbins))
        ybins = yscale.inverse(np.linspace(yscale(ylim[0]), yscale(ylim[1]), num_ybins))

        kwargs.setdefault('antialiased', False)
        kwargs.setdefault('linewidth', 0)
        kwargs.setdefault('edgecolors', 'face')
            
        grid.map(_hist2d, self.xchannel, self.ychannel, xbins = xbins, ybins = ybins, **kwargs)
        
        return {}
            

def _hist2d(x, y, xbins, ybins, **kwargs):

    h, X, Y = np.histogram2d(x, y, bins=[xbins, ybins])
    
    smoothed = kwargs.pop('smoothed', False)
    smoothed_sigma = kwargs.pop('smoothed_sigma', 1)
    
    if smoothed:
        h = gaussian_filter(h, sigma = smoothed_sigma)
    else:
        h = h.T

    ax = plt.gca()
    ax.pcolormesh(X, Y, h, **kwargs)

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