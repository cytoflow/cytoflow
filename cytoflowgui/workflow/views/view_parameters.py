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
     
#     def default_traits_view(self):
#         return View()
    
class BasePlotParams(HasTraits):
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
    
#     def default_traits_view(self):
#         return View(
#                     Item('title',
#                          editor = TextEditor(auto_set = False)),
#                     Item('xlabel',
#                          label = "X label",
#                          editor = TextEditor(auto_set = False)),
#                     Item('ylabel',
#                          label = "Y label",
#                          editor = TextEditor(auto_set = False)),
#                     Item('huelabel',
#                          label = "Hue label",
#                          editor = TextEditor(auto_set = False)),
# 
#                     Item('col_wrap',
#                          label = "Columns",
#                          editor = TextEditor(auto_set = False,
#                                              format_func = lambda x: "" if x == None else str(x))),
#                     Item('sns_style',
#                          label = "Style"),
#                     Item('sns_context',
#                          label = "Context"),
#                     Item('legend'),
#                     Item('sharex',
#                          label = "Share\nX axis?"),
#                     Item('sharey',
#                          label = "Share\nY axis?"),
#                     Item('despine',
#                          label = "Despine?"))
        
    def __repr__(self):
        return traits_repr(self)
    
class DataPlotParams(BasePlotParams):
    
    min_quantile = util.PositiveCFloat(0.001)
    max_quantile = util.PositiveCFloat(1.00)   
    
#     def default_traits_view(self):
#         base_view = BasePlotParams.default_traits_view(self)
#     
#         return View(Item('min_quantile',
#                          editor = TextEditor(auto_set = False)),
#                     Item('max_quantile',
#                          editor = TextEditor(auto_set = False)),
#                     base_view.content)
    
class Data1DPlotParams(DataPlotParams):
    
    lim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    orientation = Enum('vertical', 'horizontal')
    
#     def default_traits_view(self):
#         base_view = BasePlotParams.default_traits_view(self)
#     
#         return View(Item('orientation'),
#                     Item('lim',
#                          label = "Data\nLimits",
#                          editor = TupleEditor(editors = [TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x)),
#                                                          TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x))],
#                                               labels = ["Min", "Max"],
#                                               cols = 1)),
#                     base_view.content)
        
class Data2DPlotParams(DataPlotParams):
    
    xlim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    ylim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    
#     def default_traits_view(self):
#         base_view = BasePlotParams.default_traits_view(self)
#     
#         return View(Item('xlim',
#                          label = "X Limits",
#                          editor = TupleEditor(editors = [TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x)),
#                                                          TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x))],
#                                               labels = ["Min", "Max"],
#                                               cols = 1)),
#                     Item('ylim',
#                          label = "Y Limits",
#                          editor = TupleEditor(editors = [TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x)),
#                                                          TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x))],
#                                               labels = ["Min", "Max"],
#                                               cols = 1)),
#                     base_view.content)
        
class Stats1DPlotParams(BasePlotParams):
    
    orientation = Enum(["vertical", "horizontal"])
    lim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None)) 
    
#     def default_traits_view(self):
#         base_view = BasePlotParams.default_traits_view(self)
#         
#         return View(Item('orientation'),
#                     Item('lim',
#                          label = "Limits",
#                          editor = TupleEditor(editors = [TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x)),
#                                                          TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x))],
#                                               labels = ["Min", "Max"],
#                                               cols = 1)),
#                     base_view.content)  
        
class Stats2DPlotParams(BasePlotParams):
    
    xlim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None)) 
    ylim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None)) 
    
#     def default_traits_view(self):
#         base_view = BasePlotParams.default_traits_view(self)
#         
#         return View(Item('xlim',
#                          label = "X Limits",
#                          editor = TupleEditor(editors = [TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x)),
#                                                          TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x))],
#                                               labels = ["Min", "Max"],
#                                               cols = 1)),
#                     Item('ylim',
#                          label = "Y Limits",
#                          editor = TupleEditor(editors = [TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x)),
#                                                          TextEditor(auto_set = False,
#                                                                     evaluate = float,
#                                                                     format_func = lambda x: "" if x == None else str(x))],
#                                               labels = ["Min", "Max"],
#                                               cols = 1)),
#                     base_view.content)  
    

        
class ParametersMixin(HasStrictTraits): 
    
    # plot names
    plot_names = List(Any, status = True)
    plot_names_by = Str(status = True)
    current_plot = Any
    
    # kwargs to pass to plot()
    plot_params = Instance(EmptyPlotParams, ())
    
    def update_plot_names(self, wi):
        try:
            plot_iter = self.enum_plots_wi(wi)
            plot_names = [x for x in plot_iter]
            if plot_names == [None] or plot_names == []:
                self.plot_names = []
                self.plot_names_by = []
            else:
                self.plot_names = plot_names
                try:
                    self.plot_names_by = ", ".join(plot_iter.by)
                except Exception:
                    self.plot_names_by = ""
                    
                if self.current_plot == None:
                    self.current_plot = self.plot_names[0]
                    
        except Exception:
            self.current_plot = None
            self.plot_names = []
    
        
#     @on_trait_change('plot_params.+', post_init = True)
#     def _plot_params_changed(self, obj, name, old, new):
#         self.changed = (Changed.VIEW, (self, 'plot_params', self.plot_params))