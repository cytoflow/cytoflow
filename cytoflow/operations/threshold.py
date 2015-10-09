from traits.api import HasStrictTraits, CFloat, Str, CStr, Instance, \
    Bool, Float, on_trait_change, provides
import pandas as pd

from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError
from cytoflow.views import IView, ISelectionView
from cytoflow.views.histogram import HistogramView

@provides(IOperation)
class ThresholdOp(HasStrictTraits):
    """Apply a threshold to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    channel : Str
        The name of the channel to apply the threshold on.
        
    threshold : Float
        The value at which to threshold this channel.
        
    Examples
    --------
    >>> thresh = flow.ThresholdOp()
    >>> thresh.name = "Y2-A+"
    >>> thresh.channel = 'Y2-A'
    >>> thresh.threshold = 0.3
    >>> 
    >>> ex3 = thresh.apply(ex2)    
    
    Alternately, in an IPython notebook with `%matplotlib notebook`
    
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
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.threshold"
    friendly_id = "Threshold"
    
    name = CStr()
    channel = Str()
    threshold = CFloat()
        
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        old_experiment : Experiment
            the experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.threshold;
            it is False otherwise.
        """
        
        # make sure name got set!
        if not self.name:
            raise CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise CytoflowOpError("Experiment already contains a column {0}"
                               .format(self.name))
            
        if self.channel not in experiment.channels:
            raise CytoflowOpError("{0} isn't a channel in the experiment"
                                  .format(self.channel))
        
        
        new_experiment = experiment.clone()
        new_experiment[self.name] = \
            pd.Series(new_experiment[self.channel] > self.threshold)
            
        new_experiment.conditions[self.name] = "bool"
        new_experiment.metadata[self.name] = {}
            
        return new_experiment
    
    def default_view(self):
        return ThresholdSelection(op = self)


@provides(ISelectionView)
class ThresholdSelection(HasStrictTraits):
    """
    Plots, and lets the user interact with, a threshold on the X axis.
    
    TODO - beautify!
    
    Attributes
    ----------
    op : Instance(ThresholdOp)
        the ThresholdOp we're working on.

    interactive : Bool
        is this view interactive?

    subset : Str    
        the string passed to Experiment.subset() defining the subset we plot
        
    Examples
    --------
    In an IPython notebook with `%matplotlib notebook`
    
    >>> t = flow.ThresholdOp(name = "Threshold",
    ...                      channel = "Y2-A")
    >>> tv = t.default_view()
    >>> tv.plot(ex2)
    >>> tv.interactive = True
    >>> # .... draw a threshold on the plot
    >>> ex3 = thresh.apply(ex2)
    """
    
    id = "edu.mit.synbio.cytoflow.views.threshold"
    friendly_id = "Threshold Selection"
    

    interactive = Bool(False, transient = True)
    op = Instance(IOperation)
    subset = Str

    # internal state
    _view = Instance(HistogramView, transient = True)
    _line = Instance(Line2D, transient = True)
    _cursor = Instance(Cursor, transient = True)
    
    def plot(self, experiment, **kwargs):
        """Plot self.view, and then plot the threshold on top of it."""
        self._view = HistogramView(name = self.op.name,
                                   channel = self.op.channel,
                                   subset = self.subset)
        self._view.plot(experiment, **kwargs)
        if self.interactive:
            self._interactive()
        self._draw_threshold()
    
    @on_trait_change('op.threshold')
    def _draw_threshold(self):
        if not self._view:
            return
        
        if not self.op.threshold:
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
        
        if self.op.threshold:    
            self._line = plt.axvline(self.op.threshold, linewidth=3, color='blue')
            
        plt.draw_if_interactive()
        
    @on_trait_change('interactive')
    def _interactive(self):
        if not self._view:
            return
        
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
        self.op.threshold = event.xdata
        
if __name__ == '__main__':
    import cytoflow as flow
    import fcsparser

    #mpl.rcParams['savefig.dpi'] = 2 * mpl.rcParams['savefig.dpi']
    
    tube1 = fcsparser.parse('../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                            reformat_meta = True)

    tube2 = fcsparser.parse('../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                            reformat_meta = True)
    
    ex = flow.Experiment()
    ex.add_conditions({"Dox" : "float"})
    
    ex.add_tube(tube1, {"Dox" : 10.0})
    ex.add_tube(tube2, {"Dox" : 1.0})
    
    hlog = flow.HlogTransformOp()
    hlog.name = "Hlog transformation"
    hlog.channels = ['Y2-A']
    ex2 = hlog.apply(ex)
    
    t = ThresholdOp(channel = "Y2-A")
    v = t.default_view()
    
    plt.ioff()
    v.interactive = True
    v.plot(ex2)
    plt.show()
    print t.threshold
