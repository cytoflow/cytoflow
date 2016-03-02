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

"""
Created on Apr 19, 2015

@author: brian
"""

from __future__ import division, absolute_import

import warnings

from traits.api import HasStrictTraits, provides, Str

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import matplotlib.transforms as mtrans

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class HexbinView(HasStrictTraits):
    """
    Plots a "hexbin" 2-d plot.  
    
    A hexbin is a 2-d histogram; the plot is divided into hexagons and the color
    of the hexagon is related to the number of points that fall into it.
    
    Attributes
    ----------
    
    name : Str
        The name of the plot, for visualization (and the plot title)
        
    xchannel : Str
        The channel to plot on the X axis
        
    ychannel : Str
        The channel to plot on the Y axis
        
    xfacet : Str
        The conditioning variable for multiple plots (horizontal)
        
    yfacet = Str
        The conditioning variable for multiple plots (vertical)
        
    huefacet = Str
        The conditioning variable for multiple plots (color)

    subset = Str
        A string passed to pandas.DataFrame.query() to subset the data before
        we plot it.
        
        .. note: should this be a param instead?
    """
    
    id = 'edu.mit.synbio.cytoflow.view.hexbin'
    friend_id = "Hex Bin"
    
    name = Str
    xchannel = Str
    ychannel = Str
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    xfacet = Str
    yfacet = Str
    huefacet = Str
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.xchannel:
            raise util.CytoflowViewError("X channel not specified")
        
        if self.xchannel not in experiment.data:
            raise util.CytoflowViewError("X channel {0} not in the experiment"
                                    .format(self.xchannel))
            
        if not self.ychannel:
            raise util.CytoflowViewError("Y channel not specified")
        
        if self.ychannel not in experiment.data:
            raise util.CytoflowViewError("Y channel {0} not in the experiment")
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} not in the experiment")
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment")
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise util.CytoflowViewError("Hue facet {0} not in the experiment")

        if self.subset:
            try: 
                data = experiment.query(self.subset)
            except:
                raise util.CytoflowViewError("Subset string \'{0}\' not valid")
                            
            if len(data.index) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
        
        #kwargs.setdefault('histtype', 'stepfilled')
        #kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('edgecolor', 'none')
        #kwargs.setdefault('mincnt', 1)
        #kwargs.setdefault('bins', 'log')
        kwargs.setdefault('antialiased', True)
            
        xmin, xmax = (np.amin(data[self.xchannel]), np.amax(data[self.xchannel]))
        ymin, ymax = (np.amin(data[self.ychannel]), np.amax(data[self.ychannel]))
        # to avoid issues with singular data, expand the min/max pairs
        xmin, xmax = mtrans.nonsingular(xmin, xmax, expander=0.1)
        ymin, ymax = mtrans.nonsingular(ymin, ymax, expander=0.1)
        
        extent = (xmin, xmax, ymin, ymax)
        kwargs.setdefault('extent', extent)
        
        xbins = util.num_hist_bins(experiment[self.xchannel])
        ybins = util.num_hist_bins(experiment[self.ychannel])
        bins = np.mean([xbins, ybins])
        
        kwargs.setdefault('bins', bins) # Do not move above.  don't ask.

        g = sns.FacetGrid(data,
                          size = 6,
                          aspect = 1.5, 
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                          sharex = False,
                          sharey = False)
        
        if(self.xscale != "linear" or self.yscale != "linear"):
            warnings.warn("hexbin is broken with scales other than \"linear\"",
                          util.CytoflowViewWarning)

        xscale = util.scale_factory(self.xscale, experiment, self.xchannel)
        yscale = util.scale_factory(self.yscale, experiment, self.ychannel)
        
        for ax in g.axes.flatten():
            ax.set_xscale(self.xscale, **xscale.mpl_params)
            ax.set_yscale(self.yscale, **yscale.mpl_params)
        
        g.map(plt.hexbin, self.xchannel, self.ychannel, **kwargs)
        
if __name__ == '__main__':
    import cytoflow as flow
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])
    
    hexbin = flow.HexbinView()
    hexbin.name = "Hex"
    hexbin.xchannel = "FSC-A"
    hexbin.ychannel = "SSC-A"
    hexbin.huefacet = 'Dox'

    plt.ioff()
    hexbin.plot(ex)
    plt.show()
