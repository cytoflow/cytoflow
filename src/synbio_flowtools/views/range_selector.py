"""
Created on Mar 3, 2015

@author: brian
"""

from traits.api import provides, HasTraits, Instance, Float

from synbio_flowtools.views.i_interactiveview import IInteractiveView
from synbio_flowtools.views.i_view import IView

from matplotlib.widgets import SpanSelector
import matplotlib.pyplot as plt

@provides(IInteractiveView)
class RangeSelector(HasTraits):
    """
    classdocs
    """
    
    min = Float
    max = Float
    
    def __init__(self, view):
        self._view = view
        
    def plot(self, experiment, **kwargs):
        
        self._view.plot(experiment, **kwargs)
        ax = plt.gca()
        
        self.span = SpanSelector(ax, 
                                 onselect=self._onselect, 
                                 direction='horizontal',
                                 rectprops={'alpha':0.33,
                                            'color':'grey'},
                                 span_stays=True,
                                 useblit = True)
                                 
        
    def validate(self, experiment):
        return self.view.validate(experiment)
    
    def _onselect(self, xmin, xmax): 
        
        # update the selector properties
        self.min = xmin
        self.max = xmax
        
        