#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflowgui.workflow.workflow
-----------------------------

The main model for the GUI.

At its core, the model is a list of `WorkflowItem` instances.  A `WorkflowItem`
wraps an operation, its completion status, the result of applying it to
the previous `WorkflowItem`'s result, and `IView`'s on that result.  The Workflow
also maintains a "current" or selected WorkflowItem.

The left panel of the GUI is a View on this object (viewing the list of
WorkflowItem instances), and the right panel of the GUI is a View of the
selected WorkflowItem's current view.

So far, so simple.  However, in a single-threaded GUI application, the UI
freezes when something processor-intensive is happening.  Adding another thread
doesn't help matters because of the CPython global interpreter lock; while
Python is otherwise computing, the GUI doesn't update.  To solve this, the 
Workflow maintains a copy of itself in a separate process.  The `LocalWorkflow`
is the one that is viewed by the GUI; the `RemoteWorkflow` is the one that
actually loads the data and does the processing.  Thus the GUI remains
responsive.  Changed attributes in either Workflow are noticed by a set of 
Traits handlers, which send those changes to the other process.

This process is also where the plotting happens.  For an explanation of how
the plots are ferried back to the GUI, see the module docstring for
`cytoflowgui.matplotlib_backend_local` and `cytoflowgui.matplotlib_backend_remote`
"""

'''
Data & control flow notes: 

When a local operation trait changes (with the metadata "apply" or "estimate")
1. Handler in local workflow notices
2. Trait is sent to remote workflow
3. Remote operation trait is updated
4. If the trait has metadata "apply":
   4a. Handler in remote workflow notices the updated operation trait
   4b. Handler asks operation "should I call "apply?"
   4c. If yes, handler adds an apply() call to the execution queue.
5. If the trait has metadata "estimate":
   5a. Handler in remote workflow notices the updated operation trait
   5b: Handler asks the operation "should I clear the estimate?"
   5c: If yes, handler calls operation.clear_estimate()

When a remote operation trait changes (with the metadata "status")
1. Handler in remote workflow notices
2. Trait is sent to local workflow
3. Local trait is updated
4. UI notices and reacts

When the "Estimate" button is pressed
1. The Controller fires the operation's "do_estimate" event
2. The dedicated local workflow handler notices
3. The local workflow sends an ESTIMATE message to the remote workflow
4. The remote workflow adds a call to estimate() to its execution queue

When a WorkflowItem's result changes
1. The handler in the remote workflow notices
2. It updates the WorkflowItem's channels, conditions, statistics, metadata
3. It asks the current view "should I plot?"
   3a. If yes, adds a call to plot() to the execution queue

When the previous WorkflowItem's result changes
1. The handler in the remote workflow notices
2. It asks the current operation if the estimate should be cleared?
   2a. If yes, clear the estimate
3. It asks the current operation if it should re-apply?
   3a. If yes, sets the WI status to Invalid" and adds a call to apply() to the execution queue
4. It asks if the current view should re-plot?
   4a. If yes, adds a call to plot() to the execution queue

When a remote operation trait changes (with the metadata estimate_result)
1. The handler in the remote workflow notices
2. If the operation's WorkflowItem is the current item and it has a current view:
   2a. Ask if the view should update
   2b. If yes, add a call to plot() to the execution queue
3. Ask the operation if it should apply?
   3a. If yes, add a call to apply() to the execution queue

When a local view trait changes 
1. Handler in the local workflow notices
2. Trait is sent to remote workflow
3. Remote view instance trait is updated
4. Remote workflow handler notices
5. If the WorkflowInstance is the selected one, and the view is the current view:
   5a. Asks if the view should plot?
   5b. If yes, adds the plot call to the execution queue

'''

import sys, threading, logging

from queue import Queue, PriorityQueue

from traits.api import (HasStrictTraits, Int, Bool, Instance, Any, List,
                        observe, ComparisonMode)

import matplotlib.pyplot as plt
import cytoflowgui.matplotlib_backend_remote

from cytoflowgui.utility import log_exception

from .workflow_item import WorkflowItem
from .views import IWorkflowView
from . import Changed

logger = logging.getLogger(__name__)

class Msg(object):
    """ Messages passed between the local and remote workflows"""
    
    # make an entirely new workflow. payload: 
    # - a list of WorkflowItems
    NEW_WORKFLOW = "NEW_WORKFLOW"
    
    # add an item to the remote workflow. payload:
    # - the index of the new workflow item
    # - the workflow item itself
    ADD_ITEMS = "ADD_ITEMS"
    
    # remove a workflow item. payload:
    # - the index of the item to remove
    REMOVE_ITEMS = "REMOVE_ITEMS"
    
    # update which workflow item is selected. payload:
    # - the index of the selected workflow item
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
    """Recursively filter unpicklable items from lists and dictionaries"""
    
    if type(obj) is list:
        return [filter_unpicklable(x) for x in obj]
    elif type(obj) is dict:
        return {x: filter_unpicklable(obj[x]) for x in obj}
    else:
        if not hasattr(obj, '__getstate__') and not isinstance(obj,
                  (str, int, float, tuple, list, set, dict)):
            return "Unpicklable: {}".format(type(obj))
        else:
            return obj

    

class LocalWorkflow(HasStrictTraits):
    """
    The workflow that is maintained in the "local" process -- ie, the same one that
    showing a GUI.
    """
    
    workflow = List(WorkflowItem, comparison_mode = ComparisonMode.identity)
    """The list of `WorkflowItem`\s"""
    
    selected = Instance(WorkflowItem)
    """The currently-selected `WorkflowItem`"""
    
    modified = Bool
    """Has this workflow been modified since it was loaded?"""
    
    recv_thread = Instance(threading.Thread)
    """The `threading.Thread` that receives messages from the remote process"""
    
    send_thread = Instance(threading.Thread)
    """The `threading.Thread` that sends messages to the remote process"""
    
    message_q = Instance(Queue, ())
    """The `queue.Queue` of messages to send to the remote process"""
    
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
        """
        The method that runs in `recv_thread` to receive messages from the 
        remote process.
        """
        
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
        """
        The method that runs in `send_thread` to send messages from `message_q` to
        the remote process
        """
        
        try:
            while True:
                msg = self.message_q.get()
                
                if msg == None:
                    return
                
                child_conn.send(msg)
        except Exception:
            log_exception()

    def run_all(self):
        """
        Send the RUN_ALL message to the remote process
        """
        
        self.message_q.put((Msg.RUN_ALL, None))
       
    @observe('workflow')
    def _on_new_workflow(self, _):
        logger.debug("LocalWorkflow._on_new_workflow")
            
        self.selected = None
        
        # send the new workflow to the child process
        self.message_q.put((Msg.NEW_WORKFLOW, self.workflow)) 
        
    @observe('workflow:items')
    def _on_workflow_add_remove_items(self, event):
        logger.debug("LocalWorkflow._on_workflow_add_remove_items :: {}"
                      .format(event))

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
            
    @observe('selected')
    def _on_selected_changed(self, event):
        logger.debug("LocalWorkflow._on_selected_changed :: {}".format(event))
            
        if event.new is None:
            idx = -1
        else:
            idx = self.workflow.index(event.new)
            
        self.message_q.put((Msg.SELECT, idx))
        
        
    @observe('workflow:items:operation:[+apply,+estimate]')
    def _on_operation_changed(self, event):
        logger.debug("LocalWorkflow._operation_changed :: {}".format(event))
        
        if event.name == 'changed':
            event.name = event.new
            event.new = event.object.trait_get(event.name)[event.name]
        
        wi = next((x for x in self.workflow if x.operation is event.object))
        idx = self.workflow.index(wi)

        self.message_q.put((Msg.UPDATE_OP, (idx, event.name, event.new)))
        self.modified = True
        
        
    @observe('workflow:items:operation:do_estimate')
    def _on_estimate(self, event):
        logger.debug("LocalWorkflow._on_estimate :: {}".format(event))
        
        wi = next((x for x in self.workflow if x.operation is event.object))
        idx = self.workflow.index(wi)
        self.message_q.put((Msg.ESTIMATE, idx))
            

    @observe('workflow:items:views:items:+type')
    def _on_view_changed(self, event):
        logger.debug("LocalWorkflow._view_changed :: {}".format(event))

        if event.name == 'changed':
            event.name = event.new
            event.new = event.object.trait_get(event.name)[event.name]

        # filter out anything that's transient (like properties)     
        # in particular, delegate properties should NOT be sent.
        # they get sent over as an operation property and are properly
        # updated on the remote end (no need to set them to be transient)
        if (event.object.trait(event.name).transient or
            event.object.trait(event.name).status or
            event.object.trait(event.name).type == "delegate"):
            return

        wi = next((x for x in self.workflow if event.object in x.views))
        idx = self.workflow.index(wi)
            
        self.message_q.put((Msg.UPDATE_VIEW, (idx, event.object.id, event.name, event.new)))
        self.modified = True       
                 
    @observe('workflow:items:current_view')
    def _on_current_view_changed(self, event):
        logger.debug("LocalWorkflow._on_current_view_changed :: {}"
                      .format(event))                  
                  
        idx = self.workflow.index(event.object)
        view = event.object.current_view
        self.message_q.put((Msg.CHANGE_CURRENT_VIEW, (idx, view)))      
        
    def remote_eval(self, expr):
        """
        Evaluate an expression in the remote process and return the result
        """
        
        self.eval_event.clear()
        self.message_q.put((Msg.EVAL, expr))
        
        self.eval_event.wait()
        return self.eval_result

    def remote_exec(self, expr):
        """
        Execute an expression in the remote process and wait until it completes
        """
        
        self.exec_event.clear()
        self.message_q.put((Msg.EXEC, expr))
        
        self.exec_event.wait()
        return
    
    def wi_sync(self, wi, variable, value, timeout = 30):
        """
        Set `WorkflowItem.status` on the remote workflow, then wait for it to 
        propogate here.
        """
        
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
        """Shut down the remote process"""
        # tell the remote process to shut down
        self.message_q.put((Msg.SHUTDOWN, None))
        
        # the SHUTDOWN message stops the sending thread
        self.send_thread.join()
        
        # the reply from the remote process stops the receiving thread
        self.recv_thread.join()
        
        # make sure the remote process has shut down entirely
        remote_process.join()


class RemoteWorkflow(HasStrictTraits):
    """
    The workflow that is maintained in the "remote" process -- ie, the one that
    actually does the processing.
    """
    
    workflow = List(WorkflowItem, comparison_mode = ComparisonMode.identity)
    """The list of `WorkflowItem`'s """
    
    selected = Instance(WorkflowItem)
    """The currently-selected `WorkflowItem`"""
    
    last_view_plotted = Instance(IWorkflowView)
    """The last `IWorkflowView` that was plotted"""
    
    send_thread = Instance(threading.Thread)
    """The `threading.Thread` that sends messages to the local process"""
    
    recv_thread = Instance(threading.Thread)
    """The `threading.Thread` that receives messages from the local process"""
    
    message_q = Instance(Queue, ())
    """The `queue.Queue` of messages to send to the local process"""
    
    # synchronization primitives for plotting
    matplotlib_events = Any
    """`threading.Event` to synchronize matplotlib plotting across process boundaries"""

    plot_lock = Any
    """`threading.Lock` to synchronize matplotlib plotting across process boundaries"""
    
    exec_q = Instance(UniquePriorityQueue, ())
    exec_lock = Instance(threading.Lock, ())
    
    # for debugging
    apply_calls = Int(0)
    plot_calls = Int(0)
    
    def run(self, parent_workflow_conn, parent_mpl_conn = None):
        """
        The method that runs the main loop of the remote process
        """
        
        # set up the plotting synchronization primitives
        self.matplotlib_events = threading.Event()
        self.plot_lock = threading.Lock()
        
        # configure matplotlib backend to use the pipe
        if parent_mpl_conn:
            plt.new_figure_manager = lambda num, parent_conn = parent_mpl_conn, process_events = self.matplotlib_events, plot_lock = self.plot_lock, *args, **kwargs: \
                                        cytoflowgui.matplotlib_backend_remote.new_figure_manager(num, 
                                                                                          parent_conn = parent_conn, 
                                                                                          process_events = process_events,
                                                                                          plot_lock = plot_lock, 
                                                                                          constrained_layout = True,
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
        """
        The method that runs in the `recv_thread` to receive messages from
        the local process.
        """
        
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
                            self.exec_q.put((idx - 0.1, (wi, wi.estimate)))

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
                            raise RuntimeError("Tried to set remote status trait '{}'".format(name))
                        
                        if wi.operation.trait(name).fixed:
                            raise RuntimeError("Tried to set remote fixed trait '{}'".format(name))
                        
                        if wi.operation.trait(name).transient:
                            raise RuntimeError("Tried to set remote transient trait '{}'")
                        
                        wi.operation.trait_set(**{name : new})
                        
                elif msg == Msg.UPDATE_VIEW:
                    (idx, view_id, name, new) = payload
                    wi = self.workflow[idx]
                    try:
                        view = next((x for x in wi.views if x.id == view_id))
                    except StopIteration:
                        logger.warn("RemoteWorkflow: Couldn't find view '{}'".format(view_id))
                        continue
                    
                    with wi.lock:
                        if view.trait(name).status:
                            raise RuntimeError("Tried to set remote status trait '{}'".format(name))
                        
                        if view.trait(name).fixed:
                            raise RuntimeError("Tried to set remote fixed trait '{}'".format(name))
                        
                        if view.trait(name).transient:
                            raise RuntimeError("Tried to set remote transient trait '{}'".format(name))
                        
                        view.trait_set(**{name : new})

                elif msg == Msg.CHANGE_CURRENT_VIEW:
                    (idx, view) = payload
                    wi = self.workflow[idx]
                    try:
                        wi.current_view = next((x for x in wi.views if x.id == view.id))
                    except StopIteration:
                        if wi.default_view and view.id == wi.default_view.id:
                            wi.views.append(wi.default_view)
                            wi.current_view = wi.default_view
                        else:
                            wi.views.append(view)
                            wi.current_view = view
                                                
                elif msg == Msg.CHANGE_CURRENT_PLOT:
                    (idx, plot) = payload
                    wi = self.workflow[idx]
                    wi.current_plot = plot
                    
                elif msg == Msg.ESTIMATE:
                    idx = payload
                    wi = self.workflow[idx]
                    self.exec_q.put((idx - 0.1, (wi, wi.estimate)))
                    
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
        """
        The method that runs in `send_thread` to send messages to the
        local process.
        """
        
        try:
            while True:
                msg = self.message_q.get()
                parent_conn.send(msg)
                
                if msg[0] == Msg.SHUTDOWN:
                    return
                    
        except Exception:
            log_exception()
            
    def shutdown(self):
        """Shut down the remote process"""
        # make sure the receiving thread is shut down
        self.recv_thread.join()
        
        # shut down the sending thread
        self.message_q.put((Msg.SHUTDOWN, 0))
        self.send_thread.join()
        
    @observe('apply_calls', post_init = True)
    def _on_apply_called(self, _):
        self.message_q.put((Msg.APPLY_CALLED, self.apply_calls))
        
    @observe('plot_calls', post_init = True)
    def _on_plot_called(self, _):
        self.message_q.put((Msg.PLOT_CALLED, self.plot_calls))
        
    @observe('workflow:items', post_init = True)
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

        # add new items to the linked list
        if event.added:
            assert len(event.added) == 1
            if idx > 0:
                self.workflow[idx - 1].next_wi = self.workflow[idx]
                self.workflow[idx].previous_wi = self.workflow[idx - 1]
                
            if idx < len(self.workflow) - 1:
                self.workflow[idx].next_wi = self.workflow[idx + 1]
                self.workflow[idx + 1].previous_wi = self.workflow[idx]
    
    @observe('workflow:items:operation:+apply')
    def _on_operation_apply_changed(self, event):
        logger.debug("RemoteWorkflow._operation_apply_changed :: {}".format(event))
        
        assert(event.name != 'changed')

        wi = next((x for x in self.workflow if x.operation is event.object))
        idx = self.workflow.index(wi)
                
        if wi.operation.should_apply(Changed.APPLY, event):
            with wi.lock:
                wi.result = None
                wi.status = "invalid"
            self.exec_q.put((idx, (wi, wi.apply)))
                
    @observe('workflow:items:operation:+estimate')
    def _on_operation_estimate_changed(self, event):
        logger.debug("RemoteWorkflow._operation_estimate_changed :: {}".format(event))
        
        assert(event.name != 'changed')

        wi = next((x for x in self.workflow if x.operation is event.object))
        
        if wi.operation.should_clear_estimate(Changed.ESTIMATE, event):
            wi.operation.clear_estimate()
            
    @observe('workflow:items:operation:+estimate_result')
    def _on_estimate_result_changed(self, event):
        logger.debug("RemoteWorkflow._estimate_result_changed :: {}".format(event))
        
        wi = next((x for x in self.workflow if x.operation is event.object))
        idx = self.workflow.index(wi)
             
        if wi.operation.should_apply(Changed.ESTIMATE_RESULT, event):
            self.exec_q.put((idx, (wi, wi.apply)))
            
        if (wi == self.selected 
            and wi.current_view 
            and wi.current_view.should_plot(Changed.ESTIMATE_RESULT, event)):
            self.exec_q.put((idx + 0.1, (wi, wi.plot)))
                
    @observe('workflow:items:operation:+status')
    def _on_operation_status_changed(self, event):
        wi = next((x for x in self.workflow if x.operation is event.object))
        idx = self.workflow.index(wi)
        self.message_q.put((Msg.UPDATE_OP, (idx, event.name, event.new)))
        
    @observe('workflow:items:result', post_init = True)
    def _on_result_changed(self, event):
        logger.debug("RemoteWorkflow._result_changed :: {}".format(event))   
              
        wi = event.object
        idx = self.workflow.index(wi)

        if wi.result:
            wi.channels = list(wi.result.channels)
            wi.conditions = dict(wi.result.conditions)
            wi.statistics = dict(wi.result.statistics)
  
            # some things in metadata are unpicklable, functions and such,
            # so filter them out.
            wi.metadata = filter_unpicklable(dict(wi.result.metadata))
            
            if (wi == self.selected 
                and wi.current_view 
                and wi.current_view.should_plot(Changed.RESULT, event)):
                self.exec_q.put((idx + 0.1, (wi, wi.plot)))
                
            if wi.next_wi:
                next_wi = wi.next_wi
                next_idx = self.workflow.index(next_wi)
                if (next_wi is not None 
                    and next_wi.operation.should_clear_estimate(Changed.PREV_RESULT, event)):
                    next_wi.operation.clear_estimate()
                    
                if (next_wi is not None
                    and next_wi.operation.should_apply(Changed.PREV_RESULT, event)):
                    with next_wi.lock:
                        next_wi.result = None
                        next_wi.status = 'invalid'
                    self.exec_q.put((next_idx, (next_wi, next_wi.apply)))
                    
                if (next_wi == self.selected
                    and next_wi.current_view
                    and next_wi.current_view.should_plot(Changed.PREV_RESULT, event)):
                    self.exec_q.put((next_idx + 0.1), (wi, wi.plot))
             
    @observe('workflow:items:views:items:+type')
    def _on_view_changed(self, event):
        logger.debug("RemoteWorkflow._view_changed :: {}".format(event))
        
        assert(event.name != 'changed')
        
        # filter out anything that's transient (like properties)            
        if event.object.trait(event.name).transient:
            return
        
        view = event.object
        wi = next((x for x in self.workflow if view in x.views))
        idx = self.workflow.index(wi)
        
        if event.object.trait(event.name).status:
            self.message_q.put((Msg.UPDATE_VIEW, (idx, view.id, event.name, event.new)))
            return
        
        if (wi == self.selected 
            and wi.current_view == view 
            and wi.current_view.should_plot(Changed.VIEW, event)):
            self.exec_q.put((idx + 0.1, (wi, wi.plot)))     
            
    @observe('workflow:items:current_view')
    def _on_current_view_changed(self, event):
        logger.debug("RemoteWorkflow._current_view_changed :: {}".format(event))
        
        wi = event.object
        if wi == self.selected:
            idx = self.workflow.index(wi)
            self.exec_q.put((idx + 0.1, (wi, wi.plot)))
            
    @observe('workflow:items:+status', post_init = True)
    def _on_workflow_item_changed(self, event):
        logger.debug("RemoteWorkflow._workflow_item_changed :: {}".format(event))
              
        idx = self.workflow.index(event.object)
        self.message_q.put((Msg.UPDATE_WI, (idx, event.name, event.new)))
        
    @observe('selected', post_init = True)
    def _on_selected_workflowitem_changed(self, event):
        logger.debug("RemoteWorkflow._selected_changed :: {}".format(event))
         
        if event.new is None:
            plt.clf()
            plt.show()
        else:
            idx = self.workflow.index(event.new)
            if event.new.current_view:
                self.exec_q.put((idx + 0.1, (event.new, event.new.plot)))

    