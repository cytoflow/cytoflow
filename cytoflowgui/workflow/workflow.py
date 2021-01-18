#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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

"""
The main model for the GUI.

At its core, the model is a list of WorkflowItem instances.  A WorkflowItem
wraps an operation, its completion status, the result of applying it to
the previous WorkflowItem's result, and views on that result.  The Workflow
also maintains a "current" or selected WorkflowItem.

The left panel of the GUI is a View on this object (viewing the list of
WorkflowItem instances), and the right panel of the GUI is a View of the
selected WorkflowItem's current view.

So far, so simple.  However, in a single-threaded GUI application, the UI
freezes when something processor-intensive is happening.  Adding another thread
doesn't help matters because of the CPython global interpreter lock; while
Python is otherwise computing, the GUI doesn't update.  To solve this, the 
Workflow maintains a copy of itself in a separate process.  The local Workflow
is the one that is viewed by the GUI; the remote Workflow is the one that
actually loads the data and does the processing.  Thus the GUI remains
responsive.  Changed attributes in either Workflow are noticed by a set of 
Traits handlers, which send those changes to the other process.

This process is also where the plotting happens.  For an explanation of how
the plots are ferried back to the GUI, see the module docstring for
matplotlib_backend.py
"""

import sys, threading, logging

from queue import Queue, PriorityQueue

from traits.api import (HasStrictTraits, Int, Bool, Instance, Any, List,
                        on_trait_change)

import matplotlib.pyplot as plt
import cytoflowgui.matplotlib_backend_remote

from cytoflowgui.utility import log_exception

from .workflow_item import WorkflowItem
from .views import IWorkflowView

logger = logging.getLogger(__name__)

class Msg(object):
    NEW_WORKFLOW = "NEW_WORKFLOW"
    ADD_ITEMS = "ADD_ITEMS"
    REMOVE_ITEMS = "REMOVE_ITEMS"
    SELECT = "SELECT"
    
    # send an update to an operation.  payload:
    # - the WorkflowItem index
    # - the name of the updated trait
    # - the new trait value
    UPDATE_OP = "UPDATE_OP"
    
    # send an update to a view.  payload:
    # - the WorkflowItem index
    # - the view id
    # - the name of the updated trait
    # - the new trait value
    UPDATE_VIEW = "UPDATE_VIEW"
    
    CHANGE_CURRENT_VIEW = "CHANGE_CURRENT_VIEW"
    CHANGE_CURRENT_PLOT = "CHANGE_CURRENT_PLOT"
    
    # send an update to a WorkflowItem.  payload:
    # - the WorkflowItem index
    # - the name of the updated trait
    # - the new trait value
    UPDATE_WI = "UPDATE_WI"
    
#     CHANGE_DEFAULT_SCALE = "CHANGE_DEFAULT_SCALE"
    ESTIMATE = "ESTIMATE"
    
    APPLY_CALLED = "APPLY_CALLED"
    PLOT_CALLED = "PLOT_CALLED"
    
    # a statement to evaluate in the remote process, or the result of that
    # evaluation.
    EVAL = "EVAL"
    
    # statement execution
    EXEC = "EXEC"
    
    # apply & execute all
    RUN_ALL = "RUN_ALL"
    
    SHUTDOWN = "SHUTDOWN"
    
class Changed(object):
    # the operation's parameters needed to apply() changed.  
    # payload:
    # - the name of the changed trait
    # - the new trait value
    OPERATION = "OPERATION"  
    
    # the current view's parameters have changed
    # payload:
    # - the IView object that changed
    # - the name of the changed trait
    # - the new trait value 
    VIEW = "VIEW"         
    
    # the operation's parameters to estimate() changed   
    # payload:
    # - the name of the changed trait
    # - the new trait value
    ESTIMATE = "ESTIMATE"    
    
    # the result of calling estimate() changed
    # payload: unused
    ESTIMATE_RESULT = "ESTIMATE_RESULT"  
    
    # some operation status info changed
    # payload:
    # - the name of the changed trait
    # - the new trait value
    OP_STATUS = "OP_STATUS"     
    
    # some view status changed
    # payload:
    # - the IView object that changed
    # - the name of the changed trait
    # - the new trait value
    VIEW_STATUS = "VIEW_STATUS" 
    
    # the result of calling apply() changed
    # payload: unused
    RESULT = "RESULT"        
    
    # the previous WorkflowItem's result changed
    # payload: unused
    PREV_RESULT = "PREV_RESULT"  
    

