#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
cytoflow.views.kde_1d
---------------------
'''

from traits.api import provides, Constant
import matplotlib.pyplot as plt

import numpy as np
from sklearn.neighbors import KernelDensity
from statsmodels.nonparametric.bandwidths import bw_scott, bw_silverman

import cytoflow.utility as util

from .i_view import IView
from .base_views import Base1DView

@provides(IView)
class Kde1DView(Base1DView):
    """
    Plots a one-channel kernel density estimate, which is like a smoothed
    histogram.
    
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
        
    Plot a histogram
    
    .. plot::
        :context: close-figs
    
        >>> flow.Kde1DView(channel = 'Y2-A',
        ...                scale = 'log',
        ...                huefacet = 'Dox').plot(ex)
    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.kde1d")
    friendly_id = Constant("1D Kernel Density") 
    
    def plot(self, experiment, **kwargs):
        """
        Plot a smoothed histogram view of a channel
        
        Parameters
        ----------
        shade : bool
            If `True` (the default), shade the area under the plot.
            
        alpha : float, >=0 and <= 1
            The transparency of the shading.  1 is opaque, 0 is transparent.
            Default = 0.25
            
        kernel : str
            The kernel to use for the kernel density estimate. Choices are:
            
                - ``gaussian`` (the default)
                - ``tophat``
                - ``epanechnikov``
                - ``exponential``
                - ``linear``
                - ``cosine``
                
        bw : str or float
            The bandwidth for the kernel, controls how lumpy or smooth the
            kernel estimate is.  Choices are:
            
                - ``scott`` (the default) - ``1.059 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
                - ``silverman`` - ``.9 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
                
            If a float is given, it is the bandwidth.   Note, this is in 
            scaled units, not data units.
            
        gridsize : int (default = 100)
            How many times to compute the kernel? 

        Notes
        -----
        Other ``kwargs`` are passed to `matplotlib.pyplot.plot <https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.plot.html>`_
  
        
        """
        
        super().plot(experiment, **kwargs)
                
    def _grid_plot(self, experiment, grid, **kwargs):

        kwargs.setdefault('shade', True)
        kwargs.setdefault('orientation', "vertical")
        
        scale = kwargs.pop('scale')[self.channel]
        lim = kwargs.pop('lim')[self.channel]
                  
        grid.map(_univariate_kdeplot, self.channel, scale = scale, **kwargs)
        
        ret = {}
        if kwargs['orientation'] == 'vertical':
            ret['xscale'] = scale
            ret['xlim'] = lim
        else:
            ret['yscale'] = scale
            ret['ylim'] = lim
            
        return ret


# yoinked from seaborn/distributions.py, with modifications for scaling.

def _univariate_kdeplot(data, scale=None, shade=False, kernel="gaussian",
        bw="scott", gridsize=100, cut=3, clip=None, legend=True,
        ax=None, orientation = "vertical", **kwargs):
    
    if ax is None:
        ax = plt.gca()
        
    if clip is None:
        clip = (-np.inf, np.inf)

    scaled_data = scale(data)
    
    # mask out the data that's not in the scale domain
    scaled_data = scaled_data[~np.isnan(scaled_data)]  
    
    if kernel not in ['gaussian','tophat','epanechnikov','exponential','linear','cosine']:
        raise util.CytoflowOpError(None,
                                   "kernel must be one of ['gaussian'|'tophat'|'epanechnikov'|'exponential'|'linear'|'cosine']")
    
    if bw == 'scott':
        bw = bw_scott(scaled_data)
    elif bw == 'silverman':
        bw = bw_silverman(scaled_data)
    elif not isinstance(bw, float):
        raise util.CytoflowViewError(None,
                                     "Bandwith must be 'scott', 'silverman' or a float")
    
    support = _kde_support(scaled_data, bw, gridsize, cut, clip)[:, np.newaxis]

    kde = KernelDensity(kernel = kernel, bandwidth = bw).fit(scaled_data.to_numpy()[:, np.newaxis])
    log_density = kde.score_samples(support)

    x = scale.inverse(support[:, 0])
    y = np.exp(log_density)

    # Check if a label was specified in the call
    label = kwargs.pop("label", None)
    color = kwargs.pop("color", None)
    alpha = kwargs.pop("alpha", 0.25)

    # Draw the KDE plot and, optionally, shade
    if orientation == "vertical":
        ax.plot(x, y, color=color, label=label, **kwargs)
        if shade:
            ax.fill_between(x, 1e-12, y, facecolor=color, alpha=alpha)
    else:
        ax.plot(y, x, color=color, label=label, **kwargs)
        if shade:
            ax.fill_between(y, 1e-12, x, facecolor=color, alpha=alpha)

    return ax

def _kde_support(data, bw, gridsize, cut, clip):
    """Establish support for a kernel density estimate."""
    support_min = max(data.min() - bw * cut, clip[0])
    support_max = min(data.max() + bw * cut, clip[1])
    return np.linspace(support_min, support_max, gridsize)

util.expand_class_attributes(Kde1DView)
util.expand_method_parameters(Kde1DView, Kde1DView.plot)