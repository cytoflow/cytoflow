'''
Created on Jan 15, 2021

@author: brian
'''

import pandas as pd
import natsort

from cytoflow.views import IView
from cytoflow import utility as util

class IterWrapper(object):
    def __init__(self, iterator, by):
        self.iterator = iterator
        self.by = by
        
    def __iter__(self):
        return self
        
    def __next__(self):
        return next(self.iterator)

class IWorkflowView(IView):
            
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
    
    def plot_wi(self, wi):
        if self.plot_names:
            self.plot(wi.result, 
                      plot_name = self.current_plot,
                      **self.plot_params.trait_get())
        else:
            self.plot(wi.result,
                      **self.plot_params.trait_get())
            
    def enum_plots_wi(self, wi):
        if not self.plotfacet:
            return iter([])
        
        if self.plotfacet and self.plotfacet not in wi.result.conditions:
            raise util.CytoflowViewError("Plot facet {0} not in the experiment"
                                    .format(self.huefacet))
        values = natsort.natsorted(pd.unique(wi.result[self.plotfacet]))
        return IterWrapper(iter(values), [self.plotfacet])
    
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
            

    def get_notebook_code(self, idx):
        raise NotImplementedError("get_notebook_code is unimplemented for {id}"
                                  .format(id = self.id))
        
        