class UniquePriorityQueue(PriorityQueue):
    """
    A PriorityQueue that only allows one copy of each item.
    http://stackoverflow.com/questions/5997189/how-can-i-make-a-unique-value-priority-queue-in-python
    """
    
    def _init(self, maxsize):
        PriorityQueue._init(self, maxsize)
        self.values = set()

    def _put(self, item):
        if item[1] not in self.values:
            self.values.add(item[1])
            PriorityQueue._put(self, item)
        else:
            pass

    def _get(self):
        item = PriorityQueue._get(self)
        self.values.remove(item[1])
        return item
    
    
def filter_unpicklable(obj):
    if type(obj) is list:
        return [filter_unpicklable(x) for x in obj]
    elif type(obj) is dict:
        return {x: filter_unpicklable(obj[x]) for x in obj}
    else:
        if not hasattr(obj, '__getstate__') and not isinstance(obj,
                  (str, int, float, tuple, list, set, dict)):
            return "filtered: {}".format(type(obj))
        else:
            return obj
    

class LocalWorkflow(HasStrictTraits):
    
    workflow = List(WorkflowItem)
    selected = Instance(WorkflowItem)
    
    modified = Bool
    
    recv_thread = Instance(threading.Thread)
    send_thread = Instance(threading.Thread)
    log_thread = Instance(threading.Thread)
    message_q = Instance(Queue, ())
    
    debug = Bool(False)
    # count the number of times the remote process calls apply() or plot().
    # useful for debugging
    apply_calls = Int(0)
    plot_calls = Int(0)
    
    # evaluate an expression in the remote process.  useful for debugging.
    eval_event = Instance(threading.Event, ())
    eval_result = Any
    
    # execute an expression in the remote process.  useful for debugging.
    exec_event = Instance(threading.Event, ())
    
    def __init__(self, remote_workflow_connection, **kwargs):
        super(LocalWorkflow, self).__init__(**kwargs)  
                
        self.recv_thread = threading.Thread(target = self.recv_main, 
                                            name = "local workflow recv",
                                            args = [remote_workflow_connection])
        self.recv_thread.daemon = True
        self.recv_thread.start()
        
        self.send_thread = threading.Thread(target = self.send_main,
                                            name = "local workflow send",
                                            args = [remote_workflow_connection])
        self.send_thread.daemon = True
        self.send_thread.start()
        

    def recv_main(self, child_conn):
        while child_conn.poll(None):
            try:
                (msg, payload) = child_conn.recv()
            except EOFError:
                return
            
            logger.debug("LocalWorkflow.recv_main :: {}".format((msg, payload)))
            
            try: 
                if msg == Msg.UPDATE_WI:
                    (idx, name, new) = payload
                    wi = self.workflow[idx]
                    
                    if not wi.trait(name).status:
                        raise RuntimeError("Tried to set a local non-status wi trait")
                    
                    with wi.lock:
                        wi.trait_set(**{name : new})
                        
                elif msg == Msg.UPDATE_OP:
                    (idx, name, new) = payload
                    wi = self.workflow[idx]
                    
                    if not wi.operation.trait(name).status:
                        raise RuntimeError("Tried to set a local non-status trait")
                    
                    with wi.lock:
                        wi.operation.trait_set(**{name : new})
                    
                elif msg == Msg.UPDATE_VIEW:
                    (idx, view_id, name, new) = payload
                    wi = self.workflow[idx]
                    view = next((x for x in wi.views if x.id == view_id))
                    
                    if not view.trait(name).status:
                        raise RuntimeError("Tried to set a local non-status trait")
                    
                    with wi.lock:
                        view.trait_set(**{name : new})
                    
                elif msg == Msg.APPLY_CALLED:
                    self.apply_calls = payload
                    
                elif msg == Msg.PLOT_CALLED:
                    self.plot_calls = payload
                    
                elif msg == Msg.EVAL:
                    self.eval_result = payload
                    self.eval_event.set()
                    
                elif msg == Msg.EXEC:
                    self.exec_event.set()
                    
                elif msg == Msg.SHUTDOWN:
                    self.message_q.put(None)
                    return
                    
                else:
                    raise RuntimeError("Bad message from remote")
            
            except Exception:
                log_exception()
    
    def send_main(self, child_conn):
        try:
            while True:
                msg = self.message_q.get()
                
                if msg == None:
                    return
                
                child_conn.send(msg)
        except Exception:
            log_exception()
                
    def add_operation(self, operation):
        # make a new workflow item
        wi = WorkflowItem(operation = operation, workflow = self)
        
        # if the operation has a default view, add it to the wi
        try:
            wi.default_view = operation.default_view()
            wi.views.append(wi.default_view)
            wi.current_view = wi.default_view
        except AttributeError:
            pass
        
        # figure out where to add it
        if self.selected:
            idx = self.workflow.index(self.selected) + 1
        else:
            idx = len(self.workflow)
              
        # the add_remove_items handler takes care of updating the linked list
        self.workflow.insert(idx, wi)
         
        # and make sure to actually select the new wi
        self.selected = wi
        
        return wi
        
        
    def estimate(self, wi):
        """
        Run estimate() on this WorkflowItem
        """
        logger.debug("LocalWorkflow.estimate :: {}"
                     .format(wi))

        idx = self.workflow.index(wi)
        self.message_q.put((Msg.ESTIMATE, idx))
        

    def run_all(self):
        self.message_q.put((Msg.RUN_ALL, None))
        

    @on_trait_change('workflow')
    def _on_new_workflow(self, obj, name, old, new):
        logger.debug("LocalWorkflow._on_new_workflow")
            
        self.selected = None
        
        # send the new workflow to the child process
        self.message_q.put((Msg.NEW_WORKFLOW, self.workflow))
        
        
    @on_trait_change('workflow_items')
    def _on_workflow_add_remove_items(self, event):
        logger.debug("LocalWorkflow._on_workflow_add_remove_items :: {}"
                      .format((event.index, event.removed, event.added)))

        idx = event.index
        self.modified = True
        
        # remove deleted items from the linked list
        if event.removed:
            assert len(event.removed) == 1
            removed = event.removed[0]
            if removed.previous_wi:
                removed.previous_wi.next_wi = removed.next_wi
                
            if removed.next_wi:
                removed.next_wi.previous_wi = removed.previous_wi
            
            self.message_q.put((Msg.REMOVE_ITEMS, idx))
            
            if removed == self.selected:
                self.selected = None
        
        # add new items to the linked list
        if event.added:
            assert len(event.added) == 1

            if idx > 0:
                # populate the new wi with metadata from the old one
                self.workflow[idx].channels = list(self.workflow[idx - 1].channels)
                self.workflow[idx].conditions = dict(self.workflow[idx - 1].conditions)
                self.workflow[idx].metadata = dict(self.workflow[idx - 1].metadata)
                self.workflow[idx].statistics = dict(self.workflow[idx - 1].statistics)
                
                self.workflow[idx - 1].next_wi = self.workflow[idx]
                self.workflow[idx].previous_wi = self.workflow[idx - 1]
                
            if idx < len(self.workflow) - 1:
                self.workflow[idx].next_wi = self.workflow[idx + 1]
                self.workflow[idx + 1].previous_wi = self.workflow[idx]
                
            self.message_q.put((Msg.ADD_ITEMS, (idx, event.added[0])))
            
            
    @on_trait_change('selected')
    def _on_selected_changed(self, obj, name, old, new):
        logger.debug("LocalWorkflow._on_selected_changed :: {}"
                      .format((obj, name, old, new)))
            
        if new is None:
            idx = -1
        else:
            idx = self.workflow.index(new)
            
        self.message_q.put((Msg.SELECT, idx))
        
        
    @on_trait_change('workflow:operation:+')
    def _operation_changed(self, obj, name, old, new):
        logger.debug("LocalWorkflow._operation_changed :: {}"
                      .format((obj, name, old, new)))
        
        if not obj.trait(name).transient and not obj.trait(name).status:         
            wi = next((x for x in self.workflow if x.operation == obj))
            idx = self.workflow.index(wi)
            self.message_q.put((Msg.UPDATE_OP, (idx, name, new)))
            self.modified = True
            

