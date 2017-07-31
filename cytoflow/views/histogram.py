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

from traits.api import Str, provides
import matplotlib.pyplot as plt

import numpy as np
import math
import bottleneck

import cytoflow.utility as util
from .i_view import IView
from .base_views import Base1DView

@provides(IView)
class HistogramView(Base1DView):
    """Plots a one-channel histogram
    
    Attributes
    ----------
    name : Str
        The HistogramView name (for serialization, UI etc.)
    
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
        
        .. note: Should this be a param instead?
        
    Examples
    --------
    >>> hist = flow.HistogramView()
    >>> hist.name = "Histogram view, grid"
    >>> hist.channel = 'Y2-A'
    >>> hist.xfacet = 'Dox'
    >>> hist.yfacet = 'Y2-A+'
    >>> hist.plot(ex)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.histogram"
    friendly_id = "Histogram" 
    
    name = Str
    channel = Str
    scale = util.ScaleEnum
    xfacet = Str
    yfacet = Str
    huefacet = Str
    huescale = util.ScaleEnum
    subset = Str
    
    
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted histogram view of a channel
        
        Parameters
        ----------
        bins : int
            The number of bins to plot in the histogram
            
        histtype : {'stepfilled', 'step', 'bar'}
            The type of histogram to draw.  `stepfilled` is the default, which
            is a line plot with a color filled under the curve.
            
        normed : bool
            If `True`, re-scale the histogram to form a probability density
            function, so the area under the histogram is 1.
            
        Other Parameters
        ----------------
        Other `kwargs` are passed to matplotlib.pyplot.hist_.
    
        .. _matplotlib.pyplot.hist: https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.hist.html

        See Also
        --------
        BaseView.plot : common parameters for data views
        
        """
        
        super().plot(experiment, **kwargs)

    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):
                        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)

        # estimate a "good" number of bins; see cytoflow.utility.num_hist_bins
        # for a reference.
        
        scaled_data = xscale(experiment[self.channel])
        num_bins = util.num_hist_bins(scaled_data)
        
        # clip num_bins to (100, 1000)
        num_bins = max(min(num_bins, 1000), 100)
        
        if (self.huefacet 
            and "bins" in experiment.metadata[self.huefacet]
            and experiment.metadata[self.huefacet]["bin_scale"] == self.scale):
            
            # if we color facet by the result of a BinningOp and we don't
            # match the BinningOp bins with the histogram bins, we get
            # gnarly aliasing.
            
            # each color gets at least one bin.  however, if the estimated
            # number of bins for the histogram is much larger than the
            # number of colors, sub-divide each color into multiple bins.
            bins = experiment.metadata[self.huefacet]["bins"]
            scaled_bins = xscale(bins)
     
            num_hues = len(experiment[self.huefacet].unique())
            bins_per_hue = math.floor(num_bins / num_hues)

            if bins_per_hue == 1:
                new_bins = scaled_bins
            else:
                new_bins = []
                for idx in range(1, len(scaled_bins)):
                    new_bins = np.append(new_bins, 
                                         np.linspace(scaled_bins[idx - 1],
                                                     scaled_bins[idx],
                                                     bins_per_hue + 1,
                                                     endpoint = False))

            bins = xscale.inverse(new_bins)
        else:
            xmin = bottleneck.nanmin(scaled_data)
            xmax = bottleneck.nanmax(scaled_data)
            bins = xscale.inverse(np.linspace(xmin, xmax, num=num_bins, endpoint = True))
            
        # take care of a rare rounding error, where the first observation is
        # less than the first bin or the last observation is more than the last 
        # bin, which makes plt.hist() puke
        bins[-1] += 1
        bins[0] -= 1
                    
        kwargs.setdefault('bins', bins) 
        
        # if we have a hue facet, the y scaling is frequently wrong.  this
        # will capture the maximum bin count of each call to plt.hist, so 
        # we don't have to compute the histogram multiple times
        ymax = []
        
        def hist_lims(*args, **kwargs):
            n, _, _ = plt.hist(*args, **kwargs)
            ymax.append(max(n))
        
        grid.map(hist_lims, self.channel, **kwargs)
        
        plt.ylim(0, 1.05 * max(ymax))
        
        return {}
