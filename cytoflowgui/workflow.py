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

import threading, sys, logging, Queue

from traits.api import HasStrictTraits, Instance, List, on_trait_change, Str
                       
from traitsui.api import View, Item, InstanceEditor, Spring, Label

import cytoflow
import cytoflow.utility as util
from cytoflow.views import IView

from cytoflowgui.vertical_notebook_editor import VerticalNotebookEditor
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.util import UniquePriorityQueue
import cytoflowgui.util as guiutil

# pipe connections for communicating between processes
# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.parent_conn = None
this.child_conn = None

class Msg:
    NEW_WORKFLOW = "NEW_WORKFLOW"
    ADD_ITEMS = "ADD_ITEMS"
    REMOVE_ITEMS = "REMOVE_ITEMS"
    SELECT = "SELECT"
    UPDATE_OP = "UPDATE_OP"
    UPDATE_VIEW = "UPDATE_VIEW"
    CHANGE_CURRENT_VIEW = "CHANGE_CURRENT_VIEW"
    CHANGE_CURRENT_PLOT = "CHANGE_CURRENT_PLOT"
    UPDATE_WI = "UPDATE_WI"
    CHANGE_DEFAULT_SCALE = "CHANGE_DEFAULT_SCALE"
    ESTIMATE = "ESTIMATE"
    GET_LOG = "GET_LOG"

                    
class LocalWorkflow(HasStrictTraits):
    
    items = List(WorkflowItem)
    selected = Instance(WorkflowItem)

    default_scale = util.ScaleEnum
    
    # a view for the entire workflow's list of operations 
    # (by default, the left panel of the flow task)
    operations_traits = View(Item('items',
                                  editor = VerticalNotebookEditor(view = 'operation_traits',
                                                                  page_name = '.name',
                                                                  page_description = '.friendly_id',
                                                                  page_icon = '.icon',
                                                                  delete = True,
                                                                  page_deletable = '.deletable',
                                                                  selected = 'selected',
                                                                  scrollable = True,
                                                                  multiple_open = False),
                                show_label = False))

    # a view showing the selected workflow item's current view
    # (by default, the right panel of the flow task)
    selected_view_traits = View(Item('items',
                                     editor = InstanceEditor(view = 'current_view_traits'),
                                     style = 'custom',
                                     show_label = False),
                                Spring(),
                                Label("Default scale"),
                                Item('default_scale',
                                     show_label = False))
    
    # the view for the center pane
    plot_view = View(Item('selected',
                          editor = InstanceEditor(view = 'current_plot_view'),
                          style = 'custom',
                          show_label = False))
    
    recv_thread = Instance(threading.Thread)
    send_thread = Instance(threading.Thread)
    message_q = Instance(Queue.Queue, ())
    
    # the child log
    child_log = Str
    child_log_cond = Instance(threading.Condition, ())
    
    def __init__(self, **kwargs):
        super(LocalWorkflow, self).__init__(**kwargs)         
        self.recv_thread = threading.Thread(target = self.recv_main, 
                                            name = "local workflow recv",
                                            args = ())
        self.recv_thread.daemon = True
        self.recv_thread.start()
        
        self.send_thread = threading.Thread(target = self.send_main,
                                            name = "local workflow send",
                                            args = ())
        self.send_thread.daemon = True
        self.send_thread.start()


    def recv_main(self):
        while this.child_conn.poll(None):
            try:
                (msg, payload) = this.child_conn.recv()
            except EOFError:
                return
            
            logging.debug("LocalWorkflow.recv_main :: {}".format(msg))
            
            if msg == Msg.UPDATE_WI:
                (idx, new_wi) = payload
                wi = self.items[idx]
                wi.copy_traits(new_wi, status = True)
                    
            elif msg == Msg.UPDATE_OP:
                (idx, new_op, update_type) = payload
                wi = self.items[idx]
                wi.operation.copy_traits(new_op, 
                                         status = True,
                                         fixed = lambda t: t is not True)
                
                wi.operation.changed = update_type
                
            elif msg == Msg.UPDATE_VIEW:
                (idx, new_view, update_type) = payload
                view_id = new_view.id
                wi = self.items[idx]
                view = next((x for x in wi.views if x.id == view_id))
                view.copy_traits(new_view, 
                                 status = True,
                                 fixed = lambda t: t is not True)
                
                view.changed = update_type
                    
            elif msg == Msg.GET_LOG:
                with self.child_log_cond:
                    self.child_log = payload
                    self.child_log_cond.notify()
            else:
                raise RuntimeError("Bad message from remote")

    
    def send_main(self):
        while True:
            msg = self.message_q.get()
            this.child_conn.send(msg)
            
    def get_child_log(self):
        self.message_q.put((Msg.GET_LOG,"none"))
        with self.child_log_cond:
            while not self.child_log:
                self.child_log_cond.wait()
            child_log = self.child_log
            self.child_log = ""
        return child_log


    @on_trait_change('workflow')
    def _on_new_workflow(self, obj, name, old, new):
        logging.debug("LocalWorkflow._on_new_workflow")
            
        self.selected = None
