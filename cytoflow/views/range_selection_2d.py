from traits.api import provides, HasTraits, Instance, Float, Bool, \
                       on_trait_change

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.views.i_view import IView

from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle

@provides(ISelectionView)
class RangeSelection2D(HasTraits):
    """Plots, and lets the user interact with, a 2D selection.
    
    Attributes
    ----------
    xmin : Float
        The minimum value of the range on the X axis
        
    xmax : Float
        The maximum value of the range on the X axis
        
    ymin : Float
        The minimum value of the range on the Y axis
        
    ymax : Float
        The maximum value of the range on the Y axis
        
    view : Instance(IView)
        the IView that this view is wrapping.  I suggest that if it's another
        ISelectionView, that its `interactive` property remain False. >.>
        
    interactive : Bool
        is this view interactive?  Ie, can the user set min and max
        with a mouse drag?
    """
    
    id = "edu.mit.synbio.cytoflow.views.range2d"
    friendly_id = "2D Range Selection"
    
    xmin = Float(None)
    xmax = Float(None)

    ymin = Float(None)
    ymax = Float(None)
    
    view = Instance(IView)
    interactive = Bool(False)
    
    # internal state.
    _selector = Instance(RectangleSelector)
    _box = Instance(Rectangle)
        
    def plot(self, experiment, fig_num = None, **kwargs):
        """Plot self.view, and then plot the selection on top of it."""
        self.view.plot(experiment, fig_num, **kwargs)
        self._draw_span()

    def is_valid(self, experiment):
        """If the decorated view is valid, we are too."""
        return self.view.is_valid(experiment)
    
    @on_trait_change('xmin, xmax, ymin, ymax')
    def _draw_rect(self):
        if not (self.xmin and self.xmax and self.ymin and self.ymax):
            return
        
        if self._box:
            self._box.remove()
            
        if self.xmin and self.xmax and self.ymin and self.ymax:
            ca = plt.gca()
            self._box = Rectangle((self.xmin, self.ymin), 
                                  (self.xmax - self.xmin), 
                                  (self.ymax - self.ymin), 
                                  facecolor="grey")
            ca.add_patch(self._box)
    
    @on_trait_change('interactive')
    def _interactive(self):
        if self.interactive:
            ax = plt.gca()
            self._selector = RectangleSelector(
                                ax, 
                                onselect=self._onselect, 
                                rectprops={'alpha':0.2,
                                           'color':'grey'},
                                span_stays=False,
                                useblit = True)
        else:
            self._selector = None
        
    
    def _onselect(self, pos1, pos2): 
        """Update selection traits"""
        self.xmin = min(pos1[0], pos2[0])
        self.xmax = max(pos1[0], pos2[0])
        self.ymin = min(pos1[1], pos2[1])
        self.ymax = max(pos1[1], pos2[1])
        
        