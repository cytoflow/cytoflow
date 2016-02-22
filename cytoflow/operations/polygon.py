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

import time

from traits.api import HasStrictTraits, Str, CStr, List, Float, provides, \
                       Instance, Bool, on_trait_change, DelegatesTo, Any, \
                       Constant

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib import scale
import numpy as np

from cytoflow.views.scatterplot import ScatterplotView
from cytoflow.operations import IOperation
from cytoflow.views import ISelectionView
from cytoflow.utility import CytoflowOpError, CytoflowViewError

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
        CytoflowOpError
            if for some reason the operation can't be applied to this
            experiment. The reason is in CytoflowOpError.args
        """
        
        if not experiment:
            raise CytoflowOpError("No experiment specified")

        if self.name in experiment.data.columns:
            raise CytoflowOpError("op.name is in the experiment already!")
        
        if not self.xchannel or not self.ychannel:
            raise CytoflowOpError("Must specify both an x channel and a y channel")
        
        if not self.xchannel in experiment.channels:
            raise CytoflowOpError("xchannel {0} is not in the experiment"
                                  .format(self.xchannel))
                                  
        if not self.ychannel in experiment.channels:
            raise CytoflowOpError("ychannel {0} is not in the experiment"
                                  .format(self.ychannel))
              
        if len(self.vertices) < 3:
            raise CytoflowOpError("Must have at least 3 vertices")
       
        if any([len(x) != 2 for x in self.vertices]):
            return CytoflowOpError("All vertices must be lists of length = 2") 
        
        # make sure name got set!
        if not self.name:
            raise CytoflowOpError("You have to set the Polygon gate's name "
                               "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise CytoflowOpError("Experiment already contains a column {0}"
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
        new_experiment.history.append(self.clone_traits())
            
        return new_experiment
    
    def default_view(self):
        return PolygonSelection(op = self)
    
@provides(ISelectionView)
class PolygonSelection(ScatterplotView):
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
    
    op = Instance(PolygonOp)
    name = DelegatesTo('op')
    xchannel = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    interactive = Bool(False, transient = True)

    # internal state.
    _ax = Any(transient = True)
    _cursor = Instance(Cursor, transient = True)
    _path = Instance(mpl.path.Path, transient = True)
    _patch = Instance(mpl.patches.PathPatch, transient = True)
    _line = Instance(mpl.lines.Line2D, transient = True)
    _drawing = Bool(transient = True)
    _last_draw_time = Float(0.0, transient = True)
    _last_click_time = Float(0.0, transient = True)
        
    def plot(self, experiment, **kwargs):
        """Plot self.view, and then plot the selection on top of it."""
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")
        
        if self.xfacet:
            raise CytoflowViewError("RangeSelection.xfacet must be empty or `Undefined`")
        
        if self.yfacet:
            raise CytoflowViewError("RangeSelection.yfacet must be empty or `Undefined`")
        
        super(PolygonSelection, self).plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_poly()
        self._interactive()
    
    @on_trait_change('op.vertices', post_init = True)
    def _draw_poly(self):
        if not self._ax:
            return
         
        if self._patch and self._patch in self._ax.patches:
            self._patch.remove()
            
        if self._drawing or not self.op.vertices or len(self.op.vertices) < 3 \
                         or any([len(x) != 2 for x in self.op.vertices]):
            return
             
        patch_vert = np.concatenate((np.array(self.op.vertices), 
                                    np.array((0,0), ndmin = 2)))
                                    
        self._patch = \
            mpl.patches.PathPatch(mpl.path.Path(patch_vert, closed = True),
                                  edgecolor="black",
                                  linewidth = 1.5,
                                  fill = False)
            
        self._ax.add_patch(self._patch)
        plt.draw_if_interactive()
    
    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._cursor = Cursor(self._ax, horizOn = False, vertOn = False)            
            self._cursor.connect_event('button_press_event', self._onclick)
            self._cursor.connect_event('motion_notify_event', self._onmove)
        elif self._cursor:
            self._cursor.disconnect_events()
            self._cursor = None       
    
    def _onclick(self, event): 
        """Update selection traits"""      
        if not self._ax:
            return
        
        if(self._cursor.ignore(event)):
            return
        
        # we have to check the wall clock time because the IPython notebook
        # doesn't seem to register double-clicks
        if event.dblclick or (time.clock() - self._last_click_time < 0.5):
            self._drawing = False
            self.op.vertices = map(tuple, self._path.vertices)
            self.op._xscale = plt.gca().get_xscale()
            self.op._yscale = plt.gca().get_yscale()
            self._path = None
            return
        
        self._last_click_time = time.clock()
                
        self._drawing = True
        if self._patch and self._patch in self._ax.patches:
            self._patch.remove()
            
        if self._path:
            vertices = np.concatenate((self._path.vertices,
                                      np.array((event.xdata, event.ydata), ndmin = 2)))
        else:
            vertices = np.array((event.xdata, event.ydata), ndmin = 2)

        self._path = mpl.path.Path(vertices, closed = False)
        self._patch = mpl.patches.PathPatch(self._path, 
                                            edgecolor = "black",
                                            fill = False)

        self._ax.add_patch(self._patch)
        plt.draw_if_interactive()
        
    def _onmove(self, event):       
         
        if not self._ax:
            return
         
        if(self._cursor.ignore(event) 
           or not self._drawing
           or not self._path
           or self._path.vertices.shape[0] == 0
           or not event.xdata
           or not event.ydata):
            return

        # only draw 5 times/sec
        if(time.clock() - self._last_draw_time < 0.2):
            return
        
        self._last_draw_time = time.clock()
         
        if self._line and self._line in self._ax.lines:
            self._line.remove()
            
        xdata = [self._path.vertices[-1, 0], event.xdata]
        ydata = [self._path.vertices[-1, 1], event.ydata]
        self._line = mpl.lines.Line2D(xdata, ydata, linewidth = 1, color = "black")
        
        self._ax.add_line(self._line)
        plt.gcf().canvas.draw()
        
        
if __name__ == '__main__':
    import cytoflow as flow
    import fcsparser

    tube1 = fcsparser.parse('../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                            reformat_meta = True, 
                            channel_naming = "$PnN")

    tube2 = fcsparser.parse('../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                            reformat_meta = True,
                            channel_naming = "$PnN")
    
    ex = flow.Experiment()
    ex.add_conditions({"Dox" : "float"})
    
    ex.add_tube(tube1, {"Dox" : 10.0})
    ex.add_tube(tube2, {"Dox" : 1.0})
    
    hlog = flow.HlogTransformOp()
    hlog.name = "Hlog transformation"
    hlog.channels = ['V2-A', 'Y2-A']
    ex2 = hlog.apply(ex)
    
    p = PolygonOp(xchannel = "V2-A",
                  ychannel = "Y2-A")
    v = p.default_view()
    
    plt.ioff()
    v.plot(ex2)
    v.interactive = True
    plt.show()
    print p.vertices
