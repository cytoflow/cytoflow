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
cytoflow.views.kde_1d
---------------------
'''

from traits.api import provides, Constant
import matplotlib.pyplot as plt

import numpy as np
import statsmodels.nonparametric.api as smnp

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
            
        kernel : str
            The kernel to use for the kernel density estimate. Choices are:
                - ``gau`` for Gaussian (the default)
                - ``biw`` for biweight
                - ``cos`` for cosine
                - ``epa`` for Epanechnikov
                - ``tri`` for triangular
                - ``triw`` for triweight
                - ``uni`` for uniform
                
        bw : str or float
            The bandwidth for the kernel, controls how lumpy or smooth the
            kernel estimate is.  Choices are:
                - ``scott`` (the default) - ``1.059 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
                - ``silverman`` - ``.9 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
                - ``normal_reference`` - ``C * A * nobs ** (-1/5.)``, where ``C`` 
                    is calculated from the kernel. Equivalent (up to 2 dp) to 
                    the ``scott`` bandwidth for gaussian kernels. 
                    See ``bandwidths.py``
            If a float is given, it is the bandwidth.
            
        gridsize : int (default = 100)
            How many times to compute the kernel? 

        Notes
        -----
        Other ``kwargs`` are passed to `matplotlib.pyplot.plot <https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.plot.html>`_
  
        
        """
        
        super().plot(experiment, **kwargs)
                
    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):


        kwargs.setdefault('shade', True)
        
        # set the scale for each set of axes; can't just call plt.xscale() 
        for ax in grid.axes.flatten():
            ax.set_xscale(xscale.name, **xscale.mpl_params)  
                  
        grid.map(_univariate_kdeplot, self.channel, scale = xscale, **kwargs)
        
        return {}
        
        # i don't think is needed?
#         def autoscale_x(*args, **kwargs):
#             d = args[0]
#             plt.gca().set_xlim(d.quantile(min_quantile),
#                                d.quantile(max_quantile))
#             
#         g.map(autoscale_x, self.channel)

# yoinked from seaborn/distributions.py, with modifications for scaling.

def _univariate_kdeplot(data, scale=None, shade=False, kernel="gau",
        bw="scott", gridsize=100, cut=3, clip=None, legend=True,
        ax=None, **kwargs):
    
    if ax is None:
        ax = plt.gca()
        
    if clip is None:
        clip = (-np.inf, np.inf)

    scaled_data = scale(data)
    
    # mask out the data that's not in the scale domain
    scaled_data = scaled_data[~np.isnan(scaled_data)]  
    
    # Calculate the KDE
    fft = (kernel == "gau")
    kde = smnp.KDEUnivariate(scaled_data)
    kde.fit(kernel, bw, fft, gridsize=gridsize, cut=cut, clip=clip)

    x, y = scale.inverse(kde.support), kde.density

    # Make sure the density is nonnegative
    y = np.amax(np.c_[np.zeros_like(y), y], axis=1)

    # Check if a label was specified in the call
    label = kwargs.pop("label", None)

    color = kwargs.pop("color", None)

    # Draw the KDE plot and, optionally, shade
    ax.plot(x, y, color=color, label=label, **kwargs)
    alpha = kwargs.get("alpha", 0.25)
    if shade:
        ax.fill_between(x, 1e-12, y, facecolor=color, alpha=alpha)

    return ax

util.expand_class_attributes(Kde1DView)
util.expand_method_parameters(Kde1DView, Kde1DView.plot)