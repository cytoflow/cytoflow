'''
Created on Jan 16, 2021

@author: brian
'''

import os

from traits.api import HasTraits, observe, HTML, Instance
from traitsui.api import View, Item, HGroup, TextEditor, Controller, TupleEditor
from pyface.qt import QtGui

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
        
        if self._cached_help == "":
            current_dir = os.path.abspath(__file__)
            help_dir = os.path.split(current_dir)[0]
            help_dir = os.path.split(help_dir)[0]
            help_dir = os.path.join(help_dir, "help")
             
            view = self.get_view()
            help_file = None
            for klass in view.__class__.__mro__:
                mod = klass.__module__
                mod_html = mod + ".html"
                 
                h = os.path.join(help_dir, mod_html)
                if os.path.exists(h):
                    help_file = h
                    break
                 
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
        