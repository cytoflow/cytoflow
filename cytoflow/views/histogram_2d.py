#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
cytoflow.views.histogram_2d
---------------------------
"""

from traits.api import provides

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
    Plots a 2-d histogram.  Similar to a density plot, but the number of
    events in a bin change the bin's opacity, so you can use different colors.  
    
    Attributes
    ----------

    Examples
    --------
    
    Make a little data set.
    
    .. plot::
        :context: close-figs
            
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
        
    Plot a density plot
    
    .. plot::
        :context: close-figs
    
        >>> flow.Histogram2DView(xchannel = 'V2-A',
        ...                      xscale = 'log',
        ...                      ychannel = 'Y2-A',
        ...                      yscale = 'log',
        ...                      huefacet = 'Dox').plot(ex)
        
    The same plot, smoothed, with a log color scale.  
    
    .. plot::
        :context: close-figs

        >>> flow.Histogram2DView(xchannel = 'V2-A',
        ...                      xscale = 'log',
        ...                      ychannel = 'Y2-A',
        ...                      yscale = 'log',
        ...                      huefacet = 'Dox',
        ...                      huescale = 'log').plot(ex, smoothed = True)  
    """
    
    id = 'edu.mit.synbio.cytoflow.view.histogram2d'
    friend_id = "2D Histogram"
        
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted density plot view of a channel
        
        Parameters
        ----------
        gridsize : int
            The number of bins on the X and Y axis.
            
        smoothed : bool
            Should the mesh be smoothed?
            
        smoothed_sigma : int
            The standard deviation of the smoothing kernel.  default = 1.
            
        Notes
        -----
        Other `kwargs` are passed to `matplotlib.axes.Axes.pcolormesh <https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.pcolormesh.html>`_
    
        """
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, **kwargs):

        kwargs.setdefault('antialiased', False)
        kwargs.setdefault('linewidth', 0)
        kwargs.setdefault('edgecolors', 'face')
        
        lim = kwargs.pop('lim')
        xlim = lim[self.xchannel]
        ylim = lim[self.ychannel]
        
        scale = kwargs.pop('scale')
        xscale = scale[self.xchannel]
        yscale = scale[self.ychannel]
        
        gridsize = kwargs.pop('gridsize', 50)
        xbins = xscale.inverse(np.linspace(xscale(xlim[0]), xscale(xlim[1]), gridsize))
        ybins = yscale.inverse(np.linspace(yscale(ylim[0]), yscale(ylim[1]), gridsize))
      
        kwargs.setdefault('smoothed', False)
        
        legend_data = {}
           
        grid.map(_hist2d, self.xchannel, self.ychannel, xbins = xbins, ybins = ybins, legend_data = legend_data, **kwargs)
        
        return dict(xlim = xlim,
                    xscale = xscale,
                    ylim = ylim,
                    yscale = yscale,
                    legend_data = legend_data)
        
    def _update_legend(self, legend):
        for lh in legend.legendHandles:
            lh.set_alpha(0.5)
            #lh.set_sizes([10.0])

def _hist2d(x, y, xbins, ybins, legend_data, **kwargs):

    h, X, Y = np.histogram2d(x, y, bins=[xbins, ybins])
    
    smoothed = kwargs.pop('smoothed', False)
    smoothed_sigma = kwargs.pop('smoothed_sigma', 1)
    
    if smoothed:
        h = gaussian_filter(h, sigma = smoothed_sigma)

    ax = plt.gca()

    color = kwargs.pop("color")   
    ax.pcolormesh(X, Y, h.T, cmap = AlphaColormap("AlphaColor", color), **kwargs)
    
    # Add legend data
    if 'label' in kwargs:
        legend_data[kwargs['label']] = plt.Rectangle((0, 0), 1, 1, fc = color)
        
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
        
util.expand_class_attributes(Histogram2DView)
util.expand_method_parameters(Histogram2DView, Histogram2DView.plot)