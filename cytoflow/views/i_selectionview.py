from traits.api import Instance, Bool
from cytoflow.views import IView

class ISelectionView(IView):
    """A decorator that lets you add (possibly interactive) selections to an IView.
    
    Note that this is a Decorator *design pattern*, not a Python `@decorator`.
    
    Attributes
    ----------
    interactive : Bool
        Is this view's interactivity turned on?
        
    """

    interactive = Bool(False, transient = True)