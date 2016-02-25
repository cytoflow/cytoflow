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

from __future__ import division

from traits.api import HasStrictTraits, Str, Enum, provides
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns
import math

from cytoflow.views import IView
from cytoflow.utility import num_hist_bins, scale_factory, ScaleEnum, CytoflowViewError

@provides(IView)
class HistogramView(HasStrictTraits):
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
        
    subset : Str
        a string passed to pandas.DataFrame.query() to subset the data before 
        we plot it.
        
        .. note: Should this be a param instead?
        
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
    scale = ScaleEnum
    xfacet = Str
    yfacet = Str
    huefacet = Str
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")
        
        if self.channel not in experiment.data:
            raise CytoflowViewError("Channel {0} not in the experiment"
                                    .format(self.channel))
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise CytoflowViewError("X facet {0} not in the experiment"
                                    .format(self.xfacet))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise CytoflowViewError("Y facet {0} not in the experiment"
                                    .format(self.yfacet))
        
        if self.huefacet and self.huefacet not in experiment.conditions:
            raise CytoflowViewError("Hue facet {0} not in the experiment"
                                    .format(self.huefacet))

        if self.subset:
            try:
                data = experiment.query(self.subset)
            except:
                raise CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                
            if len(data.index) == 0:
                raise CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data        
            
        # get the scale
        scale = scale_factory(self.scale, experiment, self.channel)
        scaled_data = scale(data[self.channel])
        
        # drop data that isn't in the scale function's domain
        data = data[~np.isnan(scaled_data)]
        scaled_data = scaled_data[~np.isnan(scaled_data)]
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)

        # estimate a "good" number of bins; see cytoflow.utility.num_hist_bins
        # for a reference.
        
        num_bins = num_hist_bins(scaled_data)
        num_bins = 50 if num_bins < 50 else num_bins
        xmin = scaled_data.min()
        xmax = scaled_data.max()
                    
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
            bins = np.append(bins, xmax)
            
            num_hues = len(data[self.huefacet].unique())
            bins_per_hue = math.ceil(num_bins / num_hues)
            
            new_bins = [xmin]
            for end in [b for b in bins if (b > xmin and b <= xmax)]:
                new_bins = np.append(new_bins,
                                     np.linspace(new_bins[-1],
                                                 end,
                                                 bins_per_hue + 1,
                                                 endpoint = True)[1:])

            bins = scale.inverse(new_bins)
        else:
            bin_width = (xmax - xmin) / num_bins
            bins = scale.inverse(np.arange(xmin, xmax, bin_width))
            bins = np.append(bins, scale.inverse(xmax))
        
        kwargs.setdefault('bins', bins) 

        g = sns.FacetGrid(data, 
                          size = 6,
                          aspect = 1.5,
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                          legend_out = False)
        
        # TODO - something odd with the scaling here??
        
        plt.xscale(self.scale, **scale.mpl_params)        
        g.map(plt.hist, self.channel, **kwargs)
        g.add_legend()

    
if __name__ == '__main__':
   
    plt.ioff()
    p = plt.figure(1)

    tips = sns.load_dataset("tips")
    g = sns.FacetGrid(tips, col="time", fig_kws={"num" : 1})
    
    plt.show()