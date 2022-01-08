#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
cytoflow.operations.range2d
---------------------------

Applies a 2D range gate (ie, a rectangle gate) to an `Experiment`. 
`range2d` has two classes:

`Range2DOp` -- Applies the gate, given four thresholds

`RangeSelection2D` -- an `IView` that allows you to view the range and/or
interactively set the thresholds.
'''

import pandas as pd

from traits.api import HasStrictTraits, Float, Str, Bool, Instance, \
    provides, on_trait_change, Any, Constant

from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import cytoflow.utility as util
from cytoflow.views import ScatterplotView, ISelectionView

from .i_operation import IOperation
from .base_op_views import Op2DView

@provides(IOperation)
class Range2DOp(HasStrictTraits):
    """
    Apply a 2D range gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by `apply`
        
    xchannel : Str
        The name of the first channel to apply the range gate.
        
    xlow : Float
        The lowest value in xchannel to include in this gate.
        
    xhigh : Float
        The highest value in xchannel to include in this gate.
        
    ychannel : Str
        The name of the second channel to apply the range gate.
        
    ylow : Float
        The lowest value in ychannel to include in this gate.
        
    yhigh : Float
        The highest value in ychannel to include in this gate.
        
   
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
        
        >>> r = flow.Range2DOp(name = "Range2D",
        ...                    xchannel = "V2-A",
        ...                    xlow = 10,
        ...                    xhigh = 1000,
        ...                    ychannel = "Y2-A",
        ...                    ylow = 1000,
        ...                    yhigh = 20000)
  
        
    Show the default view.  

    .. plot::
        :context: close-figs
            
        >>> rv = r.default_view(huefacet = "Dox",
        ...                     xscale = 'log',
        ...                     yscale = 'log')
        
        >>> rv.plot(ex)
        
    .. note::
       If you want to use the interactive default view in a Jupyter notebook,
       make sure you say ``%matplotlib notebook`` in the first cell 
       (instead of ``%matplotlib inline`` or similar).  Then call 
       ``default_view()`` with ``interactive = True``::
       
           rv = r.default_view(huefacet = "Dox",
                               xscale = 'log',
                               yscale = 'log',
                               interactive = True)
           rv.plot(ex)
        
    Apply the gate, and show the result
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = r.apply(ex)
        >>> ex2.data.groupby('Range2D').size()
        Range2D
        False    16405
        True      3595
        dtype: int64
        
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.range2d')
    friendly_id = Constant("2D Range")
    
    name = Str
    
    xchannel = Str
    xlow = Float(None)
    xhigh = Float(None)
    
    ychannel = Str
    ylow = Float(None)
    yhigh = Float(None)
    
    _selection_view = Instance('RangeSelection2D', transient = True)

    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : `Experiment`
            the `Experiment` to which this op is applied
            
        Returns
        -------
        Experiment
            a new `Experiment`, the same as the old experiment but with 
            a new column with a data type of ``bool`` and the same as the 
            operation `name`.  The bool is ``True`` if the event's 
            measurement in `xchannel` is greater than `xlow` and
            less than `xhigh`, and the event's measurement in 
            `ychannel` is greater than `ylow` and less than 
            `yhigh`; it is ``False`` otherwise.
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
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
        
        if not self.xchannel or not self.ychannel:
            raise util.CytoflowOpError('xchannel',
                                       "Must specify xchannel")

        if not self.xchannel in experiment.channels:
            raise util.CytoflowOpError('xchannel',
                                       "xchannel isn't in the experiment")

        if not self.ychannel:
            raise util.CytoflowOpError('ychannel',
                                       "Must specify ychannel")
        
        if not self.ychannel in experiment.channels:
            raise util.CytoflowOpError('ychannel',
                                       "ychannel isn't in the experiment")
            
        if self.xlow is None:
            raise util.CytoflowOpError('xlow',
                                       "must set 'xlow'")       
                 
        if self.xhigh is None:
            raise util.CytoflowOpError('xhigh',
                                       "must set 'xhigh'")  
        
        if self.xhigh <= experiment[self.xchannel].min():
            raise util.CytoflowOpError('xhigh',
                                       "x channel range high must be > {0}"
                                       .format(experiment[self.xchannel].min()))
        if self.xlow >= experiment[self.xchannel].max():
            raise util.CytoflowOpError('xlow',
                                       "x channel range low must be < {0}"
                                       .format(experiment[self.xchannel].max()))
            
        if self.ylow is None:
            raise util.CytoflowOpError('ylow',
                                       "must set 'ylow'")       
                 
        if self.yhigh is None:
            raise util.CytoflowOpError('yhigh',
                                       "must set 'yhigh'")  
            
        if self.yhigh <= experiment[self.ychannel].min():
            raise util.CytoflowOpError('yhigh',
                                       "y channel range high must be > {0}"
                                       .format(experiment[self.ychannel].min()))
        if self.ylow >= experiment[self.ychannel].max():
            raise util.CytoflowOpError('ylow',
                                       "y channel range low must be < {0}"
                                       .format(experiment[self.ychannel].max()))
        
        x = experiment[self.xchannel].between(self.xlow, self.xhigh)
        y = experiment[self.ychannel].between(self.ylow, self.yhigh)
        gate = pd.Series(x & y)
        
        new_experiment = experiment.clone(deep = False) 
        new_experiment.add_condition(self.name, "bool", gate)   
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))    
        return new_experiment
    
    def default_view(self, **kwargs):
        self._selection_view = RangeSelection2D(op = self)
        self._selection_view.trait_set(**kwargs)
        return self._selection_view
    
@provides(ISelectionView)
class RangeSelection2D(Op2DView, ScatterplotView):
    """
    Plots, and lets the user interact with, a 2D selection.
    
    Attributes
    ----------
    interactive : Bool
        is this view interactive?  Ie, can the user set min and max
        with a mouse drag?
        
    Examples
    --------
    
    In a Jupyter notebook with ``%matplotlib notebook``
    
    >>> r = flow.Range2DOp(name = "Range2D",
    ...                    xchannel = "V2-A",
    ...                    ychannel = "Y2-A"))
    >>> rv = r.default_view()
    >>> rv.interactive = True
    >>> rv.plot(ex2) 
    """
    
    id = Constant('edu.mit.synbio.cytoflow.views.range2d')
    friendly_id = Constant("2D Range Selection")

    xfacet = Constant(None)
    yfacet = Constant(None)
    
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    
    interactive = Bool(False, transient = True)
    
    # internal state.
    _ax = Any(transient = True)
    _selector = Instance(RectangleSelector, transient = True)
    _box = Instance(Rectangle, transient = True)
        
    def plot(self, experiment, **kwargs):
        """
        Plot the underlying scatterplot and then plot the selection on top of it.
        
        Parameters
        ----------
        
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
        
        super(RangeSelection2D, self).plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_rect()
        self._interactive()

    @on_trait_change('op.xlow, op.xhigh, op.ylow, op.yhigh', post_init = True)
    def _draw_rect(self):
        if not self._ax:
            return
        
        if self._box and self._box in self._ax.patches:
            self._box.remove()
            
        if self.op.xlow and self.op.xhigh and self.op.ylow and self.op.yhigh:
            self._box = Rectangle((self.op.xlow, self.op.ylow), 
                                  (self.op.xhigh - self.op.xlow), 
                                  (self.op.yhigh - self.op.ylow), 
                                  facecolor="none",
                                  edgecolor = 'blue',
                                  linewidth = 2)
            self._ax.add_patch(self._box)
            plt.draw()
    
    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._selector = RectangleSelector(
                                self._ax, 
                                onselect=self._onselect, 
                                props=dict(facecolor = 'none',
                                           edgecolor = 'blue',
                                           linewidth = 2),
                                useblit = True)
        else:
            self._selector = None
        
    
    def _onselect(self, pos1, pos2): 
        """Update selection traits"""
        self.op.xlow = min(pos1.xdata, pos2.xdata)
        self.op.xhigh = max(pos1.xdata, pos2.xdata)
        self.op.ylow = min(pos1.ydata, pos2.ydata)
        self.op.yhigh = max(pos1.ydata, pos2.ydata)
        
util.expand_class_attributes(RangeSelection2D)
util.expand_method_parameters(RangeSelection2D, RangeSelection2D.plot) 
    
if __name__ == '__main__':
    import cytoflow as flow
    
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])
    
    r = flow.Range2DOp(xchannel = "V2-A",
                       ychannel = "Y2-A")
    rv = r.default_view()
    
    plt.ioff()
    rv.plot(ex)
    rv.interactive = True
    plt.show()
    print("x:({0}, {1})  y:({2}, {3})".format(r.xlow, r.xhigh, r.ylow, r.yhigh))
