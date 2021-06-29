'''
Created on Jan 17, 2021

@author: brian
'''

import inspect, pathlib
from pyface.qt import QtGui

from traits.api import HasTraits, HTML, Instance, observe
from traitsui.api import Group, Item, Controller

from cytoflowgui.workflow import WorkflowItem
from cytoflowgui.editors import ColorTextEditor

class OpHandler(Controller):
    """
    Base class for operation handlers.
    """
    context = Instance(WorkflowItem)

#     # the default traits view
#     def default_traits_view(self):
#         """
#         Gets the default :class:`traits.View` for an operation.
#         
#         Returns
#         -------
#         traits.View
#             The view for an operation.
#         """
#         
#         raise NotImplementedError("Op handlers must override 'default_traits_view")
        
    @observe('context.op_error_trait', dispatch = 'ui', post_init = True)
    def _op_trait_error(self, event):
        
        # check if we're getting called from the local or remote process
#         if self.info is None or self.info.ui is None:
#             return
        
        for ed in self.info.ui._editors:
            if ed.name == self.context.op_error_trait:
                err_state = True
            else:
                err_state = False

            if not ed.label_control:
                continue
            
            item = ed.label_control
            
            if not err_state and not hasattr(item, '_ok_color'):
                continue
            
            pal = QtGui.QPalette(item.palette())  # @UndefinedVariable
            
            if err_state:
                # TODO - this worked in Qt4 but not in Qt5.  at least on linux,
                # the color isn't changing.  i wonder if it has to do with the
                # fixed theme engine we're using...
                setattr(item, 
                        '_ok_color', 
                        QtGui.QColor(pal.color(item.backgroundRole())))  # @UndefinedVariable
                pal.setColor(item.backgroundRole(), QtGui.QColor(255, 145, 145))  # @UndefinedVariable
                item.setAutoFillBackground(True)
                item.setPalette(pal)
                item.repaint()
            else:
                pal.setColor(item.backgroundRole(), item._ok_color)
                delattr(item, '_ok_color')
                item.setAutoFillBackground(False)
                item.setPalette(pal)
                item.repaint()
                
class PluginHelpMixin(HasTraits):
    
    _cached_help = HTML
    
    def get_help(self):
        """
        Gets the HTML help for this module, deriving the filename from
        the class name.
        
        Returns
        -------
        string
            The HTML help, in a single string.
        """
        
        # we name the help files the same as the module name for 
        # the plugin. so, use the inspect module to figure that out.
        
        if self._cached_help == "":
            class_path = pathlib.PurePath(inspect.getfile(self.__class__))
            help_file = class_path.parents[1] / 'help' / 'operations' / (class_path.stem + '.html')
                
            with open(help_file, encoding = 'utf-8') as f:
                self._cached_help = f.read()
                
        return self._cached_help
                        


          
shared_op_traits_view = Group(Item('context.estimate_warning',
                                   label = 'Warning',
                                   resizable = True,
                                   visible_when = 'context.estimate_warning',
                                   editor = ColorTextEditor(foreground_color = "#000000",
                                                            background_color = "#ffff99")),
                              Item('context.estimate_error',
                                    label = 'Error',
                                    resizable = True,
                                    visible_when = 'context.estimate_error',
                                    editor = ColorTextEditor(foreground_color = "#000000",
                                                             background_color = "#ff9191")),
                              Item('context.op_warning',
                                   label = 'Warning',
                                   resizable = True,
                                   visible_when = 'context.op_warning',
                                   editor = ColorTextEditor(foreground_color = "#000000",
                                                            background_color = "#ffff99")),
                              Item('context.op_error',
                                    label = 'Error',
                                    resizable = True,
                                    visible_when = 'context.op_error',
                                    editor = ColorTextEditor(foreground_color = "#000000",
                                                            background_color = "#ff9191")))
    
        
