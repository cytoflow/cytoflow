from traits.api import provides, HasTraits, Instance, Float, Bool, \
                       on_trait_change

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.views.i_view import IView

from matplotlib.widgets import SpanSelector
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D

@provides(ISelectionView)
class RangeSelection(HasTraits):
    """Plots, and lets the user interact with, a selection on the X axis.
    
    Is it beautiful?  No, not yet.  Does it demonstrate the capabilities I
    desire?  Yes.
    
    Attributes
    ----------
    min : Float
        The minimum value of the range.
        
    max : Float
        The maximum value of the range.
        
    view : Instance(IView)
        the IView that this view is wrapping.  I suggest that if it's another
        ISelectionView, that its `interactive` property remain False. >.>
        
    interactive : Bool
        is this view interactive?  Ie, can the user set min and max
        with a mouse drag?
    """
    
    id = "edu.mit.synbio.cytoflow.view.range"
    friendly_id = "Range Selection"
    
    min = Float(None)
    max = Float(None)
    
    view = Instance(IView)
    interactive = Bool(False)
    
    # internal state.
    _span = Instance(SpanSelector)
    _min_line = Instance(Line2D)
    _max_line = Instance(Line2D)
    _hline = Instance(Line2D)
        
    def plot(self, experiment, fig_num = None, **kwargs):
        """Plot self.view, and then plot the selection on top of it."""
        self.view.plot(experiment, fig_num, **kwargs)
        self._draw_span()

    def validate(self, experiment):
        """If the decorated view is valid, we are too."""
        return self.view.validate(experiment)
    
    @on_trait_change('min, max')
    def _draw_span(self):
        if not (self.min and self.max):
            return
        
        if self._min_line:
            self._min_line.remove()
        
        if self._max_line:
            self._max_line.remove()
            
        if self._hline:
            self._hline.remove()
            
        if self.min and self.max:
            self._min_line = plt.axvline(self.min, linewidth=3, color='grey')
            self._max_line = plt.axvline(self.max, linewidth=3, color='grey')
            
            ymin, ymax = plt.ylim()
            y = (ymin + ymax) / 2.0
            self._hline = plt.plot([self.min, self.max], 
                                   [y, y], 
                                   color='grey', 
                                   linewidth = 2)[0]
    
    @on_trait_change('interactive')
    def _interactive(self):
        if self.interactive:
            ax = plt.gca()
            self._span = SpanSelector(ax, 
                             onselect=self._onselect, 
                             direction='horizontal',
                             rectprops={'alpha':0.2,
                                        'color':'grey'},
                             span_stays=False,
                             useblit = True)
        else:
            self._span = None
        
    
    def _onselect(self, xmin, xmax): 
        """Update selection traits"""
        self.min = xmin
        self.max = xmax
        
        