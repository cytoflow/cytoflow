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
cytoflow.views.histogram
------------------------
'''

from traits.api import Constant, provides
import matplotlib.pyplot as plt

import numpy as np
import math
import bottleneck

import cytoflow.utility as util
from .i_view import IView
from .base_views import Base1DView

@provides(IView)
class HistogramView(Base1DView):
    """
    Plots a one-channel histogram
    
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
    
        >>> flow.HistogramView(channel = 'Y2-A',
        ...                    scale = 'log',
        ...                    huefacet = 'Dox').plot(ex)
    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.histogram")
    friendly_id = Constant("Histogram") 
    
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted histogram view of a channel
        
        Parameters
        ----------
        num_bins : int
            The number of bins to plot in the histogram.  Clipped to [100, 1000]
            
        histtype : {'stepfilled', 'step', 'bar'}
            The type of histogram to draw.  `stepfilled` is the default, which
            is a line plot with a color filled under the curve.
            
        normed : bool
            If `True`, re-scale the histogram to form a probability density
            function, so the area under the histogram is 1.
            
        orientation : {'horizontal', 'vertical'}
            The orientation of the histogram.  `horizontal` gives a histogram
            with the intensity on the Y axis and the count on the X axis;
            default is `vertical`.
        
        linewidth : float
            The width of the histogram line (in points)
                    
        linestyle : ['-' | '--' | '-.' | ':' | "None"]
            The style of the line to plot
    
            
        Notes
        -----
        Other ``kwargs`` are passed to `matplotlib.pyplot.hist <https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.hist.html>`_

        
        """
        
        super().plot(experiment, **kwargs)

    def _grid_plot(self, experiment, grid, **kwargs):
                        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)

        # estimate a "good" number of bins; see cytoflow.utility.num_hist_bins
        # for a reference.
        scale = kwargs.pop('scale')[self.channel]
        lim = kwargs.pop('lim')[self.channel]
        
        scaled_data = scale(experiment[self.channel])
        num_bins = kwargs.pop('num_bins', util.num_hist_bins(scaled_data))
        num_bins = util.num_hist_bins(scaled_data) if num_bins is None else num_bins
        
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
            scaled_bins = scale(bins)
     
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

            bins = scale.inverse(new_bins)
        else:
            xmin = bottleneck.nanmin(scaled_data)
            xmax = bottleneck.nanmax(scaled_data)
            bins = scale.inverse(np.linspace(xmin, xmax, num=num_bins, endpoint = True))
                    
        kwargs.setdefault('bins', bins) 
        kwargs.setdefault('orientation', 'vertical')
        
        # if we have a hue facet, the y scaling is frequently wrong.  this
        # will capture the maximum bin count of each call to plt.hist, so 
        # we don't have to compute the histogram multiple times
        count_max = []
        
        def hist_lims(*args, **kwargs):
            # there's some bug in the above code where we get data that isn't
            # in the range of `bins`, which makes hist() puke.  so get rid
            # of it.
            
            bins = kwargs.get('bins')
            new_args = []
            for x in args:
                x = x[x > bins[0]]
                x = x[x < bins[-1]]
                new_args.append(x)
                
            n, _, _ = plt.hist(*new_args, **kwargs)
            count_max.append(max(n))
                    
        grid.map(hist_lims, self.channel, **kwargs)
        
        ret = {}
        if kwargs['orientation'] == 'vertical':
            ret['xscale'] = scale
            ret['xlim'] = lim
            ret['ylim'] = (0, 1.05 * max(count_max))
        else:
            ret['yscale'] = scale
            ret['ylim'] = lim
            ret['xlim'] = (0, 1.05 * max(count_max))
            
        return ret

util.expand_class_attributes(HistogramView)
util.expand_method_parameters(HistogramView, HistogramView.plot)