#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
cytoflow.views.scatterplot
--------------------------
"""

from traits.api import provides, Constant

import matplotlib.pyplot as plt

import cytoflow.utility as util

from .i_view import IView
from .base_views import Base2DView

@provides(IView)
class ScatterplotView(Base2DView):
    """
    Plots a 2-d scatterplot.  
    
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
        
    Plot a density plot
    
    .. plot::
        :context: close-figs
    
        >>> flow.ScatterplotView(xchannel = 'V2-A',
        ...                      xscale = 'log',
        ...                      ychannel = 'Y2-A',
        ...                      yscale = 'log',
        ...                      huefacet = 'Dox').plot(ex)
        
    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.scatterplot')
    friend_id = Constant("Scatter Plot")
    
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted scatter plot view of a channel
        
        Parameters
        ----------
        
        alpha : float (default = 0.25)
            The alpha blending value, between 0 (transparent) and 1 (opaque).
            
        s : int (default = 2)
            The size in points^2.
            
        marker : a matplotlib marker style, usually a string
            Specfies the glyph to draw for each point on the scatterplot.
            See `matplotlib.markers <http://matplotlib.org/api/markers_api.html#module-matplotlib.markers>`_ for examples.  Default: 'o'
            
        
        Notes
        -----
        Other ``kwargs`` are passed to `matplotlib.pyplot.scatter <https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.scatter.html>`_

        """
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, **kwargs):

        kwargs.setdefault('alpha', 0.25)
        kwargs.setdefault('s', 2)
        kwargs.setdefault('marker', 'o')
        kwargs.setdefault('antialiased', True)
        
        lim = kwargs.pop('lim')
        xlim = lim[self.xchannel]
        ylim = lim[self.ychannel]
        
        scale = kwargs.pop('scale')
        xscale = scale[self.xchannel]
        yscale = scale[self.ychannel]

        grid.map(plt.scatter, self.xchannel, self.ychannel, **kwargs)   
        
        return dict(xlim = xlim,
                    xscale = xscale,
                    ylim = ylim,
                    yscale = yscale)
    
    def _update_legend(self, legend):
        for lh in legend.legendHandles:
            lh.set_facecolor(lh.get_facecolor())  # i don't know why
            lh.set_edgecolor(lh.get_edgecolor())  # these are needed
            lh.set_alpha(0.5)
    
util.expand_class_attributes(ScatterplotView)
util.expand_method_parameters(ScatterplotView, ScatterplotView.plot)
        
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