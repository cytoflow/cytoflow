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
cytoflow.operations.threshold
-----------------------------
'''

from traits.api import (HasStrictTraits, Float, Str, Instance, 
                        Bool, on_trait_change, provides, Any, 
                        Constant)
    
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import cytoflow.utility as util
from cytoflow.views import ISelectionView, HistogramView

from .i_operation import IOperation
from .base_op_views import Op1DView

@provides(IOperation)
class ThresholdOp(HasStrictTraits):
    """
    Apply a threshold gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new column in the
        experiment that's created by :meth:`apply`
        
    channel : Str
        The name of the channel to apply the threshold on.
        
    threshold : Float
        The value at which to threshold this channel.
        
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
        
        >>> thresh_op = flow.ThresholdOp(name = 'Threshold',
        ...                              channel = 'Y2-A',
        ...                              threshold = 2000)
        

    Plot a diagnostic view
    
    .. plot::
        :context: close-figs
        
        >>> tv = thresh_op.default_view(scale = 'log')
        >>> tv.plot(ex)
        
        
    .. note::
       If you want to use the interactive default view in a Jupyter notebook,
       make sure you say ``%matplotlib notebook`` in the first cell 
       (instead of ``%matplotlib inline`` or similar).  Then call 
       ``default_view()`` with ``interactive = True``::
       
           tv = thresh_op.default_view(scale = 'log',
                                       interactive = True)
           tv.plot(ex)
        
    Apply the gate, and show the result
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = thresh_op.apply(ex)
        >>> ex2.data.groupby('Threshold').size()
        Threshold
        False    15786
        True      4214
        dtype: int64
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.threshold')
    friendly_id = Constant("Threshold")
    
    name = Str
    channel = Str
    threshold = Float
    
    _selection_view = Instance('ThresholdSelection', transient = True)
        
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the experiment to which this operation is applied
            
        Returns
        -------
        Experiment
            a new :class:`~experiment`, the same as the old experiment but with 
            a new column of type ``bool`` with the same name as the operation 
            :attr:`name`.  The new condition is ``True`` if the event's 
            measurement in :attr:`channel` is greater than :attr:`threshold`;
            it is ``False`` otherwise.
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name', 
                                       "You have to set the gate's name "
                                       "before applying it!")
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name)) 
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise util.CytoflowOpError('name', 
                                       "Experiment already contains a column {0}"
                                       .format(self.name))

        if self.channel not in experiment.channels:
            raise util.CytoflowOpError('channel',
                                       "{0} isn't a channel in the experiment"
                                       .format(self.channel))

        gate = pd.Series(experiment[self.channel] > self.threshold)

        new_experiment = experiment.clone()
        new_experiment.add_condition(self.name, "bool", gate)
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment
    
    def default_view(self, **kwargs):
        self._selection_view = ThresholdSelection(op = self)
        self._selection_view.trait_set(**kwargs)
        return self._selection_view


@provides(ISelectionView)
class ThresholdSelection(Op1DView, HistogramView):
    """
    Plots, and lets the user interact with, a threshold on the X axis.
    
    TODO - beautify!
    
    Attributes
    ----------
    interactive : Bool
        is this view interactive?
        
    Notes
    -----
    We inherit `xfacet` and `yfacet` from `cytoflow.views.HistogramView`, but
    they must both be unset!
        
    Examples
    --------
    In an Jupyter notebook with `%matplotlib notebook`
    
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

    xfacet = Constant(None)
    yfacet = Constant(None)
    
    scale = util.ScaleEnum
    interactive = Bool(False, transient = True)

    # internal state
    _ax = Any(transient = True)
    _line = Instance(Line2D, transient = True)
    _cursor = Instance(util.Cursor, transient = True)
    
    def plot(self, experiment, **kwargs):
        """
        Plot the histogram and then plot the threshold on top of it.
        
        Parameters
        ----------
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")

        super(ThresholdSelection, self).plot(experiment, **kwargs)
        self._ax = plt.gca()        
        self._draw_threshold()
        self._interactive()
    
    @on_trait_change('op.threshold', post_init = True)
    def _draw_threshold(self):
        if not self._ax or not self.op.threshold:
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
        
        if self.op.threshold:    
            self._line = plt.axvline(self.op.threshold, linewidth=3, color='blue')
            
        plt.draw()
        
    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._cursor = util.Cursor(self._ax, 
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
            self.op.threshold = event.xdata
            
util.expand_class_attributes(ThresholdSelection)
util.expand_method_parameters(ThresholdSelection, ThresholdSelection.plot)  
        
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
    print(t.threshold)
