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

from traits.api import HasStrictTraits, provides, Str

import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import numpy as np

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class ScatterplotView(HasStrictTraits):
    """
    Plots a 2-d scatterplot.  
    
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
        
    huefacet = Str
        The conditioning variable for multiple plots (color)

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
    huefacet = Str
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted scatter plot view of a channel"""
        
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
            raise util.CytoflowViewError("Y channel {0} not in the experiment"
                                         .format(self.ychannel))
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} not in the experiment"
                                         .format(self.xfacet))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment"
                                         .format(self.yfacet))
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise util.CytoflowViewError("Hue facet {0} not in the experiment"
                                         .format(self.huefacet))
        
        if self.subset:
            try:
                data = experiment.query(self.subset)
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                            
            if len(data.index) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
        
        kwargs.setdefault('alpha', 0.25)
        kwargs.setdefault('s', 2)
        kwargs.setdefault('marker', 'o')
        kwargs.setdefault('antialiased', True)

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
        
        xscale = util.scale_factory(self.xscale, experiment, self.xchannel)
        yscale = util.scale_factory(self.yscale, experiment, self.ychannel)
        
        for ax in g.axes.flatten():
            ax.set_xscale(self.xscale, **xscale.mpl_params)
            ax.set_yscale(self.yscale, **yscale.mpl_params)

        g.map(plt.scatter, self.xchannel, self.ychannel, **kwargs)
        g.add_legend()
        
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