#         
#         for wi in self.items:
#             wi.status = "invalid"
        
        # send the new workflow to the child process
        self.message_q.put((Msg.NEW_WORKFLOW, self.items))
        
        
    @on_trait_change('workflow_items')
    def _on_workflow_add_remove_items(self, event):
        logging.debug("LocalWorkflow._on_workflow_add_remove_items :: {}"
                      .format((event.index, event.removed, event.added)))

        idx = event.index

        # invalidate icons
#         for wi in self.items[idx:]:
#             wi.status = "invalid"
        
        # remove deleted items from the linked list
        if event.removed:
            assert len(event.removed) == 1
            removed = event.removed[0]
            if removed.previous:
                removed.previous.next = removed.next
                
            if removed.next:
                removed.next.previous = removed.previous
            
            self.message_q.put((Msg.REMOVE_ITEMS, idx))
            
            if removed == self.selected:
                self.selected = None

        
        # add new items to the linked list
        if event.added:
            assert len(event.added) == 1
            if idx > 0:
                self.items[idx - 1].next = self.items[idx]
                self.items[idx].previous = self.items[idx - 1]
                
            if idx < len(self.items) - 1:
                self.items[idx].next = self.items[idx + 1]
                self.items[idx + 1].previous = self.items[idx]
                
            self.message_q.put((Msg.ADD_ITEMS, (idx, event.added[0])))
 
    @on_trait_change('selected')
    def _on_selected_changed(self, obj, name, old, new):
        logging.debug("LocalWorkflow._on_selected_changed :: {}"
                      .format((obj, name, old, new)))
            
        if new is None:
            idx = -1
        else:
            idx = self.items.index(new)
            
        self.message_q.put((Msg.SELECT, idx))
        
    @on_trait_change('workflow:operation:changed')
    def _operation_changed(self, obj, name, new):
        logging.debug("LocalWorkflow._operation_changed :: {}"
                      .format(obj, new))
        
        if new == "api" or new == "estimate":         
            wi = next((x for x in self.items if x.operation == obj))
            idx = self.items.index(wi)
            self.message_q.put((Msg.UPDATE_OP, (idx, obj, new)))

    @on_trait_change('workflow:views:changed')
    def _view_changed(self, obj, name, new):
        logging.debug("LocalWorkflow._view_changed :: {}"
                      .format((obj, name, new)))
        
        if new == "api":
            wi = next((x for x in self.items if obj in x.views))
            idx = self.items.index(wi)
            self.message_q.put((Msg.UPDATE_VIEW, (idx, obj, new)))
        
    @on_trait_change('workflow:current_view')
    def _on_current_view_changed(self, obj, name, old, new):
        logging.debug("LocalWorkflow._on_current_view_changed :: {}"
                      .format((obj, name, old, new)))                  
                  
        idx = self.items.index(obj)
        view = obj.current_view
        self.message_q.put((Msg.CHANGE_CURRENT_VIEW, (idx, view)))

    @on_trait_change('workflow:current_plot')
    def _on_current_plot_changed(self, obj, name, old, new):
        logging.debug("LocalWorkflow._on_current_plot_changed :: {}"
                      .format((obj, name, old, new)))                  
                  
        idx = self.items.index(obj)
        plot = obj.current_plot
        self.message_q.put((Msg.CHANGE_CURRENT_PLOT, (idx, plot)))
        
    @on_trait_change('workflow:do_estimate')
    def _on_estimate(self, obj, name, old, new):
        logging.debug("LocalWorkflow._on_estimate :: {}"
                      .format((obj, name, old, new)))
        idx = self.items.index(obj)
        self.message_q.put((Msg.ESTIMATE, idx))

    # MAGIC: called when default_scale is changed
    def _default_scale_changed(self, new_scale):
        logging.debug("LocalWorkflow._default_scale_changed :: {}"
                      .format((new_scale)))
            
        cytoflow.set_default_scale(new_scale)
        self.message_q.put((Msg.CHANGE_DEFAULT_SCALE, new_scale))

        
