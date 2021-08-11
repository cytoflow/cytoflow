'''
Created on Jan 15, 2021

@author: brian
'''

import pandas as pd
import natsort

from traits.api import (HasStrictTraits, List, Property, Str, Instance, Bool, 
                        Enum, Tuple, observe, Event, Any)

from cytoflow.views import IView
from cytoflow import utility as util

from ..subset import ISubset
from ..serialization import traits_repr

LINE_STYLES = ["solid", "dashed", "dashdot", "dotted","none"]

SCATTERPLOT_MARKERS = ["o", ",", "v", "^", "<", ">", "1", "2", "3", "4", "8",
                       "s", "p", "*", "h", "H", "+", "x", "D", "d", ""]

class IterWrapper(object):
    def __init__(self, iterator, by):
        self.iterator = iterator
        self.by = by
        
    def __iter__(self):
        return self
        
    def __next__(self):
        return next(self.iterator)

class IWorkflowView(IView):
    """
    An interface that extends a `cytoflow` view with functions 
    required for GUI support.
    
    In addition to implementing the interface below, another common thing to 
    do in the derived class is to override traits of the underlying class in 
    order to add metadata that controls their handling by the workflow.  
    Currently, relevant metadata include:
     
      * **status** - Holds status variables -- only sent from the remote process to the local one,
        and doesn't re-plot the view. Example: the possible plot names.
    
      * **transient** - A temporary variable (not copied between processes or serialized).
    
    Attributes
    ----------

    TODO - finish this docstring (plotfacet, plot_params, etc)
        
    changed : Event
        Used to transmit status information back from the operation to the
        workflow.  Set its value to the name of the trait that was changed
    
    """
    
    # make the **kwargs parameters to plot() an object so we can 
    # view and serialize it.
    plot_params = Instance('BasePlotParams')
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset)
    
    # an all-purpose "this thing changed" event
    # set it to the name of the trait that changed
    changed = Event
    
    def should_plot(self, changed, payload):
        """
        Should the owning WorkflowItem refresh the plot when certain things
        change?  `changed` can be:
        - Changed.VIEW -- the view's parameters changed
        - Changed.RESULT -- this WorkflowItem's result changed
        - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
        - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed

        If `should_plot` was called from an event handler, the event is passed
        in as `payload`

        """
        
    def get_notebook_code(self, idx):
        """
        Return Python code suitable for a Jupyter notebook cell that plots this
        view.
        
        Parameters
        ----------
        idx : integer
            The index of the `.WorkflowItem` that holds this view.
            
        Returns
        -------
        string
            The Python code that calls this module.
        """


class WorkflowView(HasStrictTraits):
    """
    Default implementation of IWorkflowView.
    
    Make sure this class is FIRST in the derived class's declaration so it
    shows up earlier in the MRO than the base class from the 
    :module:`cytoflow` module.
    """
    
    # make the "current" value of plot_name an attribute so
    # we can view (with TraitsUI) and serialize it. 
    current_plot = Any
            
    # make the **kwargs parameters to plot() an attribute so we can 
    # view (with TraitsUI) and serialize it.
    plot_params = Instance('BasePlotParams')
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset)
    
    # an all-purpose "this thing changed" event, 
    # observed in workflow.{Local,Remote}Workflow._on_view_changed
    # set it to the name of the trait that changed
    changed = Event
    
    def enum_plots(self, experiment):
        try:
            return super().enum_plots(experiment)
        except (util.CytoflowError, AttributeError):
            return IterWrapper(iter([]), [])    
        
    def should_plot(self, changed, payload):
        """
        Should the owning WorkflowItem refresh the plot when certain things
        change?  `changed` can be:
        - Changed.VIEW -- the view's parameters changed
        - Changed.RESULT -- this WorkflowItem's result changed
        - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
        - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
        
        If `should_plot` is called from a notification handler, the payload
        is the handler `event` parameter.
        """
        return True

    # this makes sure that LocalWorkflow._view_changed notices when
    # a plot parameter changes.
    @observe('plot_params:+type')
    def _on_params_changed(self, _):
        self.changed = 'plot_params'
        
    # same for subset_list
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
            
    def get_notebook_code(self, idx):
        raise NotImplementedError("get_notebook_code is unimplemented for {id}"
                                  .format(id = self.id))
        
class WorkflowFacetView(WorkflowView):
    
    # add another facet for "plot_name".
    plotfacet = Str
    
    def enum_plots(self, experiment):
        if not self.plotfacet:
            return IterWrapper(iter([]), [])
          
        if self.plotfacet and self.plotfacet not in experiment.conditions:
            raise util.CytoflowViewError("Plot facet {0} not in the experiment"
                                    .format(self.huefacet))
        values = natsort.natsorted(pd.unique(experiment[self.plotfacet]))
        return IterWrapper(iter(values), [self.plotfacet])
    
    def plot(self, experiment, **kwargs):
        """
        A default `plot` that subsets by the `plotfacet` and
        :attribute:`current_plot`. If you need it to do something else, you must
        override this method!
        """
         
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
         
        if self.plotfacet and self.current_plot is not None:
            experiment = experiment.subset(self.plotfacet, self.current_plot)
 
        super().plot(experiment, **kwargs)
        
        
class WorkflowByView(WorkflowView):
      
    def plot(self, experiment, **kwargs):
        """
        A default `plot` that passes `current_plot` as the
        plot name.
        """
         
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
        
        plot_names = self.enum_plots(experiment)
        
        if plot_names.by:
            if 'title' not in kwargs or kwargs['title'] == '':
                kwargs['title'] = '{} = {}'.format(",".join(plot_names.by), self.current_plot)
 
            super().plot(experiment, plot_name = self.current_plot, **kwargs)
            
        else:
            super().plot(experiment, **kwargs)
            
    def enum_plots(self, experiment):
        try:
            return super().enum_plots(experiment)
        except (util.CytoflowError, AttributeError):
            return IterWrapper(iter([]), [])    
        
    
class BasePlotParams(HasStrictTraits):
    title = Str
    xlabel = Str
    ylabel = Str
    huelabel = Str

    col_wrap = util.PositiveCInt(None, allow_zero = False, allow_none = True)

    sns_style = Enum(['whitegrid', 'darkgrid', 'white', 'dark', 'ticks'])
    sns_context = Enum(['paper', 'notebook', 'poster', 'talk'])

    legend = Bool(True)
    sharex = Bool(True)
    sharey = Bool(True)
    despine = Bool(True)
        
    def __repr__(self):
        return traits_repr(self)
    
    
class DataPlotParams(BasePlotParams):
    min_quantile = util.PositiveCFloat(0.001)
    max_quantile = util.PositiveCFloat(1.00)   

    
class Data1DPlotParams(DataPlotParams):
    lim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    orientation = Enum('vertical', 'horizontal')

        
class Data2DPlotParams(DataPlotParams):
    xlim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    ylim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    
        
class Stats1DPlotParams(BasePlotParams):
    orientation = Enum(["vertical", "horizontal"])
    lim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None)) 
    
        
class Stats2DPlotParams(BasePlotParams):
    xlim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None)) 
    ylim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None)) 
    
    
class Channel(HasStrictTraits):
    channel = Str
    scale = util.ScaleEnum
        
    def __repr__(self):
        return traits_repr(self)

        
        