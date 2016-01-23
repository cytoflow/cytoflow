from traits.api import HasStrictTraits, CFloat, Str, CStr, Bool, Instance, \
    provides, on_trait_change, DelegatesTo, Any, Constant
from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError, CytoflowViewError
from cytoflow.views import ISelectionView
from cytoflow.views.scatterplot import ScatterplotView

from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import numpy as np

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
            raise CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise CytoflowOpError("Experiment already contains a column {0}"
                               .format(self.name))
        
        if not self.xchannel or not self.ychannel:
            raise CytoflowOpError("Must specify xchannel and ychannel")

        if not self.xchannel in experiment.channels:
            raise CytoflowOpError("xchannel isn't in the experiment")
        
        if not self.ychannel in experiment.channels:
            raise CytoflowOpError("ychannel isn't in the experiment")
        
        if not self.xthreshold:
            raise CytoflowOpError('xthreshold must be set!')
        
        if not self.ythreshold:
            raise CytoflowOpError('ythreshold must be set!')
        
#         if self.xthreshold <= experiment[self.xchannel].min():
#             raise CytoflowOpError("x threshold must be > {0}"
#                                   .format(experiment[self.xchannel].min()))
#         if self.xthreshold >= experiment[self.xchannel].max:
#             raise CytoflowOpError("x threshold must be < {0}"
#                                   .format(experiment[self.xchannel].max()))
#             
#         if self.ythreshold <= experiment[self.ychannel].min():
#             raise CytoflowOpError("y channel range high must be > {0}"
#                                   .format(experiment[self.ychannel].min()))
#         if self.ythreshold >= experiment[self.ychannel].max:
#             raise CytoflowOpError("y channel range low must be < {0}"
#                                   .format(experiment[self.ychannel].max()))
        
        new_experiment = experiment.clone()
        new_experiment[self.name] = self.name
        
        # perhaps there's some more pythonic way to do this?
        
        # upper-left
        ul = np.logical_and(new_experiment[self.xchannel] < self.xthreshold,
                            new_experiment[self.ychannel] > self.ythreshold)
        new_experiment.data.loc[ul, self.name] = self.name + '_1'

        # upper-right
        ur = np.logical_and(new_experiment[self.xchannel] > self.xthreshold,
                            new_experiment[self.ychannel] > self.ythreshold)
        new_experiment.data.loc[ur, self.name] = self.name + '_2'
        
        # lower-right
        lr = np.logical_and(new_experiment[self.xchannel] > self.xthreshold,
                            new_experiment[self.ychannel] < self.ythreshold)
        new_experiment.data.loc[lr, self.name] = self.name + '_3'

        # lower-left
        ll = np.logical_and(new_experiment[self.xchannel] < self.xthreshold,
                            new_experiment[self.ychannel] < self.ythreshold)
        new_experiment.data.loc[ll, self.name] = self.name + '_4'
        
        new_experiment.metadata[self.name] = {'type' : 'category'}
        new_experiment.metadata[self.name]['type'] = 'meta'

        return new_experiment
    
    def default_view(self):
        return QuadSelection(op = self)
    
@provides(ISelectionView)
class QuadSelection(ScatterplotView):
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
    ychannel = DelegatesTo('op')
    interactive = Bool(False, transient = True)
    
    # internal state.
    _ax = Any(transient = True)
    _hline = Instance(Line2D, transient = True)
    _vline = Instance(Line2D, transient = True)
    _cursor = Instance(Cursor, transient = True)
        
    def plot(self, experiment, **kwargs):
        """Plot the underlying scatterplot and then plot the selection on top of it."""
        
        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")
        
        if self.xfacet:
            raise CytoflowViewError("RangeSelection.xfacet must be empty or `Undefined`")
        
        if self.yfacet:
            raise CytoflowViewError("RangeSelection.yfacet must be empty or `Undefined`")
        
        super(QuadSelection, self).plot(experiment, **kwargs)
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

            plt.draw_if_interactive()

    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._cursor = Cursor(self._ax,
                                  horizOn = True,
                                  vertOn = True,
                                  color = 'blue') 
            self._cursor.connect_event('button_press_event', self._onclick)
        elif self._cursor:
            self._cursor.disconnect_events()
            self._cursor = None
            
    def _onclick(self, event):
        """Update the threshold location"""
        self.op.xthreshold = event.xdata
        self.op.ythreshold = event.ydata    
    
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
    
    r = flow.QuadOp(name = "Quad",
                    xchannel = "V2-A",
                    ychannel = "Y2-A")
    rv = r.default_view()
    
    plt.ioff()
    rv.plot(ex2)
    rv.interactive = True
    plt.show()
    print "x:{0}  y:{1}".format(r.xthreshold, r.ythreshold)
    ex3 = r.apply(ex2)
    
    flow.ScatterplotView(xchannel = "V2-A",
                         ychannel = "Y2-A",
                         huefacet = "Quad").plot(ex3)
    plt.show()
