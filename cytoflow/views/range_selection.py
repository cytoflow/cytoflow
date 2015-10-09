from traits.api import provides, HasStrictTraits, Instance, Float, Bool, \
                       on_trait_change

from cytoflow.views import IView, ISelectionView

from matplotlib.widgets import SpanSelector, Cursor
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D

@provides(ISelectionView)
class RangeSelection(HasStrictTraits):
    """Plots, and lets the user interact with, a selection on the X axis.
    
    Is it beautiful?  No.  Does it demonstrate the capabilities I desire?  Yes.
    
    Attributes
    ----------
    low : Float
        The minimum value of the range.
        
    high : Float
        The maximum value of the range.
        
    view : Instance(IView)
        the IView that this view is wrapping.  I suggest that if it's another
        ISelectionView, that its `interactive` property remain False. >.>
        
    interactive : Bool
        is this view interactive?  Ie, can the user set min and max
        with a mouse drag?
        
    Examples
    --------
    
    In an IPython notebook with `%matplotlib notebook`
    
    >>> h = flow.HistogramView()
    >>> h.channel = 'Y2-A'
    >>> rs = flow.RangeSelection(view = h)
    >>> rs.plot(ex2)
    >>> rs.interactive = True
    >>> # ... draw a range on the plot ....
    >>> range = RangeOp(name = "RangeGate")
    >>> range.low, range.high = rs.low, rs.high
    >>> ex3 = range.apply(ex2)
    """
    
    id = "edu.mit.synbio.cytoflow.views.range"
    friendly_id = "Range Selection"

    view = Instance(IView, transient = True)
    interactive = Bool(False, transient = True)
    
    low = Float(None)
    high = Float(None)
    
    # internal state.
    _span = Instance(SpanSelector, transient = True)
    _cursor = Instance(Cursor, transient = True)
    _low_line = Instance(Line2D, transient = True)
    _high_line = Instance(Line2D, transient = True)
    _hline = Instance(Line2D, transient = True)
        
    def plot(self, experiment, **kwargs):
        """Plot self.view, and then plot the selection on top of it."""
        self.view.plot(experiment, **kwargs)
        self._draw_span()

    @on_trait_change('low, high')
    def _draw_span(self):
        if not (self.low and self.high):
            return

        ax = plt.gca()
        
        if self._low_line and self._low_line in ax.lines:
            self._low_line.remove()
        
        if self._high_line and self._high_line in ax.lines:
            self._high_line.remove()
            
        if self._hline and self._hline in ax.lines:
            self._hline.remove()
            
        if self.low and self.high:
            self._low_line = plt.axvline(self.low, linewidth=3, color='blue')
            self._high_line = plt.axvline(self.high, linewidth=3, color='blue')
            
            ymin, ymax = plt.ylim()
            y = (ymin + ymax) / 2.0
            self._hline = plt.plot([self.low, self.high], 
                                   [y, y], 
                                   color='blue', 
                                   linewidth = 2)[0]
                                   
        plt.draw_if_interactive()
    
    @on_trait_change('interactive')
    def _interactive(self):
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
        self.low = xmin
        self.high = xmax
        
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
    hlog.channels = ['V2-A']
    ex2 = hlog.apply(ex)
    
    hist = flow.HistogramView()
    hist.name = "Hist"
    hist.channel = "V2-A"
    hist.huefacet = 'Dox'
    
    range_view = flow.RangeSelection(view = hist) 
    
    plt.ioff()
    range_view.plot(ex2)
    range_view.interactive = True
    plt.show()
