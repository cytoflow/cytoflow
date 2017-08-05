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

from traits.api import provides
import matplotlib.pyplot as plt

import numpy as np
import statsmodels.nonparametric.api as smnp

from .i_view import IView
from .base_views import Base1DView

@provides(IView)
class Kde1DView(Base1DView):
    """Plots a one-channel kernel density estimate
    
    Attributes
    ----------
    name : Str
        The view's name (for serialization, UI etc.)
    
    channel : Str
        the name of the channel we're plotting
    
    xfacet : Str 
        the conditioning variable for multiple plots (horizontal)
    
    yfacet : Str
        the conditioning variable for multiple plots (vertical)
    
    huefacet : Str
        the conditioning variable for multiple plots (color)
        
    huescale = Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the color bar, if there is one plotted
        
    subset : Str
        a string passed to pandas.DataFrame.query() to subset the data before 
        we plot it.
                
    Examples
    --------
    >>> kde = flow.Kde1DView()
    >>> kde.name = "Kernel Density 1D"
    >>> kde.channel = 'Y2-A'
    >>> kde.xfacet = 'Dox'
    >>> kde.yfacet = 'Y2-A+'
    >>> kde.plot(ex)
    """
    
    # traits   
    _id = "edu.mit.synbio.cytoflow.view.kde1d"
    _friendly_id = "1D Kernel Density" 
    
    def plot(self, experiment, **kwargs):
        """
        Plot a smoothed histogram view of a channel
        
        Parameters
        ----------
        shade : bool
            If `True` (the default), shade the area under the plot.
            
        kernel : str
            The kernel to use for the kernel density estimate. Choices are:
                - "gau" for Gaussian (the default)
                - "biw" for biweight
                - "cos" for cosine
                - "epa" for Epanechnikov
                - "tri" for triangular
                - "triw" for triweight
                - "uni" for uniform
                
        bw : str or float
            The bandwidth for the kernel, controls how lumpy or smooth the
            kernel estimate is.  Choices are:
                "scott" (the default) - 1.059 * A * nobs ** (-1/5.), where A is min(std(X),IQR/1.34)
                "silverman" - .9 * A * nobs ** (-1/5.), where A is min(std(X),IQR/1.34)
                "normal_reference" - C * A * nobs ** (-1/5.), where C is calculated from the kernel. Equivalent (up to 2 dp) to the "scott" bandwidth for gaussian kernels. See bandwidths.py

            If a float is given, it is the bandwidth.
            
        gridsize : int
            How many times to compute the kernel?  (default: 100)


        See Also
        --------
        BaseView.plot : common parameters for data views
        
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