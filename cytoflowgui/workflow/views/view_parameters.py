'''
Created on Jan 15, 2021

@author: brian
'''

from traits.api import (HasTraits, HasStrictTraits, Str, Bool, Enum, Tuple,
                        List, Instance, Any)

from cytoflow import utility as util
from cytoflowgui.workflow.serialization import traits_repr

class EmptyPlotParams(HasTraits):
    pass

    
    
        
# class ParametersMixin(HasStrictTraits): 
#     
#     # plot names
#     plot_names = List(Any, status = True)
#     plot_names_by = Str(status = True)
#     current_plot = Any
#     
#     # kwargs to pass to plot()
#     plot_params = Instance(EmptyPlotParams, ())
#     
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
#         self.changed = (Changed.VIEW, (self, 'plot_params', self.plot_params))