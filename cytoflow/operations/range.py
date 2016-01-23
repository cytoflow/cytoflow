from traits.api import HasStrictTraits, CFloat, Str, CStr, Instance, Bool, \
    provides, on_trait_change, DelegatesTo, Any, Constant

from matplotlib.widgets import SpanSelector, Cursor
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D    

from cytoflow.views.histogram import HistogramView
from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError, CytoflowViewError
from cytoflow.views import ISelectionView

@provides(IOperation)
class RangeOp(HasStrictTraits):
    """Apply a range gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    channel : Str
        The name of the channel to apply the range gate.
        
    low : Float
        The lowest value to include in this gate.
        
    high : Float
        The highest value to include in this gate.
        
    Examples
    --------
    >>> range = flow.RangeOp()
    >>> range.name = "Y2-A+"
    >>> range.channel = 'Y2-A'
    >>> range.low = 0.3
    >>> range.high = 0.8
    >>> 
    >>> ex3 = range.apply(ex2)
    
    Alternately  (in an IPython notebook with `%matplotlib notebook`)
    
    >>> r = RangeOp(name = 'Y2-A+',
    ...             channel = 'Y2-A')
    >>> rv = r.default_view()
    >>> rv.interactive = True
    >>> rv.plot(ex2)
    >>> ### draw a range on the plot ###
    >>> ex3 = r.apply(ex2)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.range')
    friendly_id = Constant('Range')
    
    name = CStr()
    channel = Str()
    low = CFloat()
    high = CFloat()
        
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.low and
            less than self.high; it is False otherwise.
        """

        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        # make sure name got set!
        if not self.name:
            raise CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")

        if self.name in experiment.data.columns:
            raise CytoflowOpError("Experiment already has a column named {0}"
                                  .format(self.name))
        
        if not self.channel:
            raise CytoflowOpError("Channel not specified")
        
        if not self.channel in experiment.channels:
            raise CytoflowOpError("Channel {0} not in the experiment"
                                  .format(self.channel))
        
        if self.high <= self.low:
            raise CytoflowOpError("range high must be > range low")
        
        if self.high <= experiment[self.channel].min():
            raise CytoflowOpError("range high must be > {0}"
                                  .format(experiment[self.channel].min()))
        if self.low >= experiment[self.channel].max:
            raise CytoflowOpError("range low must be < {0}"
                                  .format(experiment[self.channel].max()))
        
        new_experiment = experiment.clone()
        new_experiment[self.name] = \
            new_experiment[self.channel].between(self.low, self.high)
            
        new_experiment.metadata[self.name] = {'type' : 'bool'}
            
        return new_experiment
    
    def default_view(self):
        return RangeSelection(op = self)
    
@provides(ISelectionView)
class RangeSelection(HistogramView):
    """Plots, and lets the user interact with, a selection on the X axis.
    
    Is it beautiful?  No.  Does it demonstrate the capabilities I desire?  Yes.
    
    Attributes
    ----------
    op : Instance(RangeOp)
        the RangeOp instance that this view is, well, viewing
        
    huefacet : Str
        The conditioning variable to show multiple colors on this plot
        
    subset : Str
        The string passed to `Experiment.query()` to subset the data before
        plotting
        
    interactive : Bool
        is this view interactive?  Ie, can the user set min and max
        with a mouse drag?
        
    Notes
    -----
    We inherit `xfacet` and `yfacet` from `cytoflow.views.HistogramView`, but
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

    op = Instance(IOperation)
    name = DelegatesTo('op')
    channel = DelegatesTo('op')
    interactive = Bool(False, transient = True)

    # internal state.
    _ax = Any(transient = True)
    _span = Instance(SpanSelector, transient = True)
    _cursor = Instance(Cursor, transient = True)
    _low_line = Instance(Line2D, transient = True)
    _high_line = Instance(Line2D, transient = True)
    _hline = Instance(Line2D, transient = True)
        
    def plot(self, experiment, **kwargs):
        """Plot the underlying histogram and then plot the selection on top of it."""
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")
        
        if self.xfacet:
            raise CytoflowViewError("RangeSelection.xfacet must be empty or `Undefined`")
        
        if self.yfacet:
            raise CytoflowViewError("RangeSelection.yfacet must be empty or `Undefined`")
        
        super(RangeSelection, self).plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_span()
        self._interactive()

    @on_trait_change('op.low, op.high', post_init = True)
    def _draw_span(self):
        if not (self._ax and self.op.low and self.op.high):
            return
        
        if self._low_line and self._low_line in self._ax.lines:
            self._low_line.remove()
        
        if self._high_line and self._high_line in self._ax.lines:
            self._high_line.remove()
            
        if self._hline and self._hline in self._ax.lines:
            self._hline.remove()
            

        self._low_line = plt.axvline(self.op.low, linewidth=3, color='blue')
        self._high_line = plt.axvline(self.op.high, linewidth=3, color='blue')
            
        ymin, ymax = plt.ylim()
        y = (ymin + ymax) / 2.0
        self._hline = plt.plot([self.op.low, self.op.high], 
                               [y, y], 
                               color='blue', 
                               linewidth = 2)[0]
                                   
        plt.draw_if_interactive()
    
    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._cursor = Cursor(self._ax, horizOn=False, vertOn=True, color='blue')
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
        self.op.low = xmin
        self.op.high = xmax
        
if __name__ == '__main__':
    import cytoflow as flow
    import fcsparser

    mpl.rcParams['savefig.dpi'] = 2 * mpl.rcParams['savefig.dpi']
    
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
    hlog.channels = ['Y2-A']
    ex2 = hlog.apply(ex)
    
    r = flow.RangeOp(channel = 'Y2-A')
    rv = r.default_view()
    
    plt.ioff()
    rv.plot(ex2)
    rv.interactive = True
    plt.show()

    