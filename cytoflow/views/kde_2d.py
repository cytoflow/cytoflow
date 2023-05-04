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
cytoflow.views.kde_2d
---------------------

A two-dimensional kernel density estimate -- kind of like a data "topo" map.

`Kde2DView` -- the `IView` class that makes the plot.
"""

from traits.api import provides, Constant

import matplotlib.pyplot as plt
import numpy as np
from sklearn.neighbors import KernelDensity
from statsmodels.nonparametric.bandwidths import bw_scott, bw_silverman

import cytoflow.utility as util

from .i_view import IView
from .view_kwargs import try_get_kwarg
from .base_views import Base2DView

@provides(IView)
class Kde2DView(Base2DView):
    """
    Plots a 2-d kernel-density estimate.  Sort of like a smoothed histogram.
    The density is visualized with a set of isolines.
        
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
    
        >>> flow.Kde2DView(xchannel = 'V2-A',
        ...                xscale = 'log',
        ...                ychannel = 'Y2-A',
        ...                yscale = 'log',
        ...                huefacet = 'Dox').plot(ex)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.kde2d')
    friend_id = Constant("2D Kernel Density Estimate")
    
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted 2d kernel density estimate
        
        Parameters
        ----------
        shade : bool
            Shade the interior of the isoplot?  (default = `False`)
            
        min_alpha, max_alpha : float
            The minimum and maximum alpha blending values of the isolines,
            between 0 (transparent) and 1 (opaque).
            
        n_levels : int
            How many isolines to draw? (default = 10)
                
        bw : str or float
            The bandwidth for the gaussian kernel, controls how lumpy or smooth the
            kernel estimate is.  Choices are:
            
                - ``scott`` (the default) - ``1.059 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
                - ``silverman`` - ``.9 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
                
            If a float is given, it is the bandwidth.   Note, this is in 
            scaled units, not data units.
            
        gridsize : int
            How many times to compute the kernel on each axis?  (default: 100)
        
        Notes
        -----
        Other ``kwargs`` are passed to `matplotlib.axes.Axes.contour <https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.contour.html>`_

        """
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, **kwargs):

        
        kwargs.setdefault('shade', False)
        kwargs.setdefault('min_alpha', 0.2)
        kwargs.setdefault('max_alpha', 0.9)
        kwargs.setdefault('n_levels', 10)
        
        lim = try_get_kwarg(kwargs,'lim')
        xlim = lim[self.xchannel]
        ylim = lim[self.ychannel]
        
        scale = try_get_kwarg(kwargs,'scale')
        xscale = scale[self.xchannel]
        yscale = scale[self.ychannel]

        legend_data = {}

        grid.map(_bivariate_kdeplot, 
                 self.xchannel, 
                 self.ychannel, 
                 xscale = xscale, 
                 yscale = yscale, 
                 legend_data = legend_data,
                 **kwargs)
                
        return dict(xlim = xlim,
                    xscale = xscale,
                    ylim = ylim,
                    yscale = yscale,
                    legend_data = legend_data)
        
    def _update_legend(self, legend):
        for lh in legend.legendHandles:
            lh.set_alpha(0.5)
        
# yoinked from seaborn/distributions.py, with modifications for scaling.
def _bivariate_kdeplot(x, y, xscale=None, yscale=None, shade=False,
                       bw="scott", gridsize=50, cut=3, clip=None, legend=True, 
                       legend_data = None, **kwargs):
    
    ax = plt.gca()
    label = try_get_kwarg(kwargs,'label', None)
    
    # Determine the clipping
    clip = [(-np.inf, np.inf), (-np.inf, np.inf)]
        
    x = xscale(x)
    y = yscale(y)

    x_nan = np.isnan(x)
    y_nan = np.isnan(y)
    
    x = x[~(x_nan | y_nan)]
    y = y[~(x_nan | y_nan)]
    
    if bw == 'scott':
        bw_x = bw_scott(x)
        bw_y = bw_scott(y)
        bw = (bw_x + bw_y) / 2
    elif bw == 'silverman':
        bw_x = bw_silverman(x)
        bw_y = bw_silverman(y)
        bw = (bw_x + bw_y) / 2
    elif isinstance(bw, float):
        bw_x = bw_y = bw
    else:
        raise util.CytoflowViewError(None,
                                     "Bandwith must be 'scott', 'silverman' or a float")

    kde = KernelDensity(bandwidth = bw, kernel = 'gaussian').fit(np.column_stack((x, y)))
    
    x_support = _kde_support(x, bw_x, gridsize, cut, clip[0])
    y_support = _kde_support(y, bw_y, gridsize, cut, clip[1])
    
    xx, yy = np.meshgrid(x_support, y_support)
    z = kde.score_samples(np.column_stack((xx.ravel(), yy.ravel())))
    z = z.reshape(xx.shape)
    z = np.exp(z)

    n_levels = try_get_kwarg(kwargs,"n_levels", 10)
    color = try_get_kwarg(kwargs,"color")
    kwargs['colors'] = (color, )
    
    min_alpha = try_get_kwarg(kwargs,"min_alpha", 0.2)
    if shade:
        min_alpha = 0
        
    max_alpha = try_get_kwarg(kwargs,"max_alpha", 0.9)
    
    x_support = xscale.inverse(x_support)
    y_support = yscale.inverse(y_support)
    xx, yy = np.meshgrid(x_support, y_support)    
    
    contour_func = ax.contourf if shade else ax.contour
    try:
        cset = contour_func(xx, yy, z, n_levels, **kwargs)
    except ValueError as e:
        raise util.CytoflowViewError(None,
                                     "Something went wrong in {}, bandwidth = {}.  "
                                     .format(contour_func.__name__, bw)) from e
    num_collections = len(cset.collections)
    
    alpha = np.linspace(min_alpha, max_alpha, num = num_collections)
    for el in range(num_collections):
        cset.collections[el].set_alpha(alpha[el])

    # Label the axes
    if hasattr(x, "name") and legend:
        ax.set_xlabel(x.name)
    if hasattr(y, "name") and legend:
        ax.set_ylabel(y.name)
        
    # Add legend data
    if label:
        legend_data[label] = plt.Rectangle((0, 0), 1, 1, fc = color)

    return ax        

def _kde_support(data, bw, gridsize, cut, clip):
    """Establish support for a kernel density estimate."""
    support_min = max(data.min() - bw * cut, clip[0])
    support_max = min(data.max() + bw * cut, clip[1])
    return np.linspace(support_min, support_max, gridsize)

util.expand_class_attributes(Kde2DView)
util.expand_method_parameters(Kde2DView, Kde2DView.plot)


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
    
