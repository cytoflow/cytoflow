'''
Created on Jan 15, 2021

@author: brian
'''

import pandas as pd
import natsort

from traits.api import HasStrictTraits, List, Property, Str, Instance

from cytoflow.views import IView
from cytoflow import utility as util

from ..subset import ISubset
from .view_parameters import BasePlotParams

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
    plot_params = Instance(BasePlotParams)
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, depends_on = "subset_list.str")
    subset_list = List(ISubset)
    
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
    
    # add another facet for "plot_name"
    plotfacet = Str
    
    # 
    plot_names = List(Str)
    current_plot = Str
    
    # make the plot 
    plot_params = Instance(BasePlotParams)
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, depends_on = "subset_list.str")
    subset_list = List(ISubset)
        
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
    
#     def plot_wi(self, wi):
#         if self.plot_names:
#             self.plot(wi.result, 
#                       plot_name = self.current_plot,
#                       **self.plot_params.trait_get())
#         else:
#             self.plot(wi.result,
#                       **self.plot_params.trait_get())
#             
#     def enum_plots_wi(self, wi):
#         if not self.plotfacet:
#             return iter([])
#         
#         if self.plotfacet and self.plotfacet not in wi.result.conditions:
#             raise util.CytoflowViewError("Plot facet {0} not in the experiment"
#                                     .format(self.huefacet))
#         values = natsort.natsorted(pd.unique(wi.result[self.plotfacet]))
#         return IterWrapper(iter(values), [self.plotfacet])
#     
    def plot(self, experiment, plot_name = None, **kwargs):
         
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
         
        if self.plotfacet and plot_name is not None:
            experiment = experiment.subset(self.plotfacet, plot_name)
 
        super().plot(self, experiment, **kwargs)
            
            
#     def enum_plots_wi(self, wi):
#         try:
#             return self.enum_plots(wi.result)
#         except:
#             return []

    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
 
#     @on_trait_change('subset_list.str')
#     def _subset_changed(self, obj, name, old, new):
#         self.changed = (Changed.VIEW, (self, 'subset_list', self.subset_list)) 
                

            

    def get_notebook_code(self, idx):
        raise NotImplementedError("get_notebook_code is unimplemented for {id}"
                                  .format(id = self.id))
        
        