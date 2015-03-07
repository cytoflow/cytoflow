from traits.api import Instance, Bool
from cytoflow.views.i_view import IView

class ISelectionView(IView):
    """A decorator that lets you add (possibly interactive) selections to an IView.
    
    Note that this is a Decorator *design pattern*, not a Python @decorator.
    
    Attributes
    ----------
    view : Instance(IView)
        The view that this ISelectionView wraps.  Usually one of the basic
        IViews, but as long as it's not interactive an ISelectionView is
        probably okay.
        
    interactive : Bool
        Is this view's interactivity turned on?
        
    
    Examples
    --------
    
    import cytoflow as flow
    %matplotlib qt  # can't use inline for an interactive view.
    
    ## .... import data, make an experiment ..... ##
    
    h = flow.HistogramView()
    h.channel = 'Y2-A'
    h.huefacet = 'Dox'
   
    r = flow.RangeSelector(view = h)
    r.plot(ex)
    """
    
    view = Instance(IView)
    interactive = Bool(False)