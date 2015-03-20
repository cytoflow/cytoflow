'''
Created on Mar 19, 2015

@author: brian
'''
from traits.api import provides, HasTraits, Float, Instance, Bool, \
                       on_trait_change

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.views.i_view import IView

from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D

@provides(ISelectionView)
class ThresholdSelection(HasTraits):
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
    """
    
    threshold = Float(None)
    
    view = Instance(IView)
    interactive = Bool(False)

    # internal state
    _line = Instance(Line2D)
    
    def plot(self, experiment, **kwargs):
        """Plot self.view, and then plot the threshold on top of it."""
        self.view.plot(experiment, **kwargs)
        self._draw_threshold
        
    def validate(self, experiment):
        """If the decorated view is valid, we are too"""
        return self.view.validate(experiment)
    
    @on_trait_change('threshold')
    def _draw_threshold(self):
        if not self.threshold:
            return
        
        if self._line:
            self._line.remove()
            
        self._line = plt.axvline(self.threshold, linewidth=3, color='blue')
        
    @on_trait_change('interactive')
    def _interactive(self):
        if self.interactive:
            ax = plt.gca()
            self._cursor = Cursor(ax, 
                                  horizOn=False,
                                  vertOn=True,
                                  color='blue')
            fig = plt.gcf()
            fig.canvas.mpl_connect('button_press_event', self._onclick)
        else:
            self._cursor = None
            
    def _onclick(self, event):
        """Update the threshold location"""
        self.threshold = event.xdata
        
        
        