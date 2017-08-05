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

"""
Created on Apr 19, 2015

@author: brian
"""

from traits.api import provides

import matplotlib.pyplot as plt

from .i_view import IView
from .base_views import Base2DView

@provides(IView)
class ScatterplotView(Base2DView):
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
        
    huescale = Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the color bar, if there is one plotted

    subset = Str
        A string passed to pandas.DataFrame.query() to subset the data before
        we plot it.
        
    """
    
    id = 'edu.mit.synbio.cytoflow.view.scatterplot'
    friend__id = "Scatter Plot"
    
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted scatter plot view of a channel
        
        alpha : float
            The alpha blending value, between 0 (transparent) and 1 (opaque).
            Default = 0.25
            
        s : int
            The size in points^2.  Default = 2
            
        marker : a matplotlib marker style, usually a string
            Specfies the glyph to draw for each point on the scatterplot.
            See _matplotlib.markers for examples.  Default: 'o'
            
        .. _matplotlib.markers: http://matplotlib.org/api/markers_api.html#module-matplotlib.markers
        
        Other Parameters
        ----------------
        Other `kwargs` is passed to matplotlib.pyplot.scatter_.
    
        .. _matplotlib.pyplot.scatter: https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.scatter.html

        See Also
        --------
        BaseView.plot : common parameters for data views
        
        """
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):

        kwargs.setdefault('alpha', 0.25)
        kwargs.setdefault('s', 2)
        kwargs.setdefault('marker', 'o')
        kwargs.setdefault('antialiased', True)

        grid.map(plt.scatter, self.xchannel, self.ychannel, **kwargs)   
                
        return {}
        
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