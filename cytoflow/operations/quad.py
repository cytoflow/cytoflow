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

from traits.api import (HasStrictTraits, CFloat, Str, CStr, Bool, Instance,
                        provides, on_trait_change, DelegatesTo, Any, Constant)

from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import numpy as np
import pandas as pd

import cytoflow.utility as util
import cytoflow.views

from .i_operation import IOperation

@provides(IOperation)
class QuadOp(HasStrictTraits):
    """Apply a quadrant gate to a cytometry experiment.
    
    Creates a new metadata column named `name`, with values `name_1`,
    `name_2`, `name_3`, `name_4` ordered CLOCKWISE from upper-left.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    xchannel : Str
        The name of the first channel to apply the range gate.
        
    xthreshold : Float
        The threshold in the xchannel to gate with.

    ychannel : Str
        The name of the secon channel to apply the range gate.
        
    ythreshold : Float
        The threshold in ychannel to gate with.
        
    Examples
    --------
    
    >>> quad = flow.QuadOp(name = "Quad",
    ...                    xchannel = "V2-A",
    ...                    xthreshold = 0.5,
    ...                    ychannel = "Y2-A",
    ...                    ythreshold = 0.4)
    >>> ex3 = quad.apply(ex2)

    Alternately, in an IPython notebook with `%matplotlib notebook`
    
    >>> qv = quad.default_view()
    >>> qv.plot(ex2)
    >>> ### draw a box on the plot in the notebook ### 
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.quad')
    friendly_id = Constant("Quadrant Gate")
    
    name = CStr()
    
    xchannel = Str()
    xthreshold = CFloat()
    
    ychannel = Str()
    ythreshold = CFloat()

    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The new column is of type
            Enum, with values `name_1`, `name_2`, `name_3`, and `name_4`, 
            applied to events CLOCKWISE from upper-left.
            
            TODO - this is semantically weak sauce.  Add some (generalizable??)
            way to rename these populations?  It's an Enum; should be pretty
            easy.
            
        """
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise util.CytoflowOpError("Experiment already contains a column {0}"
                               .format(self.name))
        
        if not self.xchannel or not self.ychannel:
            raise util.CytoflowOpError("Must specify xchannel and ychannel")

        if not self.xchannel in experiment.channels:
            raise util.CytoflowOpError("xchannel isn't in the experiment")
        
        if not self.ychannel in experiment.channels:
            raise util.CytoflowOpError("ychannel isn't in the experiment")
        
        if not self.xthreshold:
            raise util.CytoflowOpError('xthreshold must be set!')
        
        if not self.ythreshold:
            raise util.CytoflowOpError('ythreshold must be set!')

        gate = pd.Series([None] * len(experiment))
        
        # perhaps there's some more pythonic way to do this?
        
        # these gate names match FACSDiva.  They are ARBITRARY.

        # lower-left
        ll = np.logical_and(experiment[self.xchannel] < self.xthreshold,
                            experiment[self.ychannel] < self.ythreshold)
        gate.loc[ll] = self.name + '_3'
        
        # upper-left
        ul = np.logical_and(experiment[self.xchannel] < self.xthreshold,
                            experiment[self.ychannel] > self.ythreshold)
        gate.loc[ul] = self.name + '_1'

        # upper-right
        ur = np.logical_and(experiment[self.xchannel] > self.xthreshold,
                            experiment[self.ychannel] > self.ythreshold)
        gate.loc[ur] = self.name + '_2'
        
        # lower-right
        lr = np.logical_and(experiment[self.xchannel] > self.xthreshold,
                            experiment[self.ychannel] < self.ythreshold)
        gate.loc[lr] = self.name + '_4'

        new_experiment = experiment.clone()
        new_experiment.add_condition(self.name, "category", gate)
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment
    
    def default_view(self, **kwargs):
        return QuadSelection(op = self, **kwargs)
    
@provides(cytoflow.views.ISelectionView)
class QuadSelection(cytoflow.views.ScatterplotView):
    """Plots, and lets the user interact with, a quadrant gate.
    
    Attributes
    ----------
    op : Instance(Range2DOp)
        The instance of Range2DOp that we're viewing / editing
        
    huefacet : Str
        The conditioning variable to plot multiple colors
        
    subset : Str
        The string passed to `Experiment.query()` to subset the data before
        plotting
        
    interactive : Bool
        is this view interactive?  Ie, can the user set the threshold with a 
        mouse click?
        
    Notes
    -----
    We inherit `xfacet` and `yfacet` from `cytoflow.views.ScatterplotView`, but
    they must both be unset!
        
    Examples
    --------
    
    In an IPython notebook with `%matplotlib notebook`
    
    >>> q = flow.QuadOp(name = "Quad",
    ...                 xchannel = "V2-A",
    ...                 ychannel = "Y2-A"))
    >>> qv = q.default_view()
    >>> qv.interactive = True
    >>> qv.plot(ex2) 
    """
    
    id = Constant('edu.mit.synbio.cytoflow.views.quad')
    friendly_id = Constant("Quadrant Selection")
    
    op = Instance(IOperation)
    name = DelegatesTo('op')
    xchannel = DelegatesTo('op')
    xthreshold = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    ythreshold = DelegatesTo('op')
    interactive = Bool(False, transient = True)
    
    # internal state.
    _ax = Any(transient = True)
    _hline = Instance(Line2D, transient = True)
    _vline = Instance(Line2D, transient = True)
    _cursor = Instance(Cursor, transient = True)
        
    def plot(self, experiment, **kwargs):
        """Plot the underlying scatterplot and then plot the selection on top of it."""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if self.xfacet:
            raise util.CytoflowViewError("RangeSelection.xfacet must be empty or `Undefined`")
        
        if self.yfacet:
            raise util.CytoflowViewError("RangeSelection.yfacet must be empty or `Undefined`")
        
        super(QuadSelection, self).plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_lines()
        self._interactive()

    @on_trait_change('xthreshold, ythreshold', post_init = True)
    def _draw_lines(self):
        if not self._ax:
            return
        
        if self._hline and self._hline in self._ax.lines:
            self._hline.remove()
            
        if self._vline and self._vline in self._ax.lines:
            self._vline.remove()
            
        if self.xthreshold and self.ythreshold:
            self._hline = plt.axhline(self.ythreshold, 
                                      linewidth = 3, 
                                      color = 'blue')
            self._vline = plt.axvline(self.xthreshold,
                                      linewidth = 3,
                                      color = 'blue')

            plt.draw()

    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._cursor = Cursor(self._ax,
                                  horizOn = True,
                                  vertOn = True,
                                  color = 'blue',
                                  useblit = True) 
            self._cursor.connect_event('button_press_event', self._onclick)
        elif self._cursor:
            self._cursor.disconnect_events()
            self._cursor = None
            
    def _onclick(self, event):
        """Update the threshold location"""
        self.xthreshold = event.xdata
        self.ythreshold = event.ydata    
    
if __name__ == '__main__':
    import cytoflow as flow
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])

    r = flow.QuadOp(name = "Quad",
                    xchannel = "V2-A",
                    ychannel = "Y2-A")
    rv = r.default_view(xscale = "logicle", yscale = "logicle")
    
    plt.ioff()
    rv.plot(ex)
    rv.interactive = True
    plt.show()
    print "x:{0}  y:{1}".format(r.xthreshold, r.ythreshold)
    ex2 = r.apply(ex)
    
    flow.ScatterplotView(xchannel = "V2-A",
                         ychannel = "Y2-A",
                         xscale = "logicle",
                         yscale = "logicle",
                         huefacet = "Quad").plot(ex2)
    plt.show()
