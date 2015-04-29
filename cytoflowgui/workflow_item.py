'''
Created on Mar 15, 2015

@author: brian
'''

from traits.api import HasStrictTraits, Instance, List, DelegatesTo, Enum, \
                       Property, cached_property, Bool
from traitsui.api import View, Item, Handler
from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflow.views.i_view import IView
from pyface.qt import QtGui
from pyface.api import error

class WorkflowItem(HasStrictTraits):
    """        
    The basic unit of a Workflow: wraps an operation and a list of views.
    """
    
    # the operation's id
    friendly_id = DelegatesTo('operation')
    
    # the operation's name
    name = DelegatesTo('operation')
    
    # the Task instance that serves as controller for this model
    task = Instance('flow_task.FlowTask', transient = True)
    
    # the operation this Item wraps
    operation = Instance(IOperation)
    
    # the handler that's associated with this operation.
    # since it doesn't maintain any state, we can make and destroy as needed
    handler = Property(depends_on = 'operation', trait = Instance(Handler))
    
    # the Experiment that is the result of applying *operation* to a 
    # previous Experiment
    result = Instance(Experiment, transient = True)
    
    # the IViews against the output of this operation
    views = List(IView)
    
    # the view currently displayed (or selected) by the central pane
    current_view = Instance(IView)
    
    # the default view for this workflow item
    default_view = Instance(IView)
    
    # is this wi plottable with the current view?
    is_plottable = Property(Bool, transient = True)
    
    # the previous WorkflowItem in the workflow
    # self.result = self.apply(previous.result)
    previous = Instance('WorkflowItem')
    
    # the next WorkflowItem in the workflow
    next = Instance('WorkflowItem')
    
    # is the wi valid?
    # MAGIC: first value is the default
    valid = Enum("invalid", "updating", "valid")
    
    # the icon for the vertical notebook view.  Qt specific, sadly.
    icon = Property(depends_on = 'valid', transient = True)
    
    def default_traits_view(self):
        return View(Item('handler',
                         style = 'custom',
                         show_label = False))
        

    def update(self):
        """
        Called by the controller to update this wi
        """
    
        self.valid = "updating"
        
        prev_result = self.previous.result if self.previous else None
        is_valid = self.operation.is_valid(prev_result)
        
        if not is_valid:
            self.valid = "invalid"
            return
        
        # re-run the operation
        
        try:
            self.result = self.operation.apply(prev_result)
        except RuntimeError as e:
            error(None, str(e))       

        self.valid = "valid"
        
    def plot(self, pane):
        """
        pane: FlowTaskPane
        """
        self.current_view.plot_wi(self, pane)
    
    @cached_property
    def _get_icon(self):
        if self.valid == "valid":
            return QtGui.QStyle.SP_DialogOkButton
        elif self.valid == "updating":
            return QtGui.QStyle.SP_BrowserReload
        else: # self.valid == "invalid" or None
            return QtGui.QStyle.SP_BrowserStop

    # MAGIC: returns the value for property is_plottable
    def _get_is_plottable(self):
        return self.current_view and self.current_view.is_wi_valid(self)

    @cached_property
    def _get_handler(self):
        # operation.handler isn't statically defined; it's dynamically
        # associated with this instance in flow_task
        return self.operation.handler_factory(model = self.operation,
                                              wi = self)