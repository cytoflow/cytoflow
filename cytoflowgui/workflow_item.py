'''
Created on Mar 15, 2015

@author: brian
'''

from traits.api import HasStrictTraits, Instance, List, DelegatesTo, Enum, \
                       Property, cached_property, Bool, on_trait_change, \
                       Dict, Str
from traitsui.api import View, Item, Handler
from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflow.views.i_view import IView
from cytoflow.utility import CytoflowError
from pyface.qt import QtGui
from pyface.tasks.api import Task

class WorkflowItem(HasStrictTraits):
    """        
    The basic unit of a Workflow: wraps an operation and a list of views.
    
    Notes
    -----
    Because we serialize instances of this, we have to pay careful attention
    to which traits are ``transient`` (and aren't serialized)
    """
    
    # the operation's id
    friendly_id = DelegatesTo('operation')
    
    # the operation's name
    name = DelegatesTo('operation')
    
    # the Task instance that serves as controller for this model
    task = Instance(Task, transient = True)
    
    # the operation this Item wraps
    operation = Instance(IOperation)
    
    # the handler that's associated with this operation; we get it from the 
    # operation plugin, and it controls what operation traits are in the UI
    # and any special handling (heh) of them.  since the handler doesn't 
    # maintain any state, we can make and destroy as needed.
    handler = Property(depends_on = 'operation', 
                       trait = Instance(Handler), 
                       transient = True)
    
    # the Experiment that is the result of applying *operation* to the
    # previous WorkflowItem's ``result``
    result = Instance(Experiment, transient = True)
    
    # the channels and conditions from result.  usually these would be
    # Property traits (ie, determined dynamically), but we need to cache them
    # so that persistence works properly.
    channels = List(Str)
    conditions = Dict(Str, Str)
    
    # the IViews against the output of this operation
    views = List(IView)
    
    # the view currently displayed (or selected) by the central pane
    current_view = Instance(IView)
    
    # the default view for this workflow item
    default_view = Instance(IView)
    
    # the previous WorkflowItem in the workflow
    # self.result = self.apply(previous.result)
    previous = Instance('WorkflowItem')
    
    # the next WorkflowItem in the workflow
    next = Instance('WorkflowItem')
    
    # is the wi valid?
    # MAGIC: first value is the default
    valid = Enum("invalid", "updating", "valid", transient = True)
    
    # if we errored out, what was the error string?
    error = Str(transient = True)
    
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
        self.error = ""
        self.result = None
        
        prev_result = self.previous.result if self.previous else None
        
        try:
            self.result = self.operation.apply(prev_result)
        except CytoflowError as e:
            self.valid = "invalid"
            self.error = e.__str__()    
            print self.error
            return

        self.valid = "valid"
        
#     def plot(self, pane):
#         """
#         pane: FlowTaskPane
#         """
#         if self.current_view:
#             pane.plot(self.result, self.current_plot)
    
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
        return self.operation.handler_factory(model = self.operation,
                                              wi = self)
        
    @on_trait_change('result')
    def _result_changed(self, new):
        """Update channels and conditions"""
 
        if new:
            self.channels = new.channels
            self.conditions = new.conditions