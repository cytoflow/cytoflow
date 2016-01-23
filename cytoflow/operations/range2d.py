from traits.api import HasStrictTraits, CFloat, Str, CStr, Bool, Instance, \
    provides, on_trait_change, DelegatesTo, Any, Constant
from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError, CytoflowViewError
from cytoflow.views import ISelectionView
from cytoflow.views.scatterplot import ScatterplotView

from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


@provides(IOperation)
class Range2DOp(HasStrictTraits):
    """Apply a 2D range gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    xchannel : Str
        The name of the first channel to apply the range gate.
        
    xlow : Float
        The lowest value in xchannel to include in this gate.
        
    xhigh : Float
        The highest value in xchannel to include in this gate.
        
    ychannel : Str
        The name of the secon channel to apply the range gate.
        
    ylow : Float
        The lowest value in ychannel to include in this gate.
        
    yhigh : Float
        The highest value in ychannel to include in this gate.
        
    Examples
    --------
    
    >>> range_2d = flow.Range2DOp(xchannel = "V2-A",
    ...                           xlow = 0.0,
    ...                           xhigh = 0.5,
    ...                           ychannel = "Y2-A",
    ...                           ylow = 0.4,
    ...                           yhigh = 0.8)
    >>> ex3 = range_2d.apply(ex2)

    Alternately, in an IPython notebook with `%matplotlib notebook`
    
    >>> rv = range_2d.default_view()
    >>> rv.plot(ex2)
    >>> ### draw a box on the plot in the notebook ### 
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.range2d')
    friendly_id = Constant("2D Range")
    
    name = CStr()
    
    xchannel = Str()
    xlow = CFloat()
    xhigh = CFloat()
    
    ychannel = Str()
    ylow = CFloat()
    yhigh = CFloat()

    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.low and
            less than self.high; it is False otherwise.
        """
        
        # make sure name got set!
        if not self.name:
            raise CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise CytoflowOpError("Experiment already contains a column {0}"
                               .format(self.name))
        
        if not self.xchannel or not self.ychannel:
            raise CytoflowOpError("Must specify xchannel and ychannel")

        if not self.xchannel in experiment.channels:
            raise CytoflowOpError("xchannel isn't in the experiment")
        
        if not self.ychannel in experiment.channels:
            raise CytoflowOpError("ychannel isn't in the experiment")
        
        if self.xhigh <= experiment[self.xchannel].min():
            raise CytoflowOpError("x channel range high must be > {0}"
                                  .format(experiment[self.xchannel].min()))
        if self.xlow >= experiment[self.xchannel].max:
            raise CytoflowOpError("x channel range low must be < {0}"
                                  .format(experiment[self.xchannel].max()))
            
        if self.yhigh <= experiment[self.ychannel].min():
            raise CytoflowOpError("y channel range high must be > {0}"
                                  .format(experiment[self.ychannel].min()))
        if self.ylow >= experiment[self.ychannel].max:
            raise CytoflowOpError("y channel range low must be < {0}"
                                  .format(experiment[self.ychannel].max()))
        
        new_experiment = experiment.clone()
        x = new_experiment[self.xchannel].between(self.xlow, self.xhigh)
        y = new_experiment[self.ychannel].between(self.ylow, self.yhigh)
        new_experiment[self.name] = x & y
        
        new_experiment.metadata[self.name] = {'type' : 'bool'}

        return new_experiment
    
    def default_view(self):
        return RangeSelection2D(op = self)
    
