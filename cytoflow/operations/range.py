from traits.api import HasStrictTraits, CFloat, Str, CStr, Instance, Bool, \
    provides, on_trait_change

from matplotlib.widgets import SpanSelector, Cursor
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D    

from cytoflow.views.histogram import HistogramView
from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError
from cytoflow.views import IView, ISelectionView

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
    id = "edu.mit.synbio.cytoflow.operations.range"
    friendly_id = "Range"
    
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
            
        new_experiment.conditions[self.name] = "bool"
        new_experiment.metadata[self.name] = {}
            
        return new_experiment
    
    def default_view(self):
        return RangeSelection(op = self)
    
@provides(ISelectionView)
class RangeSelection(HasStrictTraits):
    """Plots, and lets the user interact with, a selection on the X axis.
    
    Is it beautiful?  No.  Does it demonstrate the capabilities I desire?  Yes.
    
    Attributes
    ----------
    op : Instance(RangeOp)
        the RangeOp instance that this view is, well, viewing
        
    subset : Str
        The string passed to `Experiment.query()` to subset the data before
        plotting
        
    interactive : Bool
        is this view interactive?  Ie, can the user set min and max
        with a mouse drag?
        
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
    
    id = "edu.mit.synbio.cytoflow.views.range"
    friendly_id = "Range Selection"

    op = Instance(IOperation)
    subset = Str
    interactive = Bool(False, transient = True)

    # internal state.
    _view = Instance(IView, transient = True)
    _span = Instance(SpanSelector, transient = True)
    _cursor = Instance(Cursor, transient = True)
    _low_line = Instance(Line2D, transient = True)
    _high_line = Instance(Line2D, transient = True)
    _hline = Instance(Line2D, transient = True)
        
    def plot(self, experiment, **kwargs):
        """Plot self.view, and then plot the selection on top of it."""
        self._view = HistogramView(name = self.op.name,
                                   channel = self.op.channel,
                                   subset = self.subset)
        self._view.plot(experiment, **kwargs)
        if self.interactive:
            self._interactive()
        self._draw_span()

    @on_trait_change('op.low, op.high')
    def _draw_span(self):
        if not self._view:
            return
        
        if not (self.op.low and self.op.high):
            return

        ax = plt.gca()
        
        if self._low_line and self._low_line in ax.lines:
            self._low_line.remove()
        
        if self._high_line and self._high_line in ax.lines:
            self._high_line.remove()
            
        if self._hline and self._hline in ax.lines:
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
    
    @on_trait_change('interactive')
    def _interactive(self):
        if not self._view:
            return
        
        if self.interactive:
            ax = plt.gca()
            self._cursor = Cursor(ax, horizOn=False, vertOn=True, color='blue')
            self._span = SpanSelector(ax, 
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
                            reformat_meta = True)

    tube2 = fcsparser.parse('../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                            reformat_meta = True)
    
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

    