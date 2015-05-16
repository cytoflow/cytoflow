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
        
    def is_valid(self, experiment):
        """If the decorated view is valid, we are too"""
        return self.view.is_valid(experiment)
    
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
            fig = plt.gcf()
            if self._line in fig.lines:
                self._line.remove()
 
            self._line = None
        
        if self.threshold:    
            self._line = plt.axvline(self.threshold, linewidth=3, color='blue')
        
    @on_trait_change('interactive')
    def _interactive(self):
        fig = plt.gcf()
        if self.interactive:
            print "set interactive"
            ax = plt.gca()
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
        
        
        