#     @on_trait_change('workflow:operation:changed')
#     def _operation_changed_event(self, obj, _, new):
#         logger.debug("LocalWorkflow._operation_changed_event:: {}"
#                       .format((obj, new)))
#         
#         (_, (name, new)) = new
#         
#         wi = next((x for x in self.workflow if x.operation == obj))
#         idx = self.workflow.index(wi)
#         self.message_q.put((Msg.UPDATE_OP, (idx, name, new)))
#         self.modified = True


    @on_trait_change('workflow:views:+')
    def _view_changed(self, obj, name, old, new):
        logger.debug("LocalWorkflow._view_changed :: {}"
                      .format((obj, name, old, new)))

        if not obj.trait(name).transient and not obj.trait(name).status:
            wi = next((x for x in self.workflow if obj in x.views))
            idx = self.workflow.index(wi)
            self.message_q.put((Msg.UPDATE_VIEW, (idx, obj.id, name, new)))
            self.modified = True
            

#     @on_trait_change('workflow:views:changed')
#     def _view_changed_event(self, obj, _, new):
#         logger.debug("LocalWorkflow._view_changed_event:: {}"
#                       .format((obj, new)))
#         
#         (_, (_, name, new)) = new
#         
#         wi = next((x for x in self.workflow if obj in x.views))
#         idx = self.workflow.index(wi)
#         self.message_q.put((Msg.UPDATE_VIEW, (idx, obj.id, name, new)))
#         self.modified = True
        
    @on_trait_change('workflow:current_view')
    def _on_current_view_changed(self, obj, name, old, new):
        logger.debug("LocalWorkflow._on_current_view_changed :: {}"
                      .format((obj, name, old, new)))                  
                  
        idx = self.workflow.index(obj)
        view = obj.current_view
        self.message_q.put((Msg.CHANGE_CURRENT_VIEW, (idx, view)))
        

    @on_trait_change('workflow:current_plot')
    def _on_current_plot_changed(self, obj, name, old, new):
        logger.debug("LocalWorkflow._on_current_plot_changed :: {}"
                      .format((obj, name, old, new)))                  
                  
        idx = self.workflow.index(obj)
        plot = obj.current_plot
        self.message_q.put((Msg.CHANGE_CURRENT_PLOT, (idx, plot)))
        
        
    def remote_eval(self, expr):
        self.eval_event.clear()
        self.message_q.put((Msg.EVAL, expr))
        
        self.eval_event.wait()
        return self.eval_result


    def remote_exec(self, expr):
        self.exec_event.clear()
        self.message_q.put((Msg.EXEC, expr))
        
        self.exec_event.wait()
        return
    
    
    def wi_sync(self, wi, variable, value, timeout = 30):
        """Set WorkflowItem.status on the remote workflow, then wait for it to propogate here."""
        
        assert(wi.trait_get([variable])[variable] != value)
        idx = self.workflow.index(wi)
        self.remote_exec("self.workflow[{0}].trait_set({1} = '{2}')".format(idx, variable, value))
        
        self.wi_waitfor(wi, variable, value, timeout)
        
        
    def wi_waitfor(self, wi, variable, value, timeout = 30):
        """Waits a configurable amount of time for wi's status to change to status"""

        from traits.util.async_trait_wait import wait_for_condition  
        try:      
            wait_for_condition(lambda v: v.trait_get([variable])[variable] == value, wi, variable, timeout)
        except RuntimeError:
            logger.error("Timed out after {} seconds waiting for {} to become {}.\n"
                         "Current value: {}\n"
                         "WorkflowItem.op_error: {}\n"
                         "WorkflowItem.estimate_error: {}\n"
                         "WorkflowItem.view_error: {}"
                        .format(timeout, variable, value, 
                                wi.trait_get([variable])[variable],
                                wi.op_error,
                                wi.estimate_error,
                                wi.view_error))
            
            raise

        
    def shutdown_remote_process(self, remote_process):
        # tell the remote process to shut down
        self.message_q.put((Msg.SHUTDOWN, None))
        
        # the SHUTDOWN message stops the sending thread
        self.send_thread.join()
        
        # the reply from the remote process stops the receiving thread
        self.recv_thread.join()
        
        # make sure the remote process has shut down entirely
        remote_process.join()


