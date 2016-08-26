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

from traits.api import (HasStrictTraits, Str, CStr, List, Float, provides,
                        Instance, Bool, on_trait_change, DelegatesTo, Any,
                        Constant)

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import scale
import numpy as np

import cytoflow.utility as util
import cytoflow.views

from .i_operation import IOperation

@provides(IOperation)
class PolygonOp(HasStrictTraits):
    """Apply a polygon gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    xchannel : Str
        The name of the first channel to apply the range gate.
        
    ychannel : Str
        The name of the second channel to apply the range gate.
        
    vertices : List((Float, Float))
        The polygon verticies.  An ordered list of 2-tuples, representing
        the x and y coordinates of the vertices.
        
    Notes
    -----
    This module uses `matplotlib.path.Path` to represent the polygon, because
    membership testing is very fast.
    
    You can set the verticies by hand, I suppose, but it's much easier to use
    the interactive view you get from `default_view()` to do so.  Unfortunately, 
    it's currently very slow in the GUI and impossible to use in an IPython 
    notebook.
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.polygon')
    friendly_id = Constant("Polygon")
    
    name = CStr()
    xchannel = Str()
    ychannel = Str()
    vertices = List((Float, Float))
    
    _xscale = Str("linear")
    _yscale = Str("linear")
        
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.low and
            less than self.high; it is False otherwise.
            
        Raises
        ------
        util.CytoflowOpError
            if for some reason the operation can't be applied to this
            experiment. The reason is in util.CytoflowOpError.args
        """
        
        if not experiment:
            raise util.CytoflowOpError("No experiment specified")

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError("op.name is in the experiment already!")
        
        if not self.xchannel or not self.ychannel:
            raise util.CytoflowOpError("Must specify both an x channel and a y channel")
        
        if not self.xchannel in experiment.channels:
            raise util.CytoflowOpError("xchannel {0} is not in the experiment"
                                  .format(self.xchannel))
                                  
        if not self.ychannel in experiment.channels:
            raise util.CytoflowOpError("ychannel {0} is not in the experiment"
                                  .format(self.ychannel))
              
        if len(self.vertices) < 3:
            raise util.CytoflowOpError("Must have at least 3 vertices")
       
        if any([len(x) != 2 for x in self.vertices]):
            return util.CytoflowOpError("All vertices must be lists of length = 2") 
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError("You have to set the Polygon gate's name "
                               "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise util.CytoflowOpError("Experiment already contains a column {0}"
                               .format(self.name))
            
        # there's a bit of a subtlety here: if the vertices were 
        # selected with an interactive plot, and that plot had scaled
        # axes, we need to apply that scale function to both the
        # vertices and the data before looking for path membership
        xscale = scale.scale_factory(self._xscale, None)
        xscale.range = experiment.metadata[self.xchannel]['range']
        x_tf = xscale.get_transform()
        yscale = scale.scale_factory(self._yscale, None)
        yscale.range = experiment.metadata[self.ychannel]['range']
        y_tf = yscale.get_transform()
        
        vertices = [(x_tf.transform_non_affine(x), y_tf.transform_non_affine(y))
                    for (x, y) in self.vertices]
        data = experiment.data[[self.xchannel, self.ychannel]].copy()
        data[self.xchannel] = x_tf.transform_non_affine(data[self.xchannel])
        data[self.ychannel] = y_tf.transform_non_affine(data[self.ychannel])
            
        # use a matplotlib Path because testing for membership is a fast C fn.
        path = mpl.path.Path(np.array(vertices))
        xy_data = data.as_matrix(columns = [self.xchannel, self.ychannel])
        
        new_experiment = experiment.clone()        
        new_experiment.add_condition(self.name, 
                                     "bool", 
                                     path.contains_points(xy_data))
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
            
        return new_experiment
    
    def default_view(self, **kwargs):
        return PolygonSelection(op = self, **kwargs)
    
@provides(cytoflow.views.ISelectionView)
class PolygonSelection(cytoflow.views.ScatterplotView):
    """Plots, and lets the user interact with, a 2D polygon selection.
    
    Attributes
    ----------
    op : Instance(PolygonOp)
        The operation on which this selection view is operating
        
    huefacet : Str
        The conditioning variable to show multiple colors on this plot
        
    subset : Str
        The string for subsetting the plot

    interactive : Bool
        is this view interactive?  Ie, can the user set the polygon verticies
        with mouse clicks?
        
    Notes
    -----
    We inherit `xfacet` and `yfacet` from `cytoflow.views.ScatterPlotView`, but
    they must both be unset!
        
    Examples
    --------

    In an IPython notebook with `%matplotlib notebook`
    
    >>> s = flow.ScatterplotView(xchannel = "V2-A",
    ...                          ychannel = "Y2-A")
    >>> poly = s.default_view()
    >>> poly.plot(ex2)
    >>> poly.interactive = True
    """
    
    id = Constant('edu.mit.synbio.cytoflow.views.polygon')
    friendly_id = Constant("Polygon Selection")
    
    op = Instance(IOperation)
    name = DelegatesTo('op')
    xchannel = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    vertices = DelegatesTo('op')
    interactive = Bool(False, transient = True)

    # internal state.
    _ax = Any(transient = True)
    _widget = Instance(util.PolygonSelector, transient = True)
    _patch = Instance(mpl.patches.PathPatch, transient = True)
        
    def plot(self, experiment, **kwargs):
        """Plot self.view, and then plot the selection on top of it."""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if self.xfacet:
            raise util.CytoflowViewError("RangeSelection.xfacet must be empty or `Undefined`")
        
        if self.yfacet:
            raise util.CytoflowViewError("RangeSelection.yfacet must be empty or `Undefined`")
        
        super(PolygonSelection, self).plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_poly()
        self._interactive()
    
    @on_trait_change('vertices', post_init = True)
    def _draw_poly(self):
        if not self._ax:
            return
         
        if self._patch and self._patch in self._ax.patches:
            self._patch.remove()
            
        if not self.vertices or len(self.vertices) < 3:
            return
             
        patch_vert = np.concatenate((np.array(self.vertices), 
                                    np.array((0,0), ndmin = 2)))
                                    
        self._patch = \
            mpl.patches.PathPatch(mpl.path.Path(patch_vert, closed = True),
                                  edgecolor="black",
                                  linewidth = 2,
                                  fill = False)
            
        self._ax.add_patch(self._patch)
        plt.draw()
    
    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._widget = util.PolygonSelector(self._ax,
                                                self._onselect,
                                                useblit = True)
        elif self._widget:
            self._widget = None       
    
    def _onselect(self, vertices):
        self.vertices = vertices
    
        
        
if __name__ == '__main__':
    import cytoflow as flow
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])
    
    p = PolygonOp(xchannel = "V2-A",
                  ychannel = "Y2-A")
    v = p.default_view(xscale = "logicle", yscale = "logicle")
    
    plt.ioff()
    v.plot(ex)
    v.interactive = True
    plt.show()
