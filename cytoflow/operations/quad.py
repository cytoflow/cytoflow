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
cytoflow.operations.quad
------------------------
'''

from traits.api import (HasStrictTraits, Float, Str, Bool, Instance,
                        provides, on_trait_change, Any, Constant)

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import numpy as np
import pandas as pd

import cytoflow.utility as util
from cytoflow.views import ISelectionView, ScatterplotView

from .i_operation import IOperation
from .base_op_views import Op2DView


@provides(IOperation)
class QuadOp(HasStrictTraits):
    """
    Apply a quadrant gate to a cytometry experiment.
    
    Creates a new metadata column named :attr:`name`, with values 
    ``name_1`` (upper-left quadrant), ``name_2`` (upper-right), 
    ``name_3`` (lower-left), and ``name_4`` (lower-right).  This
    ordering is arbitrary, and was chosen to match the FACSDiva order.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by :meth:`apply`
        
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

    Create and parameterize the operation.
    
    .. plot::
        :context: close-figs
        
        >>> quad = flow.QuadOp(name = "Quad",
        ...                    xchannel = "V2-A",
        ...                    xthreshold = 100,
        ...                    ychannel = "Y2-A",
        ...                    ythreshold = 1000)

    Show the default view

    .. plot::
        :context: close-figs
    
        >>> qv = quad.default_view(huefacet = "Dox",
        ...                        xscale = 'log', 
        ...                        yscale = 'log')
        ...
                                   
        >>> qv.plot(ex)
        
    .. note::
       If you want to use the interactive default view in a Jupyter notebook,
       make sure you say ``%matplotlib notebook`` in the first cell 
       (instead of ``%matplotlib inline`` or similar).  Then call 
       ``default_view()`` with ``interactive = True``::
       
           qv = quad.default_view(huefacet = "Dox",
                                  xscale = 'log',
                                  yscale = 'log',
                                  interactive = True)
           qv.plot(ex)

    Apply the gate and show the result
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = quad.apply(ex)
        >>> ex2.data.groupby('Quad').size()   
        Quad
        Quad_1    1783
        Quad_2    2584
        Quad_3    8236
        Quad_4    7397
        dtype: int64
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.quad')
    friendly_id = Constant("Quadrant Gate")
    
    name = Str
    
    xchannel = Str
    xthreshold = Float(None)
    
    ychannel = Str
    ythreshold = Float(None)
    
    _selection_view = Instance('QuadSelection', transient = True)

    def apply(self, experiment):
        """Applies the quad gate to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old experiment to which this op is applied
            
        Returns
        -------
        Experiment
            a new :class:`~Experiment`, the same as the old :class:`~Experiment` 
            but with a new column the same as the operation :attr:`name`.  
            The new column is of type *Category*, with values ``name_1``, ``name_2``, 
            ``name_3``, and ``name_4``, applied to events CLOCKWISE from upper-left.

        """

        # TODO - the naming scheme (name_1, name_2, etc) is semantically weak.  
        # Add some (generalizable??) way to rename these populations?  
        # It's an Enum; should be pretty easy.
        
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
        
        if not self.xchannel:
            raise util.CytoflowOpError('xchannel', "Must specify xchannel")

        if not self.xchannel in experiment.channels:
            raise util.CytoflowOpError('xchannel',
                                       "xchannel isn't in the experiment")

        if not self.ychannel:
            raise util.CytoflowOpError('ychannel', "Must specify ychannel")
        
        if not self.ychannel in experiment.channels:
            raise util.CytoflowOpError('ychanel', 
                                       "ychannel isn't in the experiment")
        
        if self.xthreshold is None:
            raise util.CytoflowOpError('xthreshold', 'xthreshold must be set!')
        
        if self.ythreshold is None:
            raise util.CytoflowOpError('ythreshold', 'ythreshold must be set!')

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
        self._selection_view = QuadSelection(op = self)
        self._selection_view.trait_set(**kwargs)
        return self._selection_view
    
@provides(ISelectionView)
class QuadSelection(Op2DView, ScatterplotView):
    """Plots, and lets the user interact with, a quadrant gate.
    
    Attributes
    ----------
    interactive : Bool
        is this view interactive?  Ie, can the user set the threshold with a 
        mouse click?
        
    Notes
    -----
    We inherit :attr:`xfacet` and :attr:`yfacet` from 
    :class:`cytoflow.views.ScatterplotView`, but they must both be unset!
        
    Examples
    --------
    
    In an Jupyter notebook with `%matplotlib notebook`
    
    >>> q = flow.QuadOp(name = "Quad",
    ...                 xchannel = "V2-A",
    ...                 ychannel = "Y2-A"))
    >>> qv = q.default_view()
    >>> qv.interactive = True
    >>> qv.plot(ex2) 
    """
    
    id = Constant('edu.mit.synbio.cytoflow.views.quad')
    friendly_id = Constant("Quadrant Selection")
    
    xfacet = Constant(None)
    yfacet = Constant(None)
    
    # override the Op2DView
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum

    interactive = Bool(False, transient = True)
    
    # internal state.
    _ax = Any(transient = True)
    _hline = Instance(Line2D, transient = True)
    _vline = Instance(Line2D, transient = True)
    _cursor = Instance(util.Cursor, transient = True)
        
    def plot(self, experiment, **kwargs):
        """
        Plot the underlying scatterplot and then plot the selection on top of it.
        
        Parameters
        ----------
        
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
        
        super().plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_lines()
        self._interactive()

    @on_trait_change('op.xthreshold, op.ythreshold', post_init = True)
    def _draw_lines(self):
        if not self._ax:
            return
        
        if self._hline and self._hline in self._ax.lines:
            self._hline.remove()
            
        if self._vline and self._vline in self._ax.lines:
            self._vline.remove()
            
        if self.op.xthreshold and self.op.ythreshold:
            self._hline = plt.axhline(self.op.ythreshold, 
                                      linewidth = 3, 
                                      color = 'blue')
            self._vline = plt.axvline(self.op.xthreshold,
                                      linewidth = 3,
                                      color = 'blue')

            plt.draw()

    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive and self._cursor is None:
            self._cursor = util.Cursor(self._ax,
                                       horizOn = True,
                                       vertOn = True,
                                       color = 'blue',
                                       useblit = True) 
            self._cursor.connect_event('button_press_event', self._onclick)
        elif not self.interactive and self._cursor is not None:
            self._cursor.disconnect_events()
            self._cursor = None
            
    def _onclick(self, event):
        """Update the threshold location"""
        self.op.xthreshold = event.xdata
        self.op.ythreshold = event.ydata  
        
util.expand_class_attributes(QuadSelection)
util.expand_method_parameters(QuadSelection, QuadSelection.plot)  
    
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
    print("x:{0}  y:{1}".format(r.xthreshold, r.ythreshold))
    ex2 = r.apply(ex)
    
    flow.ScatterplotView(xchannel = "V2-A",
                         ychannel = "Y2-A",
                         xscale = "logicle",
                         yscale = "logicle",
                         huefacet = "Quad").plot(ex2)
    plt.show()