class RemoteWorkflow(HasStrictTraits):
    workflow = List(WorkflowItem)
    selected = Instance(WorkflowItem)
    
    last_view_plotted = Instance(IWorkflowView)
    
    send_thread = Instance(threading.Thread)
    recv_thread = Instance(threading.Thread)
    message_q = Instance(Queue, ())
    
    # synchronization primitives for plotting
    matplotlib_events = Any
    plot_lock = Any
    
    exec_q = Instance(UniquePriorityQueue, ())
    exec_lock = Instance(threading.Lock, ())
    
    # for debugging
#     apply_calls = Int(0)
#     plot_calls = Int(0)
    
    def run(self, parent_workflow_conn, parent_mpl_conn, headless = False):
        
        # set up the plotting synchronization primitives
        self.matplotlib_events = threading.Event()
        self.plot_lock = threading.Lock()
        
        # configure matplotlib backend to use the pipe
        if headless:
            pass
        else:
            plt.new_figure_manager = lambda num, parent_conn = parent_mpl_conn, process_events = self.matplotlib_events, plot_lock = self.plot_lock, *args, **kwargs: \
                                        cytoflowgui.matplotlib_backend_remote.new_figure_manager(num, 
                                                                                          parent_conn = parent_conn, 
                                                                                          process_events = process_events,
                                                                                          plot_lock = plot_lock, 
                                                                                          *args, 
                                                                                          **kwargs)
         
        # start threads
        self.recv_thread = threading.Thread(target = self.recv_main, 
                             name = "remote recv thread",
                             args = [parent_workflow_conn])
        self.recv_thread.start()
        
        self.send_thread = threading.Thread(target = self.send_main,
                                            name = "remote send thread",
                                            args = [parent_workflow_conn])
        self.send_thread.start()
        
        # loop and process updates
        while True:
            try:
                _, (wi, fn) = self.exec_q.get()
                
                if wi:
                    with wi.lock:
                        fn()
                else:

                    if fn is None:
                        self.shutdown()
                        return
                    else:
                        fn()
                
                self.exec_q.task_done()

            except Exception:
                log_exception()

    def recv_main(self, parent_conn):
        while parent_conn.poll(None):
            try:
                (msg, payload) = parent_conn.recv()
            except EOFError:
                return
            
            logger.debug("RemoteWorkflow.recv_main :: {}".format((msg, payload)))
            
            try:
                if msg == Msg.NEW_WORKFLOW:
                    self.workflow = []
                    for new_item in payload:
                        idx = len(self.workflow)
                        wi = WorkflowItem(workflow = self)
                        wi.lock.acquire()
                        wi.matplotlib_events = self.matplotlib_events
                        wi.plot_lock = self.plot_lock
                        wi.copy_traits(new_item,
                                       status = lambda t: t is not True)
                        self.workflow.append(wi)                          

                    for wi in self.workflow:
                        wi.lock.release()
                        
                elif msg == Msg.RUN_ALL:
                    for wi in self.workflow:
                        wi.lock.acquire()
                        
                    for idx, wi in enumerate(self.workflow):
                        if hasattr(wi.operation, "estimate"):
                            self.exec_q.put((idx - 0.5, (wi, wi.estimate)))

                        self.exec_q.put((idx, (wi, wi.apply)))  
                        
                    for wi in self.workflow:
                        wi.lock.release()
                        
    
                elif msg == Msg.ADD_ITEMS:
                    (idx, new_item) = payload
                    wi = WorkflowItem(workflow = self)
                    wi.lock.acquire()
                    wi.copy_traits(new_item)
                    wi.matplotlib_events = self.matplotlib_events
                    wi.plot_lock = self.plot_lock
                    
                    self.workflow.insert(idx, wi)
                    self.exec_q.put((idx, (wi, wi.apply)))
                    wi.lock.release()
    
                elif msg == Msg.REMOVE_ITEMS:
                    idx = payload
                    self.workflow.remove(self.workflow[idx])
                    
                elif msg == Msg.SELECT:
                    idx = payload
                    if idx == -1:
                        self.selected = None
                    else:
                        self.selected = self.workflow[idx]
                    
                elif msg == Msg.UPDATE_OP:
                    (idx, name, new) = payload
                    wi = self.workflow[idx]
                    with wi.lock:
                        if wi.operation.trait(name).status:
                            raise RuntimeError("Tried to set a remote status trait")
                        
                        if wi.operation.trait(name).fixed:
                            raise RuntimeError("Tried to set a remote fixed trait")
                        
                        if wi.operation.trait(name).transient:
                            raise RuntimeError("Tried to set a remote transient trait")
                        
                        wi.operation.trait_set(**{name : new})
                        
                elif msg == Msg.UPDATE_VIEW:
                    (idx, view_id, name, new) = payload
                    wi = self.workflow[idx]
                    try:
                        view = next((x for x in wi.views if x.id == view_id))
                    except StopIteration:
                        logger.warn("RemoteWorkflow: Couldn't find view {}".format(view_id))
                        continue
                    
                    with wi.lock:
                        if view.trait(name).status:
                            raise RuntimeError("Tried to set a remote status trait")
                        
                        if view.trait(name).fixed:
                            raise RuntimeError("Tried to set a remote fixed trait")
                        
                        if view.trait(name).transient:
                            raise RuntimeError("Tried to set a remote transient trait")
                        
                        view.trait_set(**{name : new})

                elif msg == Msg.CHANGE_CURRENT_VIEW:
                    (idx, view) = payload
                    wi = self.workflow[idx]
                    try:
                        wi.current_view = next((x for x in wi.views if x.id == view.id))
                    except StopIteration:
                        wi.views.append(view)
                        wi.current_view = view
                                                
                elif msg == Msg.CHANGE_CURRENT_PLOT:
                    (idx, plot) = payload
                    wi = self.workflow[idx]
                    wi.current_plot = plot
                    
                elif msg == Msg.ESTIMATE:
                    idx = payload
                    wi = self.workflow[idx]
                    self.exec_q.put((idx - 0.5, (wi, wi.estimate)))
                    
                elif msg == Msg.SHUTDOWN:
                    # tell the parent process to shut down
                    self.exec_q.put((len(self.workflow) + 1, (None, None)))
                    
                    # exit the receiving thread
                    return
                    
                elif msg == Msg.EXEC:
                    self.exec_q.put((sys.maxsize - 1, (None, lambda self = self, q = self.message_q, expr = payload: q.put((Msg.EXEC, exec(expr))))))
                                             
                elif msg == Msg.EVAL:
                    self.exec_q.put((sys.maxsize, (None, lambda self = self, q = self.message_q, expr = payload: q.put((Msg.EVAL, eval(expr))))))
                        
                else:
                    raise RuntimeError("Bad command in the remote workflow")
            
            except Exception:
                log_exception()
            
    def send_main(self, parent_conn):
        try:
            while True:
                msg = self.message_q.get()
                parent_conn.send(msg)
                
                if msg[0] == Msg.SHUTDOWN:
                    return
                    
        except Exception:
            log_exception()
            
            
    def shutdown(self):
        # make sure the receiving thread is shut down
        self.recv_thread.join()
        
        # shut down the sending thread
        self.message_q.put((Msg.SHUTDOWN, 0))
        self.send_thread.join()
        
            
    @on_trait_change('workflow_items', post_init = True)
    def _on_workflow_add_remove_items(self, event):
        logger.debug("RemoteWorkflow._on_workflow_add_remove_items :: {}"
                      .format((event.index, event.removed, event.added)))
            
        idx = event.index

        # remove deleted items from the linked list
        if event.removed:
            assert len(event.removed) == 1
            removed = event.removed[0]
            if removed.previous_wi:
                removed.previous_wi.next_wi = removed.next_wi
                
            if removed.next_wi:
                removed.next_wi.previous_wi = removed.previous_wi
                
                # invalidate following wi's
                removed.next_wi.changed = (Changed.PREV_RESULT, None)
        
        # add new items to the linked list
        if event.added:
            assert len(event.added) == 1
            if idx > 0:
                self.workflow[idx - 1].next_wi = self.workflow[idx]
                self.workflow[idx].previous_wi = self.workflow[idx - 1]
                
            if idx < len(self.workflow) - 1:
                self.workflow[idx].next_wi = self.workflow[idx + 1]
                self.workflow[idx + 1].previous_wi = self.workflow[idx]
                
                # invalidate following wi's
                self.workflow[idx + 1].changed = (Changed.PREV_RESULT, None)                
            
    @on_trait_change('workflow:operation:+', post_init = True)
    def _operation_changed(self, obj, name, old, new):
        """Translate changes in op traits to wi change events"""
        logger.debug("RemoteWorkflow._operation_changed :: {}"
                      .format((obj, name, old, new)))
        
        wi = next((x for x in self.workflow if obj == x.operation))
        
        if name == "changed":
            raise RuntimeError("This should be handled below!")
        elif obj.trait(name).estimate:
            wi.changed = (Changed.ESTIMATE, (name, new))
        elif obj.trait(name).status:
            wi.changed = (Changed.OP_STATUS, (name, new))
        elif obj.trait(name).operation:
            wi.changed = (Changed.OPERATION, (name, new))
        elif obj.trait(name).transient:
            return
        else:
            wi.changed = (Changed.OPERATION, (name, new))
            
