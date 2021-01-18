'''
Created on Jan 17, 2021

@author: brian
'''

import os
from natsort import natsorted

from traits.api import HasTraits, HTML, Property, Event, Instance, observe
from traitsui.api import Group, Item, Controller

from cytoflowgui.workflow import WorkflowItem
from cytoflowgui.editors import ColorTextEditor

class OpHandler(Controller):
    """
    Base class for operation handlers.
    """
    context = Instance(WorkflowItem)
        
    conditions_names = Property(depends_on = "context.conditions")
    previous_conditions_names = Property(depends_on = "context.previous_wi.conditions")
    statistics_names = Property(depends_on = "context.statistics")
    previous_statistics_names = Property(depends_on = "context.previous_wi.statistics")
    
    # an event to centralize handling of "Estimate" buttons
    do_estimate = Event()
        
    # the default traits view
    def default_traits_view(self):
        """
        Gets the default :class:`traits.View` for an operation.
        
        Returns
        -------
        traits.View
            The view for an operation.
        """
        
        raise NotImplementedError("Op handlers must override 'default_traits_view")
    
    @observe('do_estimate')
    def _on_estimate(self, event):
        self.context.workflow.estimate(self.context)
    
    # MAGIC: gets value for property "conditions_names"
    def _get_conditions_names(self):
        if self.model and self.model.conditions:
            return natsorted(list(self.context.conditions.keys()))
        else:
            return []
    
    # MAGIC: gets value for property "previous_conditions_names"
    def _get_previous_conditions_names(self):
        if self.context and self.context.previous_wi and self.context.previous_wi.conditions:
            return natsorted(list(self.context.previous_wi.conditions.keys()))
        else:
            return []
        
    # MAGIC: gets value for property "statistics_names"
    def _get_statistics_names(self):
        if self.context and self.context.statistics:
            return natsorted(list(self.context.statistics.keys()))
        else:
            return []
        
    # MAGIC: gets value for property "previous_statistics_names"
    def _get_previous_statistics_names(self):
        if self.context and self.context.previous_wi and self.context.previous_wi.statistics:
            return natsorted(list(self.context.previous_wi.statistics.keys()))
        else:
            return []
        
        
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
        
        if self._cached_help == "":
            current_dir = os.path.abspath(__file__)
            help_dir = os.path.split(current_dir)[0]
            help_dir = os.path.split(help_dir)[0]
            help_dir = os.path.join(help_dir, "help")
            
            op = self.get_operation()
            help_file = None
            for klass in op.__class__.__mro__:
                mod = klass.__module__
                mod_html = mod + ".html"
                
                h = os.path.join(help_dir, mod_html)
                if os.path.exists(h):
                    help_file = h
                    break
                
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
    
        