class RemoteWorkflow(HasStrictTraits):
    
    workflow = List(WorkflowItem)
    update_queue = Instance(UniquePriorityQueue, ())
    selected = Instance(WorkflowItem)
    
    plot_lock = Instance(threading.Lock, ())
    last_view_plotted = Instance(IView)
    
    send_thread = Instance(threading.Thread)
    recv_thread = Instance(threading.Thread)
    message_q = Instance(Queue.Queue, ())
    
    def run(self):
        self.recv_thread = threading.Thread(target = self.recv_main, 
                             name = "remote recv thread",
                             args = ())
        self.recv_thread.daemon = True
        self.recv_thread.start()
        
        self.send_thread = threading.Thread(target = self.send_main,
                                            name = "remote send thread",
                                            args = ())
        self.send_thread.daemon = True
        self.send_thread.start()
        
        # loop and process updates
        while True:
            _, fn = self.update_queue.get()
            fn()
#             wi = fn.im_self
#             if wi == self.selected:
#                 self.plot(wi)
            

    def recv_main(self):
        while this.parent_conn.poll(None):
            try:
                (msg, payload) = this.parent_conn.recv()
            except EOFError:
                return
            
            logging.debug("RemoteWorkflow.recv_main :: {}".format(msg))
            
            if msg == Msg.NEW_WORKFLOW:
                self.items = payload

            elif msg == Msg.ADD_ITEMS:
                (idx, new_item) = payload
                self.items.insert(idx, new_item)

            elif msg == Msg.REMOVE_ITEMS:
                idx = payload
                self.items.remove(self.items[idx])
                
            elif msg == Msg.SELECT:
                idx = payload
                if idx == -1:
                    self.selected = None
                else:
                    self.selected = self.items[idx]
#                     self.plot(self.selected)
                
            elif msg == Msg.UPDATE_OP:
                (idx, new_op, update_type) = payload
                wi = self.items[idx]
                wi.operation.copy_traits(new_op, 
                                         status = lambda t: t is not True,
                                         fixed = lambda t: t is not True)
                
                wi.operation.changed = update_type
                
#                 if update_type == "api":
#                     for wi in self.items[idx:]:
#                         wi.reset()
#                         self.update_queue.put_nowait((self.items.index(wi), wi.update))
#                 elif update_type == "estimate":
#                     try:
#                         wi.operation.clear_estimate()
#                     except AttributeError:
#                         pass   
                    
            elif msg == Msg.UPDATE_VIEW:
                (idx, new_view, update_type) = payload
                view_id = new_view.id
                wi = self.items[idx]
                try:
                    view = next((x for x in wi.views if x.id == view_id))
                except StopIteration:
                    logging.warn("RemoteWorkflow: Couldn't find view {}".format(view_id))
                    continue
                
                view.copy_traits(new_view, 
                                 status = lambda t: t is not True,
                                 fixed = lambda t: t is not True) 
                
                view.changed = update_type
                
#                 if wi == self.selected:
#                     self.plot(wi)       

            elif msg == Msg.CHANGE_CURRENT_VIEW:
                (idx, view) = payload
                wi = self.items[idx]
                try:
                    wi.current_view = next((x for x in wi.views if x.id == view.id))
                except StopIteration:
                    wi.views.append(view)
                    wi.current_view = view
                
#                 if wi == self.selected:
#                     self.plot(wi)
                    
            elif msg == Msg.CHANGE_CURRENT_PLOT:
                (idx, plot) = payload
                wi = self.items[idx]
                wi.current_plot = plot
                
#                 if wi == self.selected:
#                     self.plot(wi)
                    
            elif msg == Msg.CHANGE_DEFAULT_SCALE:
                new_scale = payload
                cytoflow.set_default_scale(new_scale)
                
            elif msg == Msg.ESTIMATE:
                pass
