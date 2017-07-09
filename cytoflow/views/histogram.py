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

from traits.api import HasStrictTraits, Str, provides
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns
import math
import bottleneck

from warnings import warn

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
        """Plot a faceted histogram view of a channel"""
        
        if experiment is None:
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
            
        facets = [x for x in [self.xfacet, self.yfacet, self.huefacet] if x]
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError("Can't reuse facets")
            
        col_wrap = kwargs.pop('col_wrap', None)
        
        if col_wrap and self.yfacet:
            raise util.CytoflowViewError("Can't set yfacet and col_wrap at the same time.")
        
        if col_wrap and not self.xfacet:
            raise util.CytoflowViewError("Must set xfacet to use col_wrap.")

        if self.subset:
            try:
                data = experiment.query(self.subset).data.reset_index()
            except util.CytoflowError as e:
                raise util.CytoflowViewError(str(e)) from e
            except Exception as e:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset)) from e
                
            if len(data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
        
        # get the scale
        scale = kwargs.pop('scale', None)
        if scale is None:
            scale = util.scale_factory(self.scale, experiment, channel = self.channel)

        scaled_data = scale(data[self.channel])
                
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)

        # estimate a "good" number of bins; see cytoflow.utility.num_hist_bins
        # for a reference.
        
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
            scaled_bins = scale(bins)
     
            num_hues = len(data[self.huefacet].unique())
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
            bin_width = (xmax - xmin) / num_bins
            bins = scale.inverse(np.arange(xmin, xmax, bin_width))
            bins = np.append(bins, scale.inverse(xmax))
            
        # take care of a rare rounding error, where the first observation is
        # less than the first bin or the last observation is more than the last 
        # bin, which makes plt.hist() puke
        bins[-1] += 1
        bins[0] -= 1
                    
        kwargs.setdefault('bins', bins) 

        # mask out the data that's not in the scale domain
        data = data[~np.isnan(scaled_data)]
        
        # mask out data that doesn't fall in the range of the bins
        if data[self.channel].min() < bins[0] or data[self.channel].max() > bins[-1]:
            warn("Masking out data that doesn't fall in the specified bins",
                 util.CytoflowViewWarning)
            data = data[data[self.channel] > bins[0]]
            data = data[data[self.channel] < bins[-1]]

        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 1.0) 
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (data[self.channel].quantile(min_quantile),
                    data[self.channel].quantile(max_quantile))
            
        sharex = kwargs.pop("sharex", True)
        sharey = kwargs.pop("sharey", True)
        
        cols = col_wrap if col_wrap else \
               len(data[self.xfacet].unique()) if self.xfacet else 1
            
        g = sns.FacetGrid(data, 
                          size = 6 / cols,
                          aspect = 1.5,
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                          col_wrap = col_wrap,
                          legend_out = False,
                          sharex = sharex,
                          sharey = sharey,
                          xlim = xlim)
        
        # set the scale for each set of axes; can't just call plt.xscale() 
        for ax in g.axes.flatten():
            ax.set_xscale(self.scale, **scale.mpl_params)  
                  
        legend = kwargs.pop('legend', True)
        
        # if we have a hue facet, the y scaling is frequently wrong.  this
        # will capture the maximum bin count of each call to plt.hist, so 
        # we don't have to compute the histogram multiple times
        ymax = []
        
        def hist_lims(*args, **kwargs):
            n, _, _ = plt.hist(*args, **kwargs)
            ymax.append(max(n))
        
        g.map(hist_lims, self.channel, **kwargs)
        
        plt.ylim(0, 1.05 * max(ymax))
        
        # if we are sharing y axes, make sure the y scale is the same for each
        if sharey:
            fig = plt.gcf()
            fig_y_max = float("-inf")
            
            for ax in fig.get_axes():
                _, ax_y_max = ax.get_ylim()
                if ax_y_max > fig_y_max:
                    fig_y_max = ax_y_max
                    
            for ax in fig.get_axes():
                ax.set_ylim(None, fig_y_max)
            
        # if we are sharing x axes, make sure the x scale is the same for each
        if sharex:
            fig = plt.gcf()
            fig_x_min = float("inf")
            fig_x_max = float("-inf")
            
            for ax in fig.get_axes():
                ax_x_min, ax_x_max = ax.get_xlim()
                if ax_x_min < fig_x_min:
                    fig_x_min = ax_x_min
                if ax_x_max > fig_x_max:
                    fig_x_max = ax_x_max
                    
            for ax in fig.get_axes():
                ax.set_xlim(fig_x_min, fig_x_max)
        
        # if we have a hue facet and a lot of hues, make a color bar instead
        # of a super-long legend.
        
        if self.huefacet and legend:
            current_palette = mpl.rcParams['axes.color_cycle']
        
            if util.is_numeric(experiment.data[self.huefacet]) and \
               len(g.hue_names) > len(current_palette):
                
                hue_scale = util.scale_factory(self.huescale, 
                                               experiment, 
                                               condition = self.huefacet)
                
                plot_ax = plt.gca()
                cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
                                                                   n_colors = len(g.hue_names)))
                cax, _ = mpl.colorbar.make_axes(plt.gca())

                mpl.colorbar.ColorbarBase(cax, 
                                          cmap = cmap, 
                                          norm = hue_scale.color_norm(), 
                                          label = self.huefacet)
                plt.sca(plot_ax)
            else:
                g.add_legend(title = self.huefacet)
                
        return g
