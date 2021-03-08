'''
Created on Jan 15, 2021

@author: brian
'''

import pandas as pd
import natsort

from traits.api import (HasStrictTraits, List, Property, Str, Instance, Bool, 
                        Enum, Tuple, observe, Event)

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
    """Default implementation of IWorkflowView"""
    
    # add another facet for "plot_name".
    plotfacet = Str
    
    # make the "current" value of plot_name an attribute so
    # we can view (with TraitsUI) and serialize it. 
    current_plot = Str
        
    # make the **kwargs parameters to plot() an attribute so we can 
    # view (with TraitsUI) and serialize it.
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
        return True
    
    
    def enum_plots(self, experiment):
        if not self.plotfacet:
            return iter([])
          
        if self.plotfacet and self.plotfacet not in experiment.conditions:
            raise util.CytoflowViewError("Plot facet {0} not in the experiment"
                                    .format(self.huefacet))
        values = natsort.natsorted(pd.unique(experiment[self.plotfacet]))
        return IterWrapper(iter(values), [self.plotfacet])
    
    
    def plot(self, experiment, **kwargs):
         
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
         
        if self.plotfacet is not None and self.current_plot is not None:
            experiment = experiment.subset(self.plotfacet, self.current_plot)
        elif self.current_plot is not None:
            kwargs['plot_name'] = self.current_plot
 
        super().plot(self, experiment, **kwargs)
        
    
    # this makes sure that LocalWorkflow._view_changed notices when
    # a plot parameter changes.
    @observe('plot_params:+type')
    def _on_params_changed(self, event):
        self.changed = 'plot_params'
        
    
#     def plot_wi(self, wi):
#         if self.plot_names:
#             self.plot(wi.result, 
#                       plot_name = self.current_plot,
#                       **self.plot_params.trait_get())
#         else:
#             self.plot(wi.result,
#                       **self.plot_params.trait_get())
#             
#             
#             
#     def enum_plots_wi(self, wi):
#         try:
#             return self.enum_plots(wi.result)
#         except:
#             return []

#     def update_plot_names(self, wi):
#         try:
#             plot_iter = self.enum_plots_wi(wi)
#             plot_names = [x for x in plot_iter]
#             if plot_names == [None] or plot_names == []:
#                 self.plot_names = []
#                 self.plot_names_by = []
#             else:
#                 self.plot_names = plot_names
#                 try:
#                     self.plot_names_by = ", ".join(plot_iter.by)
#                 except Exception:
#                     self.plot_names_by = ""
#                     
#                 if self.current_plot == None:
#                     self.current_plot = self.plot_names[0]
#                     
#         except Exception:
#             self.current_plot = None
#             self.plot_names = []
#     
#         
#     @on_trait_change('plot_params.+', post_init = True)
#     def _plot_params_changed(self, obj, name, old, new):
#         self.changed =

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

        
        