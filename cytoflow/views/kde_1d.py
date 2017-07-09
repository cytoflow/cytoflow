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
import matplotlib.pyplot as plt
import matplotlib as mpl

import numpy as np
import seaborn as sns
import statsmodels.nonparametric.api as smnp

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class Kde1DView(HasStrictTraits):
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
        
        .. note: Should this be a param instead?
        
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
    id = "edu.mit.synbio.cytoflow.view.kde1d"
    friendly_id = "1D Kernel Density" 
    
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
            except Exception as e:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset)) from e
                
            if len(data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data

        kwargs.setdefault('shade', True)
        kwargs['label'] = self.name
        
        # get the scale     
        kwargs['scale'] = scale = util.scale_factory(self.scale, experiment, channel = self.channel)

        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 1.0) 
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (scale.clip(data[self.channel].quantile(min_quantile)),
                    scale.clip(data[self.channel].quantile(max_quantile)))
        
        sharex = kwargs.pop('sharex', True)
        sharey = kwargs.pop('sharey', True)
        
        cols = col_wrap if col_wrap else \
               len(data[self.xfacet].unique()) if self.xfacet else 1
        
        g = sns.FacetGrid(data, 
                          size = (6 / cols),
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
                  
        g.map(_univariate_kdeplot, self.channel, **kwargs)
        
        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 0.999)
        
        def autoscale_x(*args, **kwargs):
            d = args[0]
            plt.gca().set_xlim(d.quantile(min_quantile),
                               d.quantile(max_quantile))
            
        g.map(autoscale_x, self.channel)
        
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
        
        if self.huefacet:
            current_palette = mpl.rcParams['axes.color_cycle']
            if util.is_numeric(experiment.data[self.huefacet]) and \
               len(g.hue_names) > len(current_palette):
                
                plot_ax = plt.gca()
                cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
                                                                   n_colors = len(g.hue_names)))
                cax, _ = mpl.colorbar.make_axes(plt.gca())
                hue_scale = util.scale_factory(self.huescale, 
                                               experiment, 
                                               condition = self.huefacet)
                mpl.colorbar.ColorbarBase(cax, 
                                          cmap = cmap, 
                                          norm = hue_scale.color_norm(),
                                          label = self.huefacet)
                plt.sca(plot_ax)
            else:
                g.add_legend(title = self.huefacet)

# yoinked from seaborn/distributions.py, with modifications for scaling.

def _univariate_kdeplot(data, scale=None, shade=False, kernel="gau",
        bw="scott", gridsize=100, cut=3, clip=None, legend=True,
        cumulative=False, shade_lowest=True, ax=None, **kwargs):
    
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