#                 idx = payload
#                 self.update_queue.put_nowait((self.items.index(wi), wi.estimate))
#                 for wi in self.items[idx:]:
#                     wi.reset()
#                     if wi == self.items[idx]:
#                         self.update_queue.put_nowait((self.items.index(wi), wi.estimate))
#                     self.update_queue.put_nowait((self.items.index(wi) + 0.1, wi.update))
                
            elif msg == Msg.GET_LOG:
                self.message_q.put((Msg.GET_LOG, guiutil.child_log.getvalue()))

            else:
                raise RuntimeError("Bad command in the remote workflow")
            
            
    def send_main(self):
        while True:
            msg = self.message_q.get()
            this.parent_conn.send(msg)
            
        
#     @on_trait_change('workflow')
#     def _on_new_workflow(self, obj, name, old, new):     
#         logging.debug("RemoteWorkflow._on_new_workflow :: {}"
#                       .format((obj, name, old, new)))
#                
#         for wi in self.items:
#             wi.status = "invalid"
#             self.update_queue.put_nowait((self.items.index(wi), wi.update))
            
            
    @on_trait_change('workflow_items')
    def _on_workflow_add_remove_items(self, event):
        logging.debug("RemoteWorkflow._on_workflow_add_remove_items :: {}"
                      .format((event.index, event.removed, event.added)))
            
        idx = event.index

        # remove deleted items from the linked list
        if event.removed:
            assert len(event.removed) == 1
            removed = event.removed[0]
            if removed.previous:
                removed.previous.next = removed.next
                
            if removed.next:
                removed.next.previous = removed.previous
        
        # add new items to the linked list
        if event.added:
            assert len(event.added) == 1
            if idx > 0:
                self.items[idx - 1].next = self.items[idx]
                self.items[idx].previous = self.items[idx - 1]
                
            if idx < len(self.items) - 1:
                self.items[idx].next = self.items[idx + 1]
                self.items[idx + 1].previous = self.items[idx]
                
#         for wi in self.items[idx:]:
#             wi.status = "invalid"
#             self.update_queue.put_nowait((self.items.index(wi), wi.update))

    @on_trait_change('workflow:operation:changed')
    def _operation_changed(self, obj, name, new):
        logging.debug("LocalWorkflow._operation_changed :: {}"
                      .format(obj))
        
        
#         wi = next((x for x in self.items if x.operation == obj))
#         idx = self.items.index(wi)      
#            
#         if new == "status":
#             self.message_q.put((Msg.UPDATE_OP, (idx, obj, new)))
#         elif new == "estimate":
#             for wi in self.items[idx:]:
#                 wi.reset()            
#         elif new == "api":
#             for wi in self.items[idx:]:
#                 wi.reset()
#                 #wi.status = "invalid"
#                 self.update_queue.put_nowait((self.items.index(wi), wi.update))            
            
    @on_trait_change('workflow:views:changed')
    def _view_changed(self, obj, name, new):
        logging.debug("RemoteWorkflow._view_changed :: {}"
                      .format((obj, name, new)))
        
#         if new == "status":
#             wi = next((x for x in self.items if obj in x.views))
#             idx = self.items.index(wi)
#             self.message_q.put((Msg.UPDATE_VIEW, (idx, obj)))

    @on_trait_change('workflow:changed')
    def _workflow_item_changed(self, obj, name, old, new):
        logging.debug("RemoteWorkflow._on_workflow_item_changed :: {}"
                      .format((obj, name, old, new)))
            
        idx = self.items.index(obj)            
        self.message_q.put((Msg.UPDATE_WI, (idx, obj)))
        
#     @on_trait_change('workflow:operation:changed')
#     def _on_operation_changed(self, obj, name, old, new):
#         logging.debug("RemoteWorkflow._on_operation_changed :: {}"
#                       .format((obj, name, old, new))) 
#  
#         wi = next((x for x in self.items if x.operation == obj))
#         idx = self.items.index(wi)
#         
#         if wi.operation in self.updating:
#             return
#         
#         for wi in self.items[idx:]:
#             wi.status = "invalid"
#             self.update_queue.put_nowait((self.items.index(wi), wi))
     
#         # some traits don't need to trigger a re-apply
#         if not obj.trait(name).later and not obj.trait(name).status:
#             for wi in self.items[idx:]:
#                 wi.status = "invalid"
#                 self.update_queue.put_nowait((self.items.index(wi), wi))
#          
#         if (obj, name) in self.updating_traits:        
#             self.updating_traits.remove((obj, name))
#         else:
#             if name.endswith("_items"):
#                 name = name.replace("_items", "")
#                 new = obj.trait_get(name)[name]
#             self.message_q.put((Msg.UPDATE_OP, (idx, name, new)))        
        
