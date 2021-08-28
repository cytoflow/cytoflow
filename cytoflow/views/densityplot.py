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
cytoflow.views.densityplot
--------------------------

Plot a 2D density plot.

`DensityView` -- the `IView` class that makes the plot.
"""

from traits.api import provides, Constant

import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage.filters
import copy

import cytoflow.utility as util
from .i_view import IView

from .base_views import Base2DView

@provides(IView)
class DensityView(Base2DView):
    """
    Plots a 2-d density plot.  
    
    Attributes
    ----------
    
    huefacet : None
        You must leave the hue facet unset!
        
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
    
        >>> flow.DensityView(xchannel = 'V2-A',
        ...                 xscale = 'log',
        ...                 ychannel = 'Y2-A',
        ...                 yscale = 'log').plot(ex)
        
    The same plot, smoothed, with a log color scale.  *Note - you can change*
    *the hue scale, even if you don't have control over the hue facet!*
    
    .. plot::
        :context: close-figs

        >>> flow.DensityView(xchannel = 'V2-A',
        ...                  xscale = 'log',
        ...                  ychannel = 'Y2-A',
        ...                  yscale = 'log',
        ...                  huescale = 'log').plot(ex, smoothed = True)        
    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.density')
    friend_id = Constant("Density Plot")
    
    huefacet = Constant(None)
    
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted density plot view of a channel
        
        Parameters
        ----------
        gridsize : int
            The size of the grid on each axis.  Default = 50
            
        smoothed : bool
            Should the resulting mesh be smoothed?
            
        smoothed_sigma : int
            The standard deviation of the smoothing kernel.  default = 1.
            
        cmap : cmap
            An instance of matplotlib.colors.Colormap.  By default, the 
            ``viridis`` colormap is used
            
        under_color : matplotlib color
            Sets the color to be used for low out-of-range values.
            
        bad_color : matplotlib color
            Set the color to be used for masked values.
            
        Notes
        -----
        Other ``kwargs`` are passed to `matplotlib.axes.Axes.pcolormesh`
        
        """
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, **kwargs):

        kwargs.setdefault('antialiased', False)
        kwargs.setdefault('linewidth', 0)
        kwargs.setdefault('edgecolors', 'face')
        kwargs.setdefault('cmap', plt.get_cmap('viridis'))
        
        lim = kwargs.pop('lim')
        xlim = lim[self.xchannel]
        ylim = lim[self.ychannel]
        
        scale = kwargs.pop('scale')
        xscale = scale[self.xchannel]
        yscale = scale[self.ychannel]
        
        # can't modify color maps in place!
        cmap = copy.copy(kwargs['cmap'])
        
        under_color = kwargs.pop('under_color', None)
        if under_color is not None:
            cmap.set_under(color = under_color)
        else:
            cmap.set_under(cmap(0.0))

        bad_color = kwargs.pop('bad_color', None)
        if bad_color is not None:
            cmap.set_bad(color = bad_color)
        else:
            cmap.set_bad(color = cmap(0.0))
            
        gridsize = kwargs.pop('gridsize', 50)

        xbins = xscale.inverse(np.linspace(xscale(xlim[0]), xscale(xlim[1]), gridsize))
        ybins = yscale.inverse(np.linspace(yscale(ylim[0]), yscale(ylim[1]), gridsize))
  
        # set up the range of the color map
        if 'norm' not in kwargs:
            data_max = 0
            for _, data_ijk in grid.facet_data():
                x = data_ijk[self.xchannel]
                y = data_ijk[self.ychannel]
                h, _, _ = np.histogram2d(x, y, bins=[xbins, ybins])
                data_max = max(data_max, h.max())
                
            hue_scale = util.scale_factory(self.huescale, 
                                           experiment, 
                                           data = np.array([1, data_max]))
            kwargs['norm'] = hue_scale.norm()
        
        grid.map(_densityplot, self.xchannel, self.ychannel, xbins = xbins, ybins = ybins, **kwargs)
               
        return dict(xlim = xlim,
                    xscale = xscale,
                    ylim = ylim,
                    yscale = yscale,
                    cmap = kwargs['cmap'], 
                    norm = kwargs['norm'])
        
        
def _densityplot(x, y, xbins, ybins, **kwargs):
    
    h, X, Y = np.histogram2d(x, y, bins=[xbins, ybins])
    
    smoothed = kwargs.pop('smoothed', False)
    smoothed_sigma = kwargs.pop('smoothed_sigma', 1)
    
    if smoothed:
        h = scipy.ndimage.filters.gaussian_filter(h, sigma = smoothed_sigma)

    ax = plt.gca()
    ax.pcolormesh(X, Y, h.T, **kwargs)
    
util.expand_class_attributes(DensityView)
util.expand_method_parameters(DensityView, DensityView.plot)
         
         
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
    thresh.threshold = 200.0

    ex2 = thresh.apply(ex)
    
    scatter = flow.ScatterplotView()
    scatter.name = "Scatter"
    scatter.xchannel = "FSC-A"
    scatter.ychannel = "SSC-A"
    scatter.xscale = "logicle"
    scatter.yscale = "logicle"
    scatter.huefacet = 'Dox'
    
    plt.ioff()
    scatter.plot(ex2)
    plt.show()