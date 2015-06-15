from traits.api import provides, HasTraits, Instance, Float, Bool, \
                       on_trait_change, List, Any

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.views.i_view import IView

from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

@provides(ISelectionView)
class PolygonSelection(HasTraits):
    """Plots, and lets the user interact with, a 2D selection.
    
    Attributes
    ----------
    polygon : Instance(numpy.ndarray)
        The polygon vertices
        
    view : Instance(IView)
        the IView that this view is wrapping.  I suggest that if it's another
        ISelectionView, that its `interactive` property remain False. >.>
        
    interactive : Bool
        is this view interactive?  Ie, can the user set the polygon verticies
        with mouse clicks?
    """
    
    id = "edu.mit.synbio.cytoflow.views.polygon"
    friendly_id = "Polygon Selection"
    
    view = Instance(IView, transient = True)
    interactive = Bool(False, transient = True)
    
    vertices = List((Float, Float))
    
    # internal state.
    _cursor = Instance(Cursor, transient = True)
    _path = Instance(mpl.path.Path, transient = True)
    _patch = Instance(mpl.patches.PathPatch, transient = True)
    _line = Instance(mpl.lines.Line2D, transient = True)
    _drawing = Bool(transient = True)
        
    def plot(self, experiment, **kwargs):
        """Plot self.view, and then plot the selection on top of it."""
        self.view.plot(experiment, **kwargs)
        self._draw_poly()

    def is_valid(self, experiment):
        """If the decorated view is valid, we are too."""
        return self.view.is_valid(experiment)
    
    @on_trait_change('vertices')
    def _draw_poly(self):
        ca = plt.gca()
         
        if self._patch and self._patch in ca.patches:
            self._patch.remove()
            
        if self._drawing or not self.vertices or len(self.vertices) < 3 \
           or any([len(x) != 2 for x in self.vertices]):
            return
             

        patch_vert = np.concatenate((np.array(self.vertices), 
                                    np.array((0,0), ndmin = 2)))
                                    
        self._patch = \
            mpl.patches.PathPatch(mpl.path.Path(patch_vert, closed = True),
                                  edgecolor="black",
                                  linewidth = 1.5,
                                  fill = False)
            
        ca.add_patch(self._patch)
        plt.gcf().canvas.draw()
    
    @on_trait_change('interactive')
    def _interactive(self):
        if self.interactive:
            ax = plt.gca()
            self._cursor = Cursor(ax, horizOn = False, vertOn = False)            
            self._cursor.connect_event('button_press_event', self._onclick)
            self._cursor.connect_event('motion_notify_event', self._onmove)
        else:
            self._cursor.disconnect_events()
            self._cursor = None       
    
    def _onclick(self, event): 
        """Update selection traits"""      
        if(self._cursor.ignore(event)):
            return
        
        if event.dblclick:
            self._drawing = False
            self.vertices = map(tuple, self._path.vertices)
            self._path = None
            return
                
        ca = plt.gca()
                
        self._drawing = True
        if self._patch and self._patch in ca.patches:
            self._patch.remove()
            
        if self._path:
            vertices = np.concatenate((self._path.vertices,
                                      np.array((event.xdata, event.ydata), ndmin = 2)))
        else:
            vertices = np.array((event.xdata, event.ydata), ndmin = 2)
            
        self._path = mpl.path.Path(vertices, closed = False)
        self._patch = mpl.patches.PathPatch(self._path, 
                                            edgecolor = "black",
                                            fill = False)

        ca.add_patch(self._patch)
        plt.gcf().canvas.draw()
        
    def _onmove(self, event):       
         
        if(self._cursor.ignore(event) 
           or not self._drawing
           or not self._path
           or self._path.vertices.shape[0] == 0
           or not event.xdata
           or not event.ydata):
            return
        
        ca = plt.gca()
         
        if not ca:
            return
         
        if self._line and self._line in ca.lines:
            self._line.remove()
            
        xdata = [self._path.vertices[-1, 0], event.xdata]
        ydata = [self._path.vertices[-1, 1], event.ydata]
        self._line = mpl.lines.Line2D(xdata, ydata, linewidth = 1, color = "black")
        
        ca.add_line(self._line)
        plt.gcf().canvas.draw()
        
        
if __name__ == '__main__':
    import seaborn as sns
    import cytoflow as flow
    import FlowCytometryTools as fc
    
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    mpl.rcParams['savefig.dpi'] = 2 * mpl.rcParams['savefig.dpi']
    
    tube1 = fc.FCMeasurement(ID='Test 1', 
                             datafile='../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')

    tube2 = fc.FCMeasurement(ID='Test 2', 
                           datafile='../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs')
    
    ex = flow.Experiment()
    ex.add_conditions({"Dox" : "float"})
    
    ex.add_tube(tube1, {"Dox" : 10.0})
    ex.add_tube(tube2, {"Dox" : 1.0})
    
    hlog = flow.HlogTransformOp()
    hlog.name = "Hlog transformation"
    hlog.channels = ['V2-A', 'Y2-A']
    ex2 = hlog.apply(ex)
    
    scatter = flow.ScatterplotView()
    scatter.name = "Scatter"
    scatter.xchannel = "V2-A"
    scatter.ychannel = "Y2-A"
    scatter.huefacet = 'Dox'
    
    p = PolygonSelection(view = scatter)
    
    plt.ioff()
    p.plot(ex2)
    p.interactive = True
    plt.show()