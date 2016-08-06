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

from __future__ import absolute_import, division

from traits.api import (HasStrictTraits, CFloat, Str, CStr, Instance, 
                        Bool, on_trait_change, provides, DelegatesTo, Any, 
                        Constant)
    
import pandas as pd

from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import cytoflow.utility as util
import cytoflow.views

from .i_operation import IOperation

@provides(IOperation)
class ThresholdOp(HasStrictTraits):
    """Apply a threshold to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    channel : Str
        The name of the channel to apply the threshold on.
        
    threshold : Float
        The value at which to threshold this channel.
        
    Examples
    --------
    >>> thresh = flow.ThresholdOp()
    >>> thresh.name = "Y2-A+"
    >>> thresh.channel = 'Y2-A'
    >>> thresh.threshold = 0.3
    >>> 
    >>> ex3 = thresh.apply(ex2)    
    
    Alternately, in an IPython notebook with `%matplotlib notebook`
    
    >>> h = flow.HistogramView()
    >>> h.channel = 'Y2-A'
    >>> h.huefacet = 'Dox'
    >>> ts = flow.ThresholdSelection(view = h)
    >>> ts.plot(ex2)
    >>> ts.interactive = True
    >>> # .... draw a threshold on the plot
    >>> thresh = flow.ThresholdOp(name = "Y2-A+",
    ...                           channel = "Y2-A",
    ...                           thresh.threshold = ts.threshold)
    >>> ex3 = thresh.apply(ex2)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.threshold')
    friendly_id = Constant("Threshold")
    
    name = CStr(api = True)
    channel = Str(api = True)
    threshold = CFloat(api = True)
        
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        old_experiment : Experiment
            the experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.threshold;
            it is False otherwise.
        """
        
        if not experiment:
            raise util.CytoflowOpError("No experiment specified")
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise util.CytoflowOpError("Experiment already contains a column {0}"
                               .format(self.name))

        if self.channel not in experiment.channels:
            raise util.CytoflowOpError("{0} isn't a channel in the experiment"
                                  .format(self.channel))

        gate = pd.Series(experiment[self.channel] > self.threshold)

        new_experiment = experiment.clone()
        new_experiment.add_condition(self.name, "bool", gate)
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment
    
    def default_view(self, **kwargs):
        return ThresholdSelection(op = self, **kwargs)


@provides(cytoflow.views.ISelectionView)
class ThresholdSelection(cytoflow.views.HistogramView):
    """
    Plots, and lets the user interact with, a threshold on the X axis.
    
    TODO - beautify!
    
    Attributes
    ----------
    op : Instance(ThresholdOp)
        the ThresholdOp we're working on.
        
    huefacet : Str
        The conditioning variable to show multiple colors on this plot

    subset : Str    
        the string passed to Experiment.subset() defining the subset we plot

    interactive : Bool
        is this view interactive?
        
    Notes
    -----
    We inherit `xfacet` and `yfacet` from `cytoflow.views.HistogramView`, but
    they must both be unset!
        
    Examples
    --------
    In an IPython notebook with `%matplotlib notebook`
    
    >>> t = flow.ThresholdOp(name = "Threshold",
    ...                      channel = "Y2-A")
    >>> tv = t.default_view()
    >>> tv.plot(ex2)
    >>> tv.interactive = True
    >>> # .... draw a threshold on the plot
    >>> ex3 = thresh.apply(ex2)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.views.threshold')
    friendly_id = Constant("Threshold Selection")
    
    op = Instance(IOperation)
    name = DelegatesTo('op')
    channel = DelegatesTo('op')
    threshold = DelegatesTo('op')
    interactive = Bool(False, transient = True)

    # internal state
    _ax = Any(transient = True)
    _line = Instance(Line2D, transient = True)
    _cursor = Instance(Cursor, transient = True)
    
    def plot(self, experiment, **kwargs):
        """Plot the histogram and then plot the threshold on top of it."""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if self.xfacet:
            raise util.CytoflowViewError("ThresholdSelection.xfacet must be empty")
        
        if self.yfacet:
            raise util.CytoflowViewError("ThresholdSelection.yfacet must be empty")
        
        super(ThresholdSelection, self).plot(experiment, **kwargs)
        self._ax = plt.gca()        
        self._draw_threshold()
        self._interactive()
    
    @on_trait_change('threshold', post_init = True)
    def _draw_threshold(self):
        if not self._ax or not self.threshold:
            return
        
        if self._line:
            # when used in the GUI, _draw_threshold gets called *twice* without
            # the plot being updated inbetween: and then the line can't be 
            # removed from the plot, because it was never added.  so check
            # explicitly first.  this is likely to be an issue in other
            # interactive plots, too.
            if self._line and self._line in self._ax.lines:
                self._line.remove()
 
            self._line = None
        
        if self.threshold:    
            self._line = plt.axvline(self.threshold, linewidth=3, color='blue')
            
        plt.draw_if_interactive()
        
    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._cursor = Cursor(self._ax, 
                                  horizOn=False,
                                  vertOn=True,
                                  color='blue',
                                  useblit = True)
            self._cursor.connect_event('button_press_event', self._onclick)
            
        elif self._cursor:
            self._cursor.disconnect_events()
            self._cursor = None
            
    def _onclick(self, event):
        """Update the threshold location"""
        # sometimes the axes aren't set up and we don't get xdata (??)
        if event.xdata:
            self.threshold = event.xdata
        
if __name__ == '__main__':
    import cytoflow as flow
    
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])
    
    t = ThresholdOp(channel = "Y2-A", scale = "logicle")
    v = t.default_view()
    
    plt.ioff()
    v.interactive = True
    v.plot(ex)
    plt.show()
    print t.threshold