#     @on_trait_change('workflow:operation:+status')
#     def _on_operation_trait_changed(self, obj, name, old, new):
#         logging.debug("RemoteWorkflow._on_operation_trait_changed :: {}"
#                       .format((obj, name, old, new))) 
#  
#         wi = next((x for x in self.items if x.operation == obj))
#         idx = self.items.index(wi)
# 
#         self.message_q.put((Msg.UPDATE_OP, (idx, obj)))

#      
#         # some traits don't need to trigger a re-apply
#         if not obj.trait(name).later and not obj.trait(name).status:
#             for wi in self.items[idx:]:
#                 wi.status = "invalid"
#                 self.update_queue.put_nowait((self.items.index(wi), wi))
#          
#         if (obj, name) in self.updating_traits:        
#             self.updating_traits.remove((obj, name))
#         else:
#             if name.endswith("_items"):
#                 name = name.replace("_items", "")
#                 new = obj.trait_get(name)[name]
#             self.message_q.put((Msg.UPDATE_OP, (idx, name, new)))

        
#     @on_trait_change('workflow:views:api')
#     def _on_view_trait_changed_plot(self, obj, name, old, new):
#         logging.debug("RemoteWorkflow._on_view_trait_changed_plot :: {}"
#                       .format((obj, name, old, new)))
#             
# #         # delegate traits are "implicitly" transient; they'll show up here
# #         # but not in _on_view_trait_changed_send_to_parent, below
# #         if not obj.trait(name).transient:      
#         wi = next((x for x in self.items if obj in x.views))
# # 
# #             if hasattr(obj, 'enum_plots'):
# #                 plot_names = list(obj.enum_plots(wi.result))
# #                 if plot_names == [None]:
# #                     plot_names = []
# #                     
# #                 if set(plot_names) != set(wi.current_view_plot_names):
# #                     wi.current_view_plot_names = plot_names
# #                     return
# 
#         if wi == self.selected and wi.current_view == obj:
#             self.plot(wi)


            
#     @on_trait_change('workflow:views:[error,warning]')
#     def _on_view_status_changed(self, obj, name, old, new):
#         logging.debug("RemoteWorkflow._on_view_status_changed :: {}"
#                       .format((obj, name, old, new)))
#             
#         if (obj, name) in self.updating_traits:
#             self.updating_traits.remove((obj, name))
#         else:
#             wi = next((x for x in self.items if obj in x.views))
#             idx = self.items.index(wi)
#             self.message_q.put((Msg.UPDATE_VIEW, (idx, obj.id, name, new)))
         
#     # if either selected or status changeds
#     @on_trait_change('selected.status')
#     def _on_operation_status_changed(self, obj, name, old, new):
#         logging.debug("RemoteWorkflow._on_operation_status_changed :: {}"
#                       .format((obj, name, old, new)))
# 
#         if self.selected is not None and new != "estimating" and new != "applying":
#             self.plot(self.selected)
#         else:
#             plt.clf()
#             plt.show()
#             
# 
#     def plot(self, wi):              
#         logging.debug("RemoteWorkflow.plot :: {}".format((wi)))
#             
#         if not wi.current_view:
#             plt.clf()
#             plt.show()
#             return
#         
#         wi.view_warning = ""
#         wi.view_error = ""
#          
#         with warnings.catch_warnings(record = True) as w:
#             try:
#                 with self.plot_lock:
#                     mpl_backend.process_events.clear()
# 
#                     wi.current_view.plot_wi(wi)
#                 
#                     if self.last_view_plotted and "interactive" in self.last_view_plotted.traits():
#                         self.last_view_plotted.interactive = False
#                      
#                     if "interactive" in wi.current_view.traits():
#                         wi.current_view.interactive = True
#                     self.last_view_plotted = wi.current_view
#                       
#                     # the remote canvas/pyplot interface of the multiprocess backend
#                     # is NOT interactive.  this call lets us batch together all 
#                     # the plot updates
#                     plt.show()
#                      
#                     mpl_backend.process_events.set()
#                  
#                 if w:
#                     wi.view_warning = w[-1].message.__str__()
#             except util.CytoflowViewError as e:
#                 wi.view_error = e.__str__()   
#                 plt.clf()
#                 plt.show()
#             except Exception as e:
#                 wi.view_error = e.__str__()   
#                 plt.clf()
#                 plt.show()                
             

