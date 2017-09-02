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

'''
cytoflow.operations.range
-------------------------
'''

from traits.api import (HasStrictTraits, CFloat, Str, CStr, Instance, Bool, 
                        provides, on_trait_change, DelegatesTo, Any, Constant)

from matplotlib.widgets import SpanSelector, Cursor
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D    

import cytoflow.utility as util
from cytoflow.views import HistogramView, ISelectionView

from .i_operation import IOperation
from .base_op_views import Op1DView

@provides(IOperation)
class RangeOp(HasStrictTraits):
    """
    Apply a range gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by :meth:`apply`
        
    channel : Str
        The name of the channel to apply the range gate.
        
    low : Float
        The lowest value to include in this gate.
        
    high : Float
        The highest value to include in this gate.

    Examples
    --------
    
    .. plot::
        :context: close-figs
        
        Make a little data set.
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
    
    Create and parameterize the operation.
    
    .. plot::
        :context: close-figs
        
        >>> range_op = flow.RangeOp(name = 'Range',
        ...                         channel = 'Y2-A',
        ...                         low = 2000,
        ...                         high = 10000)
        

    Plot a diagnostic view
    
    .. plot::
        :context: close-figs
        
        >>> range_op.default_view(scale = 'log').plot(ex)
        
    Apply the gate, and show the result
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = range_op.apply(ex)
        >>> ex2.data.groupby('Range').size()
        Range
        False    16042
        True      3958
        dtype: int64
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.range')
    friendly_id = Constant('Range')
    
    name = CStr()
    channel = Str()
    low = CFloat()
    high = CFloat()
        
    def apply(self, experiment):
        """Applies the range gate to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
        Experiment
            a new experiment, the same as old :class:`~Experiment` but with a new
            column of type ``bool`` with the same as the operation name.  The 
            bool is ``True`` if the event's measurement in :attr:`channel` is 
            greater than :attr:`low` and less than :attr:`high`; it is ``False`` 
            otherwise.
        """

        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name', 
                                       "You have to set the gate's name "
                                       "before applying it!")

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError('name', 
                                       "Experiment already has a column named {0}"
                                       .format(self.name))
        
        if not self.channel:
            raise util.CytoflowOpError('channel', "Channel not specified")
        
        if not self.channel in experiment.channels:
            raise util.CytoflowOpError('channel',
                                       "Channel {0} not in the experiment"
                                       .format(self.channel))
        
        if self.high <= self.low:
            raise util.CytoflowOpError('high',
                                       "range high must be > range low")
        
        if self.high <= experiment[self.channel].min():
            raise util.CytoflowOpError('high',
                                       "range high must be > {0}"
                                       .format(experiment[self.channel].min()))
        if self.low >= experiment[self.channel].max():
            raise util.CytoflowOpError('low',
                                       "range low must be < {0}"
                                       .format(experiment[self.channel].max()))
        
        gate = experiment[self.channel].between(self.low, self.high)
        new_experiment = experiment.clone()
        new_experiment.add_condition(self.name, "bool", gate)
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
            
        return new_experiment
    
    def default_view(self, **kwargs):
        return RangeSelection(op = self, **kwargs)
    
@provides(ISelectionView)
class RangeSelection(Op1DView, HistogramView):
    """
    Plots, and lets the user interact with, a selection on the X axis.
    
    
    Attributes
    ----------
        
    interactive : Bool
        is this view interactive?  Ie, can the user set min and max
        with a mouse drag?
        
    Notes
    -----
    We inherit :attr:`xfacet` and :attr:`yfacet` from `cytoflow.views.HistogramView`, but
    they must both be unset!
        
    Examples
    --------
    
    In an IPython notebook with `%matplotlib notebook`
    
    >>> r = RangeOp(name = "RangeGate",
    ...             channel = 'Y2-A')
    >>> rv = r.default_view()
    >>> rv.interactive = True
    >>> rv.plot(ex2)
    >>> ### draw a range on the plot ###
    >>> print r.low, r.high
    """
    
    id = Constant('edu.mit.synbio.cytoflow.views.range')
    friendly_id = Constant("Range Selection")

    xfacet = Constant(None)
    yfacet = Constant(None)

    low = DelegatesTo('op')
    high = DelegatesTo('op')
    
    scale = util.ScaleEnum
    
    interactive = Bool(False, transient = True)

    # internal state.
    _ax = Any(transient = True)
    _span = Instance(SpanSelector, transient = True)
    _cursor = Instance(Cursor, transient = True)
    _low_line = Instance(Line2D, transient = True)
    _high_line = Instance(Line2D, transient = True)
    _hline = Instance(Line2D, transient = True)
        
    def plot(self, experiment, **kwargs):
        """
        Plot the underlying histogram and then plot the selection on top of it.
        
        Parameters
        ----------
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")

        super(RangeSelection, self).plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_span()
        self._interactive()

    @on_trait_change('low,high', post_init = True)
    def _draw_span(self):
        if not (self._ax and self.low and self.high):
            return
        
        if self._low_line and self._low_line in self._ax.lines:
            self._low_line.remove()
        
        if self._high_line and self._high_line in self._ax.lines:
            self._high_line.remove()
            
        if self._hline and self._hline in self._ax.lines:
            self._hline.remove()
            

        self._low_line = plt.axvline(self.low, linewidth=3, color='blue')
        self._high_line = plt.axvline(self.high, linewidth=3, color='blue')
            
        ymin, ymax = plt.ylim()
        y = (ymin + ymax) / 2.0
        self._hline = plt.plot([self.low, self.high], 
                               [y, y], 
                               color='blue', 
                               linewidth = 2)[0]
                                   
        plt.draw()
    
    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._cursor = Cursor(self._ax, 
                                  horizOn=False, 
                                  vertOn=True, 
                                  color='blue', 
                                  useblit = True)
            
            self._span = SpanSelector(self._ax, 
                                      onselect=self._onselect, 
                                      direction='horizontal',
                                      rectprops={'alpha':0.3,
                                                 'color':'grey'},
                                      span_stays=False,
                                      useblit = True)
        else:
            self._cursor = None
            self._span = None
        
    
    def _onselect(self, xmin, xmax): 
        """Update selection traits"""
        self.low = xmin
        self.high = xmax
        
util.expand_class_attributes(RangeSelection)
util.expand_method_parameters(RangeSelection, RangeSelection.plot)  
        
if __name__ == '__main__':
    import cytoflow as flow
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])
    
    r = flow.RangeOp(channel = 'Y2-A')
    rv = r.default_view(scale = "logicle")
    
    plt.ioff()
    rv.plot(ex)
    rv.interactive = True
    plt.show()

    
