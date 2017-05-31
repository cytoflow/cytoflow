#!/usr/bin/env python2.7
# coding: latin-1

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

"""
Created on Apr 19, 2015

@author: brian
"""

from traits.api import HasStrictTraits, provides, Str

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.interpolate import griddata

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class DensityView(HasStrictTraits):
    """
    Plots a 2-d density plot.  
    
    Attributes
    ----------
    
    name : Str
        The name of the plot, for visualization (and the plot title)
        
    xchannel : Str
        The channel to plot on the X axis
        
    xscale : Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the X axis
        
    ychannel : Str
        The channel to plot on the Y axis
        
    yscale : Enum("linear", "log", "logicle") (default = "linear")
        The scale to use on the Y axis
        
    xfacet : Str
        The conditioning variable for multiple plots (horizontal)
        
    yfacet = Str
        The conditioning variable for multiple plots (vertical)
        
    huescale = Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the color bar, if there is one plotted

    subset = Str
        A string passed to pandas.DataFrame.query() to subset the data before
        we plot it.
        
        .. note: should this be a param instead?
    """
    
    id = 'edu.mit.synbio.cytoflow.view.scatterplot'
    friend_id = "Scatter Plot"
    
    name = Str
    xchannel = Str
    xscale = util.ScaleEnum
    ychannel = Str
    yscale = util.ScaleEnum
    xfacet = Str
    yfacet = Str
    huescale = util.ScaleEnum
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted scatter plot view of a channel"""
        
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")

        if not self.xchannel:
            raise util.CytoflowViewError("X channel not specified")
        
        if self.xchannel not in experiment.data:
            raise util.CytoflowViewError("X channel {0} not in the experiment"
                                    .format(self.xchannel))
            
        if not self.ychannel:
            raise util.CytoflowViewError("Y channel not specified")
        
        if self.ychannel not in experiment.data:
            raise util.CytoflowViewError("Y channel {0} not in the experiment"
                                         .format(self.ychannel))
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} not in the experiment"
                                         .format(self.xfacet))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment"
                                         .format(self.yfacet))
            
        facets = filter(lambda x: x, [self.xfacet, self.yfacet])
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
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                            
            if len(data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data

#         legend = kwargs.pop('legend', True)
        
        kwargs.setdefault('antialiased', True)
        kwargs.setdefault('linewidth', 1)
        kwargs.setdefault('edgecolor', 'face')

        xscale = kwargs.get('xscale', None)
        if xscale is None:
            xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)
            kwargs['xscale'] = xscale
        
        yscale = kwargs.get('yscale', None)
        if yscale is None:
            yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
            kwargs['yscale'] = yscale

        # adjust the limits to clip extreme values
        min_quantile = kwargs.pop("min_quantile", 0.001)
        max_quantile = kwargs.pop("max_quantile", 1.0) 
                
        xlim = kwargs.pop("xlim", None)
        if xlim is None:
            xlim = (xscale.clip(data[self.xchannel].quantile(min_quantile)),
                    xscale.clip(data[self.xchannel].quantile(max_quantile)))
                      
        ylim = kwargs.pop("ylim", None)
        if ylim is None:
            ylim = (yscale.clip(data[self.ychannel].quantile(min_quantile)),
                    yscale.clip(data[self.ychannel].quantile(max_quantile)))
            
        gridsize = kwargs.pop('gridsize', 50)
        xbins = xscale.inverse(np.linspace(xscale(xlim[0]), xscale(xlim[1]), gridsize))
        ybins = yscale.inverse(np.linspace(yscale(ylim[0]), yscale(ylim[1]), gridsize))
            
        sharex = kwargs.pop('sharex', True)
        sharey = kwargs.pop('sharey', True)
            
        cols = col_wrap if col_wrap else \
               len(data[self.xfacet].unique()) if self.xfacet else 1
            
        g = sns.FacetGrid(data, 
                          size = (6 / cols),
                          aspect = 1.5,
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          col_wrap = col_wrap,
                          legend_out = False,
                          sharex = sharex,
                          sharey = sharey,
                          xlim = xlim,
                          ylim = ylim)
        
        for ax in g.axes.flatten():
            ax.set_xscale(self.xscale, **xscale.mpl_params)
            ax.set_yscale(self.yscale, **yscale.mpl_params)

        g.map(_densityplot, self.xchannel, self.ychannel, xbins = xbins, ybins = ybins, **kwargs)
        
        # if we're sharing y axes, make sure the y scale is the same for each
        if sharey:
            fig = plt.gcf()
            fig_y_min = float("inf")
            fig_y_max = float("-inf")
            for ax in fig.get_axes():
                ax_y_min, ax_y_max = ax.get_ylim()
                if ax_y_min < fig_y_min:
                    fig_y_min = ax_y_min
                if ax_y_max > fig_y_max:
                    fig_y_max = ax_y_max
                    
            for ax in fig.get_axes():
                ax.set_ylim(fig_y_min, fig_y_max)
            
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
        
#         if legend and self.huefacet:
#             current_palette = mpl.rcParams['axes.color_cycle']
#             if util.is_numeric(experiment.data[self.huefacet]) and \
#                len(g.hue_names) > len(current_palette):
#                 
#                 plot_ax = plt.gca()
#                 cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
#                                                                    n_colors = len(g.hue_names)))
#                 cax, _ = mpl.colorbar.make_axes(plt.gca())
#                 hue_scale = util.scale_factory(self.huescale, 
#                                                experiment, 
#                                                condition = self.huefacet)
#                 mpl.colorbar.ColorbarBase(cax, 
#                                           cmap = cmap, 
#                                           norm = hue_scale.color_norm(),
#                                           label = self.huefacet)
#                 plt.sca(plot_ax)
#             else:
#                 g.add_legend(title = self.huefacet)
#                 
        return g
        
        
def _densityplot(x, y, xbins, ybins, **kwargs):
    
    h, X, Y = np.histogram2d(x, y, bins=[xbins, ybins])
    
    smoothed = kwargs.pop('smoothed', False)
    xscale = kwargs.pop('xscale')
    yscale = kwargs.pop('yscale')
    
    if smoothed:
        grid_x, grid_y = np.mgrid[xscale(X[0]):xscale(X[-1]):complex(5 * len(xbins)), 
                                  yscale(Y[0]):yscale(Y[-1]):complex(5 * len(ybins))]
        
        loc = [(x, y) for x in xscale(X[1:]) for y in yscale(Y[1:])]
         
        h = griddata(loc, h.flatten(), (grid_x, grid_y), method = "linear", fill_value = 0)
         
        X, Y = xscale.inverse(grid_x), yscale.inverse(grid_y)
    else:
        h = h.T

    ax = plt.gca()
    ax.pcolormesh(X, Y, h, **kwargs)
         
         
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