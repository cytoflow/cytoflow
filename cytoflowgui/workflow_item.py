'''
Created on Mar 15, 2015

@author: brian
'''

from traits.api import HasStrictTraits, Instance, List, DelegatesTo, Event, \
                       Enum, Property, cached_property, on_trait_change
from traitsui.api import View
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
    id = DelegatesTo('operation')
    
    # the operation's name
    name = DelegatesTo('operation')
    
    # the Task instance that serves as controller for this model
    task = Instance('flow_task.FlowTask')
    
    # the operation this Item wraps
    operation = Instance(IOperation)
    
    # the traitsui View that displays this operation
    ui = Instance(View)
    
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
    
    # a Property wrapper around the previous.result.channels
    # used to constrain the operation view (with an EnumEditor)
    previous_channels = Property(depends_on = 'previous.result.channels')
    
    # the next WorkflowItem in the workflow
    next = Instance('WorkflowItem')
    
    # are we valid?
    # MAGIC: first value is the default
    valid = Enum("invalid", "updating", "valid")
    
    # the icon for the vertical notebook view.  Qt specific, sadly.
    icon = Property(depends_on = 'valid')
    
    # an event for the previous WorkflowItem to tell this one to update
    update = Event
        
    @on_trait_change('operation.+')
    def _update_fired(self):
        """
        Called when the previous WorkflowItem has changed its result or
        self.operation changed its parameters
        """
        
        self.task.operation_parameters_updated(self)
            
#     def _valid_changed(self, old, new):
#         if old == "valid" and new == "invalid" and self.next is not None:
#             self.next.valid = "invalid"
#     
#     @on_trait_change('operation.+')
#     def _on_operation_trait_change(self):
#         self._update_fired()
    
    @cached_property
    def _get_previous_channels(self):
        if (not self.previous) or (not self.previous.result):
            return []
              
        return self.previous.result.channels
    
    @cached_property
    def _get_icon(self):
        if self.valid == "valid":
            return QtGui.QStyle.SP_DialogOkButton
        elif self.valid == "updating":
            return QtGui.QStyle.SP_BrowserReload
        else: # self.valid == "invalid" or None
            return QtGui.QStyle.SP_BrowserStop
     
    def default_traits_view(self):
        return self.ui
    
