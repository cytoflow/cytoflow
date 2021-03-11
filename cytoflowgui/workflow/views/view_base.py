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

class IterWrapper(object):
    def __init__(self, iterator, by):
        self.iterator = iterator
        self.by = by
        
    def __iter__(self):
        return self
        
    def __next__(self):
        return next(self.iterator)

class IWorkflowView(IView):
    
    # add another facet for the plot tab
    plotfacet = Str
    
    # make the **kwargs parameters to plot() an object so we can 
    # view and serialize it.
    plot_params = Instance('BasePlotParams')
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, depends_on = "subset_list.str")
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

        """
        
    def get_notebook_code(self, idx):
        """
        Return Python code suitable for a Jupyter notebook cell that plots this
        view.
        
        Parameters
        ----------
        idx : integer
            The index of the :class:`.WorkflowItem` that holds this view.
            
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
    
    # add another facet for "plot_name".
    plotfacet = Str
    
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
        
        If :method:`should_plot` is called from a notification handler, the payload
        is the handler `event` parameter.
        """
        return True
    
    
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
        A default :method:`plot` that subsets by the :attribute:`plotfacet` and
        :attribute:`current_plot`. If you need it to do something else, you must
        override this method!
        """
         
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
         
        if self.plotfacet and self.current_plot is not None:
            experiment = experiment.subset(self.plotfacet, self.current_plot)
 
        super().plot(experiment, **kwargs)
        
    
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

        
        