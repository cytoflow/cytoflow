#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from traits.api import HasTraits, List, Instance, on_trait_change, Any
from traitsui.api import View, Item

from cytoflowgui.vertical_notebook_editor import VerticalNotebookEditor
from cytoflowgui.workflow_item import WorkflowItem

import warnings

from traits.api import HasStrictTraits, Instance, List, DelegatesTo, Enum, \
                       Property, cached_property, on_trait_change, \
                       Str, Dict
from traitsui.api import View, Item, Handler
from pyface.qt import QtGui
from pyface.tasks.api import Task

from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflow.views.i_view import IView
from cytoflow.utility import CytoflowError


# threading AND multiprocessing, oh my!

import multiprocessing
import threading

class Workflow(HasTraits):
    """
    A list of WorkflowItems.
    """

    workflow = List(WorkflowItem)
    selected = Instance(WorkflowItem)

    traits_view = View(Item(name='workflow',
                            id='table',
                            editor=VerticalNotebookEditor(page_name='.name',
                                                          page_description='.friendly_id',
                                                          page_icon='.icon',
                                                          selected = 'selected',
                                                          scrollable = True,
                                                          multiple_open = False,
                                                          delete = True),
                            show_label = False
                            ),
                       #resizable = True
                       )
    
    # multiprocessing and multithreading plan:
    
    # the parent process maintains the UI and a copy of the model but with 
    # NO DATA.  all the actual data processing happens in a pair of child 
    # processes, the "valid" process and the "running" process.  the "valid"
    # process contains a workflow for which all the WorkflowItems' states
    # are "valid" or "invalid"; the "running" process is allowed to have
    # workflow items that are "estimating" or "applying".
    
    # the order of operations is as follows:  in the parent process, we
    # start with all the WorkflowItems in the "valid" state.  the "valid"
    # process contains a copy of the parent workflow, with actual Experiment
    # instances in the "result" traits.
    
    # assume that the user changes a parameter in one of the operations.
    # the parent process serializes the changed Operation and sends it
    # through a pipe to the "valid" process.  the "valid" process updates
    # its copy of the operation, then spawns a subprocess (the "running"
    # process) and returns its handler and a pipe connection to the parent.
    
    # the "running" process actually runs the operation.  when the operation
    # is finished, it informs the parent process.  the parent process
    # terminates the "valid" process and makes the "running" process the
    # "valid" process.  then, the new "valid" process spawns a new "running"
    # process, which runs the next invalid operation.  the process continues
    # until all the operations have run.
    
    # there are several advantages to this setup.  first, there are never
    # more than two processes that have the actual data, so the in-memory
    # size should never grow beyond twice the size of the same pipeline
    # in a Jupyter notebook.  and it should be very fast, at least on 
    # Linux and MacOS, because spawning a new process gets a copy of all
    # the variables from the old one.
    
    # second, it is not uncommon to have an operation's parameters update
    # while that operation is running.  this is actually the original
    # movitvation for multiprocessing: when 
    
    # each operation runs in its own process, spawned as a child 
    # of the operation before it.  when an operation's parameters get 
    # updated, requiring reprocessing, that operation's process and all 
    # its children are terminated; the previous operation then spawns a 
    # subprocess with a copy of its output Experiment as the input of the 
    # child process's.
    
    # i think that on linux and macos, the copy-on-write model will keep the
    # 
    # we'll have to see if this keeps things from growing
    # out of control.
    
    def __init__(self, *args, **kwargs):
        super(Workflow, self).__init__(*args, **kwargs)
        
    def add_operation(self, operation, default_view):
        # add the new operation after the selected workflow item or at the end
        # of the workflow if no wi is selected
    
    def set_current_view(self, view):
        pass
        
    
    @on_trait_change('workflow[]')
    def _on_workflow_changed(self, name, removed, added):
        pass
    
    parent_connection = Any
    child_connection = Any
    
    def wait_for_updates(self):
        while True:
            (pos, items) = self.conn.recv()
            del self.workflow[pos:]
            self.workflow[-1].next = items[0]
            items[0].previous = self.workflow[-1]
            self.workflow.extend(items)    
            
            
from util import UniquePriorityQueue

def start_worker_process(conn):
    p = WorkflowManager(conn = conn)
    p.wait_for_updates()
    

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
    status = Enum("invalid", "estimating", "applying", "valid", transient = True)
    
    # if we errored out, what was the error string?
    error = Str(transient = True)
    
    # if we got a warning, what was the warning string?
    warning = Str(transient = True)
    
    # the icon for the vertical notebook view.  Qt specific, sadly.
    icon = Property(depends_on = 'status', transient = True)
    
    def default_traits_view(self):
        return View(Item('handler',
                         style = 'custom',
                         show_label = False))
        
#     def update(self):
#         """
#         Called by the controller to update this wi
#         """
#     
# 
#         self.warning = ""
#         self.error = ""
#         self.result = None
#         
#         prev_result = self.previous.result if self.previous else None
#         
#         with warnings.catch_warnings(record = True) as w:
#             try:
#                 if (hasattr(self.operation, "estimate") and
#                     callable(getattr(self.operation, "estimate"))):
#                     self.status = "estimating"
#                     self.operation.estimate(prev_result)
#                 self.status = "applying"
#                 self.result = self.operation.apply(prev_result)
#                 if w:
#                     self.warning = w[-1].message.__str__()
#             except CytoflowError as e:
#                 self.status = "invalid"
#                 self.error = e.__str__()    
#                 print self.error
#                 return
# 
#         self.status = "valid"
           
    @cached_property
    def _get_icon(self):
        if self.status == "valid":
            return QtGui.QStyle.SP_DialogOkButton
        elif self.status == "estimating" or self.status == "applying":
            return QtGui.QStyle.SP_BrowserReload
        else: # self.valid == "invalid" or None
            return QtGui.QStyle.SP_BrowserStop

    @cached_property
    def _get_handler(self):
        return self.operation.handler_factory(model = self.operation,
                                              wi = self)
         
    @on_trait_change('result')
    def _result_changed(self, experiment):
        """Update channels and conditions"""
  
        if experiment:
            self.channels = experiment.channels
            self.conditions = experiment.conditions

                        
    