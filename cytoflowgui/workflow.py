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

import threading, sys, warnings

import matplotlib.pyplot as plt

from traits.api import HasStrictTraits, Instance, List, Set, on_trait_change
                       
from traitsui.api import View, Item, InstanceEditor, Spring, Label

import cytoflow
import cytoflow.utility as util
from cytoflow.views import IView

from cytoflowgui.vertical_notebook_editor import VerticalNotebookEditor
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.util import UniquePriorityQueue

# pipe connections for communicating between canvases
# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.parent_conn = None
this.child_conn = None

DEBUG = 1

class Msg:
    NEW_WORKFLOW = "NEW_WORKFLOW"
    ADD_ITEMS = "ADD_ITEMS"
    REMOVE_ITEMS = "REMOVE_ITEMS"
    SELECT = "SELECT"
    UPDATE_OP = "UPDATE_OP"
    UPDATE_VIEW = "UPDATE_VIEW"
    CHANGE_CURRENT_VIEW = "CHANGE_CURRENT_VIEW"
    UPDATE_WI = "UPDATE_WI"
    CHANGE_DEFAULT_SCALE = "CHANGE_DEFAULT_SCALE"

                    
class LocalWorkflow(HasStrictTraits):
    
    workflow = List(WorkflowItem)
    selected = Instance(WorkflowItem)

    default_scale = util.ScaleEnum
    
    # a view for the entire workflow's list of operations
    operations_traits = View(Item('workflow',
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
    selected_view_traits = View(Item('selected',
                                     editor = InstanceEditor(view = 'current_view_traits'),
                                     style = 'custom',
                                     show_label = False),
                                Spring(),
                                Label("Default scale"),
                                Item('default_scale',
                                     show_label = False))
    
    def __init__(self, **kwargs):
        super(LocalWorkflow, self).__init__(**kwargs)         
        t = threading.Thread(target = self.listen_for_remote, 
                             name = "workflow listen",
                             args = ())
        t.daemon = True
        t.start()

    def listen_for_remote(self):
        while this.child_conn.poll():
            try:
                (msg, payload) = this.child_conn.recv()
            except EOFError:
                return
            
            if DEBUG:
                print "LocalWorkflow.listen_for_remote :: {}".format(msg)
            
            if msg == Msg.UPDATE_WI:
                (idx, trait, new_value) = payload
                wi = self.workflow[idx]
                if wi.trait_get(trait)[trait] != new_value:
                    wi.trait_set(**{trait : new_value})
            elif msg == Msg.UPDATE_OP:
                (idx, trait, new_value) = payload
                wi = self.workflow[idx]
                if wi.operation.trait_get(trait)[trait] != new_value:
                    wi.operation.trait_set(**{trait : new_value})
            elif msg == Msg.UPDATE_VIEW:
                (idx, view_id, trait, new_value) = payload
                wi = self.workflow[idx]
                view = next((x for x in wi.views if x.id == view_id))
                
                if view.trait_get(trait)[trait] != new_value:
                    view.trait_set(**{trait : new_value})
            else:
                raise RuntimeError("Bad message from remote")

                    
    def add_operation(self, operation):
        # add the new operation after the selected workflow item or at the end
        # of the workflow if no wi is selected
        
        # make a new workflow item
        wi = WorkflowItem(operation = operation,
                          deletable = (operation.id != "edu.mit.synbio.cytoflow.operations.import"))

        # they say in Python you should ask for forgiveness instead of permission
        try:
            wi.default_view = operation.default_view()
            wi.views.append(wi.default_view)
        except AttributeError:
            pass

        if self.workflow and self.selected:
            idx = self.workflow.index(self.selected) + 1
        elif self.workflow:
            idx = len(self.workflow)
        else:
            idx = 0
            
        # the add_remove_items handler takes care of updating the linked list
        self.workflow.insert(idx, wi)
 
        # select (open) the new workflow item
        self.selected = wi
        if wi.default_view:
            wi.current_view = wi.default_view
            
            
    def set_current_view(self, view):
        try:
            self.selected.current_view = next((x for x in self.selected.views if x.id == view.id))
        except StopIteration:
            self.selected.views.append(view)
            self.selected.current_view = view


    @on_trait_change('workflow')
    def _on_new_workflow(self, obj, name, old, new):
        if DEBUG:
            print "LocalWorkflow._on_new_workflow"
            
        self.selected = None
        
        for wi in self.workflow:
            wi.status = "invalid"
        
        # send the new workflow to the child process
        this.child_conn.send((Msg.NEW_WORKFLOW, self.workflow))
        
        
    @on_trait_change('workflow_items')
    def _on_workflow_add_remove_items(self, event):
        if DEBUG:
            print("LocalWorkflow._on_workflow_add_remove_items :: {}"
                  .format((event.index, event.removed, event.added)))

        idx = event.index

        # invalidate icons
        for wi in self.workflow[idx:]:
            wi.status = "invalid"
        
        # remove deleted items from the linked list
        if event.removed:
            assert len(event.removed) == 1
            removed = event.removed[0]
            if removed.previous:
                removed.previous.next = removed.next
                
            if removed.next:
                removed.next.previous = removed.previous
            
            this.child_conn.send((Msg.REMOVE_ITEMS, idx))
            
            if removed == self.selected:
                self.selected = None

        
        # add new items to the linked list
        if event.added:
            assert len(event.added) == 1
            if idx > 0:
                self.workflow[idx - 1].next = self.workflow[idx]
                self.workflow[idx].previous = self.workflow[idx - 1]
                
            if idx < len(self.workflow) - 1:
                self.workflow[idx].next = self.workflow[idx + 1]
                self.workflow[idx + 1].previous = self.workflow[idx]
                
            this.child_conn.send((Msg.ADD_ITEMS, (idx, event.added[0])))
 
    @on_trait_change('selected')
    def _on_selected_changed(self, obj, name, old, new):
        if DEBUG:
            print("LocalWorkflow._on_selected_changed :: {}"
                  .format((obj, name, old, new)))
            
        if new is None:
            idx = -1
        else:
            idx = self.workflow.index(new)
            
        this.child_conn.send((Msg.SELECT, idx))   
    
    @on_trait_change('workflow:operation:-transient')
    def _on_operation_trait_changed(self, obj, name, old, new):
        if DEBUG:
            print("LocalWorkflow._on_operation_trait_changed :: {}"
                  .format((obj, name, old, new)))
        
        wi = next((x for x in self.workflow if x.operation == obj))
        idx = self.workflow.index(wi)
    
        if name.endswith("_items"):
            name = name.replace("_items", "")
            new = obj.trait_get(name)[name]

        this.child_conn.send((Msg.UPDATE_OP, (idx, name, new)))

        
    @on_trait_change('workflow:current_view')
    def _on_current_view_changed(self, obj, name, old, new):
        if DEBUG:
            print("LocalWorkflow._on_current_view_changed :: {}"
                  .format((obj, name, old, new)))                  
                  
        idx = self.workflow.index(obj)
        view = obj.current_view
        this.child_conn.send((Msg.CHANGE_CURRENT_VIEW, (idx, view)))
        
    @on_trait_change('workflow:views:-transient')
    def _on_view_trait_changed(self, obj, name, old, new):
        if DEBUG:
            print("LocalWorkflow._on_view_trait_changed :: {}"
                  .format((obj, name, old, new)))
    
        wi = next((x for x in self.workflow if obj in x.views))
        idx = self.workflow.index(wi)
        view_id = obj.id
        
        if name.endswith("_items"):
            name = name.replace("_items", "")
            new = obj.trait_get(name)[name]
        
        this.child_conn.send((Msg.UPDATE_VIEW, (idx, view_id, name, new)))

    # MAGIC: called when default_scale is changed
    def _default_scale_changed(self, new_scale):
        if DEBUG:
            print("LocalWorkflow._default_scale_changed :: {}"
                  .format((new_scale)))
            
        cytoflow.set_default_scale(new_scale)
        this.child_conn.send((Msg.CHANGE_DEFAULT_SCALE, new_scale))

        
class RemoteWorkflow(HasStrictTraits):
    
    workflow = List(WorkflowItem)
    update_queue = Instance(UniquePriorityQueue, ())
    selected = Instance(WorkflowItem)
    
    plot_lock = Instance(threading.Lock, ())
    last_view_plotted = Instance(IView)

    updating_traits = Set()
    
    def run(self):
        t = threading.Thread(target = self._process_queue, 
                             name = "workflow process queue",
                             args = ())
        t.daemon = True
        t.start()

        while this.parent_conn.poll():
            try:
                (msg, payload) = this.parent_conn.recv()
            except EOFError:
                return
            
            if DEBUG:
                print "RemoteWorkflow.run :: {}".format(msg)
            
            if msg == Msg.NEW_WORKFLOW:
                self.workflow = payload

            elif msg == Msg.ADD_ITEMS:
                (idx, new_item) = payload
                self.workflow.insert(idx, new_item)

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
                (idx, trait, new_value) = payload
                wi = self.workflow[idx]
                if wi.operation.trait_get(trait)[trait] != new_value:
                    self.updating_traits.add((wi.operation, trait))
                    wi.operation.trait_set(**{trait : new_value})

            elif msg == Msg.CHANGE_CURRENT_VIEW:
                (idx, view) = payload
                wi = self.workflow[idx]
                try:
                    wi.current_view = next((x for x in wi.views if x.id == view.id))
                except StopIteration:
                    wi.views.append(view)
                    wi.current_view = view
                
                if wi == self.selected:
                    self.plot(wi)
                
            elif msg == Msg.UPDATE_VIEW:
                (idx, view_id, trait, new_value) = payload
                wi = self.workflow[idx]
                try:
                    view = next((x for x in wi.views if x.id == view_id))
                except StopIteration as e:
                    #raise RuntimeError("RemoteWorkflow: Couldn't find view {}".format(view_id))
                    print "RemoteWorkflow: Couldn't find view {}".format(view_id)
                    continue
                    
                if view.trait_get(trait)[trait] != new_value:
                    self.updating_traits.add((view, trait))
                    view.trait_set(**{trait : new_value})
                    
            elif msg == Msg.CHANGE_DEFAULT_SCALE:
                new_scale = payload
                cytoflow.set_default_scale(new_scale)
                
            else:
                raise RuntimeError("Bad command in the remote workflow")
            
    def _process_queue(self):
        while True:
            _, wi = self.update_queue.get()
            wi.update()
        
    @on_trait_change('workflow')
    def _on_new_workflow(self, obj, name, old, new):     
        if DEBUG:
            print("RemoteWorkflow._on_new_workflow :: {}"
                  .format((obj, name, old, new)))
               
        for wi in self.workflow:
            wi.status = "invalid"
            self.update_queue.put_nowait((self.workflow.index(wi), wi))
            
    @on_trait_change('workflow_items')
    def _on_workflow_add_remove_items(self, event):
        if DEBUG:
            print("RemoteWorkflow._on_workflow_add_remove_items :: {}"
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
                self.workflow[idx - 1].next = self.workflow[idx]
                self.workflow[idx].previous = self.workflow[idx - 1]
                
            if idx < len(self.workflow) - 1:
                self.workflow[idx].next = self.workflow[idx + 1]
                self.workflow[idx + 1].previous = self.workflow[idx]
                
        for wi in self.workflow[idx:]:
            wi.status = "invalid"
            self.update_queue.put_nowait((self.workflow.index(wi), wi))

    @on_trait_change('workflow:operation:-transient')
    def _on_operation_trait_changed(self, obj, name, old, new):
        if DEBUG:
            print("RemoteWorkflow._on_operation_trait_changed :: {}"
                  .format((obj, name, old, new))) 

        wi = next((x for x in self.workflow if x.operation == obj))
        idx = self.workflow.index(wi)

        for wi in self.workflow[idx:]:
            wi.status = "invalid"
            self.update_queue.put_nowait((self.workflow.index(wi), wi))

        if (obj, name) in self.updating_traits:
            self.updating_traits.remove((obj, name))
        else:
            if name.endswith("_items"):
                name = name.replace("_items", "")
                new = obj.trait_get(name)[name]
            this.parent_conn.send((Msg.UPDATE_OP, (idx, name, new)))

        
    @on_trait_change('workflow:views:+')
    def _on_view_trait_changed_plot(self, obj, name, old, new):
        if DEBUG:
            print("RemoteWorkflow._on_view_trait_changed_plot :: {}"
                  .format((obj, name, old, new)))
            
        # delegate traits are "implicitly" transient; they'll show up here
        # but not in _on_view_trait_changed_send_to_parent, below
        if not obj.trait(name).transient:        
            wi = next((x for x in self.workflow if obj in x.views))
            if wi == self.selected and wi.current_view == obj:
                self.plot(wi)
            
    @on_trait_change('workflow:views:-transient')
    def _on_view_trait_changed_send_to_parent(self, obj, name, old, new):
        if DEBUG:
            print("RemoteWorkflow._on_view_trait_changed_send_to_parent :: {}"
                  .format((obj, name, old, new)))
            
        if (obj, name) in self.updating_traits:
            self.updating_traits.remove((obj, name))
        else:
            wi = next((x for x in self.workflow if obj in x.views))
            idx = self.workflow.index(wi)
            if name.endswith("_items"):
                name = name.replace("_items", "")
                new = obj.trait_get(name)[name]
            this.parent_conn.send((Msg.UPDATE_VIEW, (idx, obj.id, name, new)))

    @on_trait_change('workflow:[status,channels,conditions,conditions_types,conditions_values,error,warning]')
    def _on_workflow_item_status_changed(self, obj, name, old, new):
        if DEBUG:
            print("RemoteWorkflow._on_workflow_item_status_changed :: {}"
                  .format((obj, name, old, new)))
            
        idx = self.workflow.index(obj)
        
        if name.endswith("_items"):
            name = name.replace("_items", "")
            new = obj.trait_get(name)[name]
            
        this.parent_conn.send((Msg.UPDATE_WI, (idx, name, new)))
            
    @on_trait_change('workflow:views:[error,warning]')
    def _on_view_status_changed(self, obj, name, old, new):
        if DEBUG:
            print("RemoteWorkflow._on_view_status_changed :: {}"
                  .format((obj, name, old, new)))
            
        if (obj, name) in self.updating_traits:
            self.updating_traits.remove((obj, name))
        else:
            wi = next((x for x in self.workflow if obj in x.views))
            idx = self.workflow.index(wi)
            this.parent_conn.send((Msg.UPDATE_VIEW, (idx, obj.id, name, new)))
         
    # if either selected or status changeds
    @on_trait_change('selected.status')
    def _on_operation_status_changed(self, obj, name, old, new):
        if DEBUG:
            print("RemoteWorkflow._on_operation_status_changed :: {}"
                  .format((obj, name, old, new)))

        if self.selected is not None:
            self.plot(self.selected)
        else:
            plt.clf()
            plt.show()


    def plot(self, wi):      
        
        # TODO - replot if the selected wi changes!
        
        if DEBUG:
            print("RemoteWorkflow.plot :: {}"
                  .format((wi)))
            
        if not wi.current_view:
            plt.clf()
            plt.show()
            return
        
        wi.current_view.warning = ""
        wi.current_view.error = ""
         
        with warnings.catch_warnings(record = True) as w:
            try:
                with self.plot_lock:
                    wi.current_view.plot_wi(wi)
                
                if self.last_view_plotted and "interactive" in self.last_view_plotted.traits():
                    self.last_view_plotted.interactive = False
                
                if "interactive" in wi.current_view.traits():
                    wi.current_view.interactive = True
                self.last_view_plotted = wi.current_view
                 
                # the remote canvas/pyplot interface of the multiprocess backend
                # is NOT interactive.  this call lets us batch together all 
                # the plot updates
                plt.show()
                 
                if w:
                    wi.current_view.warning = w[-1].message.__str__()
            except util.CytoflowViewError as e:
                wi.current_view.error = e.__str__()   
                plt.clf()
                plt.show()
             