@provides(ISelectionView)
class RangeSelection2D(ScatterplotView):
    """Plots, and lets the user interact with, a 2D selection.
    
    Attributes
    ----------
    op : Instance(Range2DOp)
        The instance of Range2DOp that we're viewing / editing
        
    huefacet : Str
        The conditioning variable to plot multiple colors
        
    subset : Str
        The string passed to `Experiment.query()` to subset the data before
        plotting
        
    interactive : Bool
        is this view interactive?  Ie, can the user set min and max
        with a mouse drag?
        
    Notes
    -----
    We inherit `xfacet` and `yfacet` from `cytoflow.views.ScatterplotView`, but
    they must both be unset!
        
    Examples
    --------
    
    In an IPython notebook with `%matplotlib notebook`
    
    >>> r = flow.Range2DOp(name = "Range2D",
    ...                    xchannel = "V2-A",
    ...                    ychannel = "Y2-A"))
    >>> rv = r.default_view()
    >>> rv.interactive = True
    >>> rv.plot(ex2) 
    """
    
    id = Constant('edu.mit.synbio.cytoflow.views.range2d')
    friendly_id = Constant("2D Range Selection")
    
    op = Instance(IOperation)
    name = DelegatesTo('op')
    xchannel = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    interactive = Bool(False, transient = True)
    
    # internal state.
    _ax = Any(transient = True)
    _selector = Instance(RectangleSelector, transient = True)
    _box = Instance(Rectangle, transient = True)
        
    def plot(self, experiment, **kwargs):
        """Plot the underlying scatterplot and then plot the selection on top of it."""
        
        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")
        
        if self.xfacet:
            raise CytoflowViewError("RangeSelection.xfacet must be empty or `Undefined`")
        
        if self.yfacet:
            raise CytoflowViewError("RangeSelection.yfacet must be empty or `Undefined`")
        
        super(RangeSelection2D, self).plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_rect()
        self._interactive()

    @on_trait_change('op.xlow, op.xhigh, op.ylow, op.yhigh', post_init = True)
    def _draw_rect(self):
        if not self._ax:
            return
        
        if self._box and self._box in self._ax.patches:
            self._box.remove()
            
        if self.op.xlow and self.op.xhigh and self.op.ylow and self.op.yhigh:
            self._box = Rectangle((self.op.xlow, self.op.ylow), 
                                  (self.op.xhigh - self.op.xlow), 
                                  (self.op.yhigh - self.op.ylow), 
                                  facecolor="grey",
                                  alpha = 0.2)
            self._ax.add_patch(self._box)
            plt.draw_if_interactive()
    
    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._selector = RectangleSelector(
                                self._ax, 
                                onselect=self._onselect, 
                                rectprops={'alpha':0.2,
                                           'color':'grey'},
                                useblit = True)
        else:
            self._selector = None
        
    
    def _onselect(self, pos1, pos2): 
        """Update selection traits"""
        self.op.xlow = min(pos1.xdata, pos2.xdata)
        self.op.xhigh = max(pos1.xdata, pos2.xdata)
        self.op.ylow = min(pos1.ydata, pos2.ydata)
        self.op.yhigh = max(pos1.ydata, pos2.ydata)
    
if __name__ == '__main__':
    import cytoflow as flow
    import fcsparser
    
    tube1 = fcsparser.parse('../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                            reformat_meta = True,
                            channel_naming = "$PnN")

    tube2 = fcsparser.parse('../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                            reformat_meta = True,
                            channel_naming = "$PnN")
    
    ex = flow.Experiment()
    ex.add_conditions({"Dox" : "float"})
    
    ex.add_tube(tube1, {"Dox" : 10.0})
    ex.add_tube(tube2, {"Dox" : 1.0})
    
    hlog = flow.HlogTransformOp()
    hlog.name = "Hlog transformation"
    hlog.channels = ['V2-A', 'Y2-A']
    ex2 = hlog.apply(ex)
    
    r = flow.Range2DOp(xchannel = "V2-A",
                       ychannel = "Y2-A")
    rv = r.default_view()
    
    plt.ioff()
    rv.plot(ex2)
    rv.interactive = True
    plt.show()
    print "x:({0}, {1})  y:({2}, {3})".format(r.xlow, r.xhigh, r.ylow, r.yhigh)