#     @on_trait_change('workflow:operation:changed', post_init = True)
#     def _operation_change_event(self, obj, _, new):
#         logger.debug("RemoteWorkflow._operation_change_event :: {}"
#                       .format((obj, new)))
#         
#         wi = next((x for x in self.workflow if obj == x.operation))
#         wi.changed = new
            
            
    @on_trait_change('workflow:views:+', post_init = True)
    def _view_changed(self, obj, name, new):
        """Translate changes in view traits to wi change events"""
        logger.debug("RemoteWorkflow._view_changed :: {}"
                      .format((obj, name, new)))
        
        wi = next((x for x in self.workflow if obj in x.views))
        
        if name == "changed":
            raise RuntimeError("This should be handled elsewhere")
        elif obj.trait(name).transient:
            return
        elif obj.trait(name).status:
            wi.changed = (Changed.VIEW_STATUS, (obj, name, new))
        else:
            wi.changed = (Changed.VIEW, (obj, name, new))
            
#     @on_trait_change('workflow:changed')
#     def _changed_event(self, obj, name, new):
#         logger.debug("RemoteWorkflow._changed_event:: {}"
#                       .format((obj, name, new)))
#         
#         wi = obj
#         idx = self.workflow.index(wi)
#         (msg, payload) = new
#         
#         if msg == Changed.OPERATION:
#             if wi.operation.should_apply(Changed.OPERATION, payload):
#                 with wi.lock:
#                     wi.result = None
#                     wi.status = "invalid"
#                 self.exec_q.put((idx, (wi, wi.apply)))
#         
#         elif msg == Changed.VIEW:
#             (view, name, new) = payload
#             if wi.current_view == view and wi.current_view.should_plot(Changed.VIEW, payload):
#                 wi.current_view.update_plot_names(wi)
#                 self.exec_q.put((idx - 0.1, (wi, wi.plot)))
#                 
#         elif msg == Changed.ESTIMATE:
#             if wi.operation.should_clear_estimate(Changed.ESTIMATE, payload):
#                 try:
#                     wi.operation.clear_estimate()
#                 except AttributeError:
#                     pass
#         
#         elif msg == Changed.ESTIMATE_RESULT:
#             if (wi == self.selected 
#                 and wi.current_view 
#                 and wi.current_view.should_plot(Changed.ESTIMATE_RESULT, payload)):
#                 wi.current_view.update_plot_names(wi)
#                 self.exec_q.put((idx - 0.1, (wi, wi.plot)))
#                 
#             if wi.operation.should_apply(Changed.ESTIMATE_RESULT, payload):
#                 self.exec_q.put((idx, (wi, wi.apply)))
#                         
#         elif msg == Changed.OP_STATUS:
#             (name, new) = payload
#             self.message_q.put((Msg.UPDATE_OP, (idx, name, new)))
#             
#         elif msg == Changed.VIEW_STATUS:
#             (view, name, new) = payload
#             self.message_q.put((Msg.UPDATE_VIEW, (idx, view.id, name, new)))
#             
#         elif msg == Changed.RESULT:
#             if (wi == self.selected 
#                 and wi.current_view 
#                 and wi.current_view.should_plot(Changed.RESULT, payload)):
#                 wi.current_view.update_plot_names(wi)
#                 self.exec_q.put((idx - 0.1, (wi, wi.plot)))
#                 
#         elif msg == Changed.PREV_RESULT:
#             if wi.operation.should_clear_estimate(Changed.PREV_RESULT, payload):
#                 try:
#                     wi.operation.clear_estimate()
#                 except AttributeError:
#                     pass
#                 
#             if wi.operation.should_apply(Changed.PREV_RESULT, payload):
#                 with wi.lock:
#                     wi.result = None
#                     wi.status = "invalid"
#                 self.exec_q.put((idx, (wi, wi.apply)))
#                 
#             if (wi == self.selected 
#                 and wi.current_view 
#                 and wi.current_view.should_plot(Changed.PREV_RESULT, payload)):
#                 wi.current_view.update_plot_names(wi)
#                 self.exec_q.put((idx - 0.1, (wi, wi.plot)))

    @on_trait_change('workflow:+', post_init = True)
    def _workflow_item_changed(self, obj, name, old, new):
        logger.debug("RemoteWorkflow._workflow_item_changed :: {}"
                      .format((obj, name, old, new)))
             
        idx = self.workflow.index(obj)
        if obj.trait(name).status:            
            self.message_q.put((Msg.UPDATE_WI, (idx, name, new)))

            
    @on_trait_change('workflow:result', post_init = True)
    def _result_changed(self, obj, name, old, new):
        logger.debug("RemoteWorkflow._result_changed :: {}"
                      .format((self, obj, name, old, new)))   
             
        if obj.result:
            obj.channels = list(obj.result.channels)
            obj.conditions = dict(obj.result.conditions)
            obj.statistics = dict(obj.result.statistics)
 
            # some things in metadata are unpicklable, functions and such,
            # so filter them out.
            obj.metadata = filter_unpicklable(dict(obj.result.metadata))
            
        obj.changed = (Changed.RESULT, None)
        
        if obj.next_wi:
            obj.next_wi.changed = (Changed.PREV_RESULT, None)
            
             
    @on_trait_change('workflow:current_view, workflow:current_view:current_plot', post_init = True)
    def _current_view_changed(self, obj, name, old, new):
        logger.debug("RemoteWorkflow._current_view_changed :: {}"
                      .format((self, obj, name, old, new)))
        
        if obj == self.selected:
            idx = self.workflow.index(obj)
            obj.current_view.update_plot_names(obj)
            self.exec_q.put((idx + 0.1, (obj, obj.plot)))
        
            
    @on_trait_change('selected', post_init = True)
    def _selected_changed(self, obj, name, new):
        logger.debug("RemoteWorkflow._selected_changed :: {}"
                      .format((self, obj, name, new)))
        
        if new:
            idx = self.workflow.index(new)
            if new.current_view:
                new.current_view.update_plot_names(new)
                self.exec_q.put((idx + 0.1, (new, new.plot)))
        
#             
#     @on_trait_change('workflow:apply_called')
#     def _apply_called(self):
#         self.apply_calls += 1
#         self.message_q.put((Msg.APPLY_CALLED, self.apply_calls))
#         
#         
#     @on_trait_change('workflow:plot_called')
#     def _plot_called(self):
#         self.plot_calls += 1
#         self.message_q.put((Msg.PLOT_CALLED, self.plot_calls))



    