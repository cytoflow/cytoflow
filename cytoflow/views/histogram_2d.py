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

from traits.api import HasStrictTraits, provides, Str

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
#import matplotlib.transforms as mtrans
from matplotlib.colors import Colormap
import matplotlib.cbook as cbook

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

    subset = Str
        A string passed to pandas.DataFrame.query() to subset the data before
        we plot it.
        
        .. note: should this be a param instead?
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
    subset = Str
    
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

        if self.subset:
            try: 
                data = experiment.query(self.subset)
            except:
                raise util.CytoflowViewError("Subset string \'{0}\' not valid")
                            
            if len(data.index) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
            
        xscale = util.scale_factory(self.xscale, experiment, self.xchannel)
        yscale = util.scale_factory(self.yscale, experiment, self.ychannel)

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
        
        _, xedges, yedges = np.histogram2d(scaled_xdata, 
                                           scaled_ydata, 
                                           bins = (num_xbins, num_ybins))

        kwargs['xedges'] = xscale.inverse(xedges)
        kwargs['yedges'] = yscale.inverse(yedges)

        kwargs.setdefault('antialiased', True)

        g = sns.FacetGrid(data,
                          size = 6,
                          aspect = 1.5, 
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                          sharex = False,
                          sharey = False)
         
        for ax in g.axes.flatten():
            ax.set_xscale(self.xscale, **xscale.mpl_params)
            ax.set_yscale(self.yscale, **yscale.mpl_params)
        
        g.map(_hist2d, self.xchannel, self.ychannel, **kwargs)
        

def _hist2d(x, y, xedges = None, yedges = None, xscale = None, yscale = None, **kwargs):

    ax = plt.gca()
    
    x = xscale(x)
    y = yscale(y)    
    h, _, _ = np.histogram2d(x, y, 
                             bins = (xscale(xedges), 
                                     yscale(yedges)))

    X, Y = np.meshgrid(xedges, yedges)
    
    color = kwargs.pop("color")
    print kwargs
    
    ax.pcolormesh(X, Y, h.transpose(), cmap = AlphaColormap("AlphaColor", color), **kwargs)
        
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