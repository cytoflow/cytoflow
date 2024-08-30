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
cytoflow.views.parallel_coords
------------------------------

A parallel-coordinates plot.

`ParallelCoordinatesView` -- the `IView` class that makes the plot.
"""

from traits.api import provides, Constant

import matplotlib.pyplot as plt
import matplotlib.collections

import pandas as pd
import numpy as np

import cytoflow.utility as util
from .i_view import IView
from .view_kwargs import try_get_kwarg

from .base_views import BaseNDView

@provides(IView)
class ParallelCoordinatesView(BaseNDView):
    """
    Plots a parallel coordinates plot.  PC plots are good for multivariate
    data; each vertical line represents one attribute, and one set of
    connected line segments represents one data point.

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
        
    Plot the PC plot.
    
    .. plot::
        :context: close-figs
    
        >>> flow.ParallelCoordinatesView(channels = ['B1-A', 'V2-A', 'Y2-A', 'FSC-A'],
        ...                              scale = {'Y2-A' : 'log',
        ...                                       'V2-A' : 'log',
        ...                                       'B1-A' : 'log',
        ...                                       'FSC-A' : 'log'},
        ...                              huefacet = 'Dox').plot(ex)
            
    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.parallel_coords')
    friend_id = Constant("Parallel Coordinates Plot")
        
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted parallel coordinates plot
        
        Parameters
        ----------
        
        alpha : float (default = 0.02)
            The alpha blending value, between 0 (transparent) and 1 (opaque).

        axvlines_kwds : dict
            A dictionary of parameters to pass to `ax.axvline <https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.axvline.html>`_

        
        Notes
        -----
        This uses a low-level API for speed; there are far fewer visual options
        that with other views.
  
        """
        
        if len(self.channels) < 3:
            raise util.CytoflowViewError('channels',
                                         "Must have at least 3 channels")
        
        super().plot(experiment, **kwargs)
        
        # clean up the plot
        for ax in plt.gcf().get_axes():
            ax.set_xlabel("")
            ax.set_ylabel("")
            ax.get_yaxis().set_ticks([])
        
    def _grid_plot(self, experiment, grid, **kwargs):
        
        # xlim and ylim, xscale and yscale are the limits and scale of the
        # plane onto which we are projecting.  the kwargs 'scale' and 'lim'
        # are the data scale and limits, respectively
        
        scale = try_get_kwarg(kwargs,'scale')
        lim = try_get_kwarg(kwargs,'lim')
        
        # TODO - some way to optimize attribute order
        # TODO - allow changing attribute spacing
        
        # memo to track if we've put annotations on an axes yet
        ax_annotations = {}
                
        grid.map(_parallel_coords_plot, 
                 *self.channels, 
                 ax_annotations = ax_annotations, 
                 scale = scale,
                 lim = lim,
                 **kwargs)
   
        return {}
    
    
    def _update_legend(self, legend):
        for lh in legend.legendHandles:
            lh.set_alpha(0.5)
            lh.set_linewidth(3)
    
def _parallel_coords_plot(*channels, ax_annotations, scale, lim, **kwargs):

    color = try_get_kwarg(kwargs,'color')
    alpha = try_get_kwarg(kwargs,'alpha', 0.02)
    aa = try_get_kwarg(kwargs,'antialiased', True)
    color = tuple(list(color) + [alpha])
    label = try_get_kwarg(kwargs,'label', None)
        
    df = pd.DataFrame()
    for c in channels:
        vmin = lim[c.name][0]
        vmax = lim[c.name][1]
        c_scaled = pd.Series(data = scale[c.name].norm(vmin = vmin, vmax = vmax)(c.values),
                             index = c.index,
                             name = c.name)

        c_scaled[(c < vmin) | (c > vmax)] = np.nan
        df[c.name] = c_scaled
        
    df.dropna(axis = 0, how = 'any', inplace = True)
    
    # adapted from pandas.plotting._misc
    
    axvlines_kwds = try_get_kwarg(kwargs,'axvlines_kwds', {'linewidth' : 1, 'color' : 'black'})
    
    ax = plt.gca()
    
    # we're creating a LineCollection manually because it's much much much
    # faster than the higher-level plotting routines
    out = pd.Series()
    for i in range(len(df.columns) - 1):
        new_series = df.apply( lambda x: [(i, x[i]), (i + 1, x[i + 1])], axis = 1)
        out = out.append(new_series)
        
    lc = matplotlib.collections.LineCollection(out.values, colors = color, antialiaseds = aa)
    lc.set_label(label)
    ax.add_collection(lc)
        
    # have we already annotated these axes?
    if ax in ax_annotations:
        return
    
    ax_annotations[ax] = True
    
    x = np.arange(len(df.columns))
    for i in x:
        ax.axvline(i, **axvlines_kwds)
         
    ax.set_xticks(x)
    ax.set_xticklabels(df.columns)
    ax.set_xlim(x[0], x[-1])
    ax.grid()    
    
util.expand_class_attributes(ParallelCoordinatesView)
util.expand_method_parameters(ParallelCoordinatesView, ParallelCoordinatesView.plot)
