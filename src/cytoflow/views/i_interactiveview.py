"""
Created on Mar 3, 2015

@author: brian
"""
from traits.api import Interface, Instance, provides
from cytoflow.views.i_view import IView

class IInteractiveView(IView):
    """
    A decorator that lets you add interactions to an IView.
    
    Note that this is a Decorator *design pattern*, not a Python @decorator.
    """
    
    def __init__(self, view):
        """
        Create a new InteractiveView wrapping an IView
        
        Args:
            view(IView) - an IView around which to wrap this interaction.
        """
        pass
    