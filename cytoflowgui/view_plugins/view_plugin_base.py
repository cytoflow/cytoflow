'''
Created on Jan 16, 2021

@author: brian
'''

import inspect, pathlib

from traits.api import HasTraits, observe, HTML, Instance
from traitsui.api import View, Item, HGroup, TextEditor, Controller, TupleEditor, EnumEditor
from pyface.qt import QtGui

from ..workflow.views.view_base import COLORMAPS
from ..editors import TabListEditor

class PluginHelpMixin(HasTraits):
    """
    A mixin to get online HTML help for a class.  It determines the HTML
    path name from the class name.
    """
    
    _cached_help = HTML
    
    def get_help(self):
        """
        Gets the HTML help for this class.
        
        Returns
        -------
        string
            The HTML help in a single string.
        """
        
        
        # we name the help files the same as the module name for 
        # the plugin. so, use the inspect module to figure that out.
        
        if self._cached_help == "":
            class_path = pathlib.PurePath(inspect.getfile(self.__class__))
            help_file = class_path.parents[1] / 'help' / 'views' / (class_path.stem + '.html')
                 
            with open(help_file, encoding = 'utf-8') as f:
                self._cached_help = f.read()
                 
        return self._cached_help
    

class ViewHandler(Controller):
    """
    Useful bits for view handlers.
    """      
     
    context = Instance('cytoflowgui.workflow.workflow_item.WorkflowItem')
    
    # the view for the current plot (tab editor at the top of the plot window)
    view_plot_name_view = \
        View(HGroup(Item('context.plot_names_label',
                         editor = TextEditor(),
                         style = "readonly",
                         show_label = False),
                    Item('current_plot',
                         editor = TabListEditor(name = 'context.plot_names'),
                         style = 'custom',
                         show_label = False)))
        
    @observe('context:plot_names,context:plot_names.items', post_init = True)
    def _plot_names_changed(self, _):
        if self.model and not self.context.plot_names:
            self.model.current_plot = ""

    @observe('context.view_error_trait', dispatch = 'ui', post_init = True)
    def _view_trait_error(self, _):
        
        # check if we're getting called on the local or remote process
        if self.info is None or self.info.ui is None:
            return
        
        for ed in self.info.ui._editors:  
                          
            if ed.name == self.context.view_error_trait:
                err_state = True
            else:
                err_state = False

            if not ed.label_control:
                continue
            
            item = ed.label_control
            
            if not err_state and not hasattr(item, '_ok_color'):
                continue
            
            pal = QtGui.QPalette(item.palette())
            
            if err_state:
                setattr(item, 
                        '_ok_color', 
                        QtGui.QColor(pal.color(item.backgroundRole())))  
                pal.setColor(item.backgroundRole(), QtGui.QColor(255, 145, 145))
                item.setAutoFillBackground(True)
                item.setPalette(pal)
            else:
                pal.setColor(item.backgroundRole(), item._ok_color)
                delattr(item, '_ok_color')
                item.setAutoFillBackground(False)
                item.setPalette(pal)
                
                
BasePlotParamsView = View(Item('title',
                               editor = TextEditor(auto_set = False,
                                                   placeholder = "None")),
                          Item('xlabel',
                               label = "X label",
                               editor = TextEditor(auto_set = False,
                                                   placeholder = "None")),
                          Item('ylabel',
                               label = "Y label",
                               editor = TextEditor(auto_set = False,
                                                   placeholder = "None")),
                          Item('huelabel',
                               label = "Hue label",
                               editor = TextEditor(auto_set = False,
                                                   placeholder = "None")),
        
                          Item('col_wrap',
                               label = "Columns",
                               editor = TextEditor(auto_set = False,
                                                   placeholder = "None",
                                                   format_func = lambda x: "" if x is None else str(x))),
                          Item('sns_style',
                               label = "Style"),
                          Item('sns_context',
                               label = "Context"),
                          Item('palette',
                               label = "Color palette",
                               editor = EnumEditor(values = {'' : '0:(Default)'} | COLORMAPS)),
                          Item('legend',
                               label = "Show legend?"),
                          Item('sharex',
                               label = "Share\nX axis?"),
                          Item('sharey',
                               label = "Share\nY axis?"),
                          Item('despine',
                               label = "Despine?"))


DataPlotParamsView =  View(Item('min_quantile',
                                editor = TextEditor(auto_set = False,
                                                    placeholder = "None")),
                           Item('max_quantile',
                                editor = TextEditor(auto_set = False,
                                                    placeholder = "None")),
                           BasePlotParamsView.content)


Data1DPlotParamsView = View(Item('orientation'),
                            Item('lim',
                                 label = "Data\nLimits",
                                 editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                                            evaluate = float,
                                                                            placeholder = "None",
                                                                            format_func = lambda x: "" if x is None else str(x)),
                                                                 TextEditor(auto_set = False,
                                                                            evaluate = float,
                                                                            placeholder = "None",
                                                                            format_func = lambda x: "" if x is None else str(x))],
                                                      labels = ["Min", "Max"],
                                                      cols = 1)),
                            DataPlotParamsView.content)


Data2DPlotParamsView =  View(Item('xlim',
                                  label = "X Limits",
                                  editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x)),
                                                                  TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x))],
                                                       labels = ["Min", "Max"],
                                                       cols = 1)),
                             Item('ylim',
                                  label = "Y Limits",
                                  editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x)),
                                                                  TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x))],
                                                       labels = ["Min", "Max"],
                                                       cols = 1)),
                             DataPlotParamsView.content)


Stats1DPlotParamsView = View(Item('orientation'),
                             Item('lim',
                                  label = "Limits",
                                  editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x)),
                                                                  TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x))],
                                                       labels = ["Min", "Max"],
                                                       cols = 1)),
                             BasePlotParamsView.content)  


Stats2DPlotParamsView = View(Item('xlim',
                                  label = "X Limits",
                                  editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x)),
                                                                  TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x))],
                                                       labels = ["Min", "Max"],
                                                       cols = 1)),
                             Item('ylim',
                                  label = "Y Limits",
                                  editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x)),
                                                                  TextEditor(auto_set = False,
                                                                             evaluate = float,
                                                                             placeholder = "None",
                                                                             format_func = lambda x: "" if x is None else str(x))],
                                                       labels = ["Min", "Max"],
                                                       cols = 1)),
                             BasePlotParamsView.content)  
        