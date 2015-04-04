'''
Created on Mar 15, 2015

@author: brian
'''

from traits.api import HasStrictTraits, Instance, List, DelegatesTo, Event, \
                       Enum, Property, cached_property, on_trait_change, \
                       Any
from traitsui.api import View, Item, Handler
from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflow.views.i_view import IView
from pyface.qt import QtGui

class WorkflowItem(HasStrictTraits):
    """        
    The basic unit of a Workflow: wraps an operation and a list of views.
    
    This object is part of the workflow *model* -- as such, it is implemented
    *reactively*.  No methods; just reactions to traits being changed by
    the UI and handler.
    """
    
    # the operation's id
    friendly_id = DelegatesTo('operation')
    
    # the operation's name
    name = DelegatesTo('operation')
    
    # the Task instance that serves as controller for this model
    task = Instance('flow_task.FlowTask')
    
    # the operation this Item wraps
    operation = Instance(IOperation)
    
    # the handler that's associated with this operation.
    # since it doesn't maintain any state, we can make and destroy as needed
    handler = Property(depends_on = 'operation', trait = Instance(Handler))
    
    # the Experiment that is the result of applying *operation* to a 
    # previous Experiment
    result = Instance(Experiment)
    
    # the IViews against the output of this operation
    views = List(IView)
    
    # the view currently displayed (or selected) by the central pane
    current_view = Instance(IView)
    
    # the previous WorkflowItem in the workflow
    # self.result = self.apply(previous.result)
    previous = Instance('WorkflowItem')
    
    # the next WorkflowItem in the workflow
    next = Instance('WorkflowItem')
    
    # are we valid?
    # MAGIC: first value is the default
    valid = Enum("invalid", "updating", "valid")
    
    # the icon for the vertical notebook view.  Qt specific, sadly.
    icon = Property(depends_on = 'valid')
    
    def default_traits_view(self):
        return View(Item('handler',
                         style = 'custom',
                         show_label = False))
        
    @on_trait_change('operation.+')
    def update(self):
        """
        Called when self.operation changed its parameters.  also called by
        the controller.
        """
        if self.task:
            self.task.operation_parameters_updated(self)
    
    @cached_property
    def _get_icon(self):
        if self.valid == "valid":
            return QtGui.QStyle.SP_DialogOkButton
        elif self.valid == "updating":
            return QtGui.QStyle.SP_BrowserReload
        else: # self.valid == "invalid" or None
            return QtGui.QStyle.SP_BrowserStop

    @cached_property
    def _get_handler(self):
        # operation.handler isn't statically defined; it's dynamically
        # associated with this instance in flow_task
        return self.operation.handler_factory(model = self.operation,
                                              wi = self)