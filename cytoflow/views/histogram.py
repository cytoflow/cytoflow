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

from __future__ import division, absolute_import

from traits.api import HasStrictTraits, Str, provides
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import seaborn as sns
import math
import bottleneck

import cytoflow.utility as util
from .i_view import IView

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
    
    name = Str(api = True)
    channel = Str(api = True)
    scale = util.ScaleEnum(api = True)
    xfacet = Str(api = True)
    yfacet = Str(api = True)
    huefacet = Str(api = True)
    subset = Str(api = True)
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.channel:
            raise util.CytoflowViewError("Must specify a channel")
        
        if self.channel not in experiment.data:
            raise util.CytoflowViewError("Channel {0} not in the experiment"
                                    .format(self.channel))
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} not in the experiment"
                                    .format(self.xfacet))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment"
                                    .format(self.yfacet))
        
        if self.huefacet and self.huefacet not in experiment.conditions:
            raise util.CytoflowViewError("Hue facet {0} not in the experiment"
                                    .format(self.huefacet))

        if self.subset:
            try:
                data = experiment.query(self.subset).data.reset_index()
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                
            if len(experiment.data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
        
        # get the scale
        scale = util.scale_factory(self.scale, experiment, self.channel)
        scaled_data = scale(data[self.channel])
        
        #print scaled_data
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)

        # estimate a "good" number of bins; see cytoflow.utility.num_hist_bins
        # for a reference.
        
        num_bins = util.num_hist_bins(scaled_data)
        
        # clip num_bins to (50, 1000)
        num_bins = max(min(num_bins, 1000), 50)
        
        xmin = bottleneck.nanmin(scaled_data)
        xmax = bottleneck.nanmax(scaled_data)
                    
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
            
        # take care of a rare rounding error, where the last observation is
        # a liiiitle bit more than the last bin, which makes plt.hist() puke
        bins[-1] += 1
                    
        kwargs.setdefault('bins', bins) 
        
        # mask out the data that's not in the scale domain
        data = data[~np.isnan(scaled_data)]

        g = sns.FacetGrid(data, 
                          size = 6,
                          aspect = 1.5,
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                          legend_out = False,
                          sharex = False,
                          sharey = False)
        
        # set the scale for each set of axes; can't just call plt.xscale() 
        for ax in g.axes.flatten():
            ax.set_xscale(self.scale, **scale.mpl_params)  
                  
        g.map(plt.hist, self.channel, **kwargs)
        
        # if we have a hue facet and a lot of hues, make a color bar instead
        # of a super-long legend.
        
        if self.huefacet:
            current_palette = mpl.rcParams['axes.color_cycle']
            if len(g.hue_names) > len(current_palette):
                plot_ax = plt.gca()
                cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
                                                                   n_colors = len(g.hue_names)))
                cax, _ = mpl.colorbar.make_axes(plt.gca())
                norm = mpl.colors.Normalize(vmin = np.min(g.hue_names), 
                                            vmax = np.max(g.hue_names), 
                                            clip = False)
                mpl.colorbar.ColorbarBase(cax, 
                                          cmap = cmap, 
                                          norm = norm, 
                                          label = self.huefacet)
                plt.sca(plot_ax)
            else:
                g.add_legend(title = self.huefacet)
