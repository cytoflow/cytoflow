'''
Created on Mar 19, 2015

@author: brian
'''
from traits.api import provides, HasStrictTraits, Float, Instance, Bool, \
                       on_trait_change

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.views.i_view import IView

from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

@provides(ISelectionView)
class ThresholdSelection(HasStrictTraits):
    """
    Plots, and lets the user interact with, a threshold on the X axis.
    
    TODO - beautify!
    
    Attributes
    ----------
    threshold : Float
        The threshold
        
    view : Instance(IView)
        the IView that this view is wrapping.
        
    interactive : Bool
        is this view interactive?
        
    Examples
    --------
    In an IPython notebook with `%matplotlib notebook`
    
    >>> h = flow.HistogramView()
    >>> h.channel = 'Y2-A'
    >>> h.huefacet = 'Dox'
    >>> ts = flow.ThresholdSelection(view = h)
    >>> ts.plot(ex2)
    >>> ts.interactive = True
    >>> # .... draw a threshold on the plot
    >>> thresh = flow.ThresholdOp(name = "Y2-A+",
    ...                           channel = "Y2-A",
    ...                           thresh.threshold = ts.threshold)
    >>> ex3 = thresh.apply(ex2)
    """
    
    id = "edu.mit.synbio.cytoflow.views.threshold"
    friendly_id = "Threshold Selection"
    
    view = Instance(IView, transient = True)
    interactive = Bool(False, transient = True)
    
    threshold = Float(None)

    # internal state
    _line = Instance(Line2D, transient = True)
    _cursor = Instance(Cursor, transient = True)
    
    def plot(self, experiment, **kwargs):
        """Plot self.view, and then plot the threshold on top of it."""
        self.view.plot(experiment, **kwargs)
        self._draw_threshold()
    
    @on_trait_change('threshold')
    def _draw_threshold(self):
        if not self.threshold:
            return
        
        if self._line:
            
            # when used in the GUI, _draw_threshold gets called *twice* without
            # the plot being updated inbetween: and then the line can't be 
            # removed from the plot, because it was never added.  so check
            # explicitly first.  this is likely to be an issue in other
            # interactive plots, too.
            ax = plt.gca()
            if self._line and self._line in ax.lines:
                self._line.remove()
 
            self._line = None
        
        if self.threshold:    
            self._line = plt.axvline(self.threshold, linewidth=3, color='blue')
            
        plt.draw_if_interactive()
        
    @on_trait_change('interactive')
    def _interactive(self):
        ax = plt.gca()
        if self.interactive:
            self._cursor = Cursor(ax, 
                                  horizOn=False,
                                  vertOn=True,
                                  color='blue')
            self._cursor.connect_event('button_press_event', self._onclick)
            
        else:
            self._cursor.disconnect_events()
            self._cursor = None
            
    def _onclick(self, event):
        """Update the threshold location"""
        self.threshold = event.xdata
        