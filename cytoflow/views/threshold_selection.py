'''
Created on Mar 19, 2015

@author: brian
'''
from traits.api import provides, HasTraits, Float, Instance, Bool, \
                       on_trait_change

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.views.i_view import IView
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
    _hline = Instance(Line2D)
    
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
        
        
        