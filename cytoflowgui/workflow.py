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

# threading AND multiprocessing, oh my!
import threading, sys

import warnings

import matplotlib.pyplot as plt

from traits.api import HasStrictTraits, Instance, List, on_trait_change
                       
from traitsui.api import View, Item, InstanceEditor, Spring, Label

import cytoflow
import cytoflow.utility as util

from cytoflowgui.vertical_notebook_editor import VerticalNotebookEditor
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.util import UniquePriorityQueue
#from cytoflowgui import matplotlib_multiprocess_backend

# THE NEW NEW PLAN combines both:
# The parent process runs the GUI
# The child process holds the data
# When a WI needs to run in the child process, it runs the operation
# in grandchild process, which sends back just the changed columns.
# threads are used to listen for status updates, passed back as new
# WI instances (though we'll have to break the update loop somewhere!)

# THE NEW PLAN: when a WorkflowItem runs, it will kick off a new process.
# that new process will be passed the previous WI's result and the 
# operation (which should be FAST because of process cloning, at least on
# Linux and Mac.) the new process will run the operation on the data,
# collect the result, then do a column-by-column comparison of the two
# and send new and changed columns back to the parent process.  the 
# parent process's WI will construct a result out of the previous WI's
# result and the changed columns from the child process.

# THE OLD PLAN:
# (the old plan has problems with orphaned processes.)

# multiprocessing and multithreading plan:

# the parent process maintains the GUI and a copy of the model but with 
# NO DATA.  all the actual data processing happens in a child process, 
# which maintains its own list of WorkflowItems that actually have the
# data and do the processing.

# 

# pair of child 
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
# motivation for multiprocessing: when a long-running operation is
# running, it holds the Python global interpreter lock (GIL) and thus
# freezes the GUI.

# pipe connections for communicating between canvases
# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.parent_conn = None
this.child_conn = None

class Msg:
    NEW_WORKFLOW = 0
    ADD_ITEMS = 1
    REMOVE_ITEMS = 2
    SELECT = 3
    UPDATE_OP = 4
    UPDATE_VIEW = 5
    CHANGE_CURRENT_VIEW = 6
    UPDATE_WI = 7

                    
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
        threading.Thread(target = self.listen_for_remote, args = ()).start()

    def listen_for_remote(self):
        while True:
            (msg, payload) = this.child_conn.recv()
            print "local msg: {}".format(msg)
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
        self.selected = None
        
        for wi in self.workflow:
            wi.status = "invalid"
        
        # send the new workflow to the child process
        this.child_conn.send((Msg.NEW_WORKFLOW, self.workflow))
        
        
    @on_trait_change('workflow_items')
    def _on_workflow_add_remove_items(self, event):
        #print "workflow items changed"
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
        # TODO - handle closing all the WIs
        idx = self.workflow.index(new)
        this.child_conn.send((Msg.SELECT, idx))   
    
    @on_trait_change('workflow:operation:-transient')
    def _on_operation_trait_changed(self, obj, name, old, new):
        print "local operation changed {}".format((name, old, new))
        wi = next((x for x in self.workflow if x.operation == obj))
        idx = self.workflow.index(wi)
        this.child_conn.send((Msg.UPDATE_OP, (idx, name, new)))
        
    @on_trait_change('workflow:current_view')
    def _on_current_view_changed(self, obj, name, old, new):
        idx = self.workflow.index(obj)
        view = obj.current_view
        this.child_conn.send((Msg.CHANGE_CURRENT_VIEW, (idx, view)))
        
    @on_trait_change('workflow:views:-transient')
    def _on_view_trait_changed(self, obj, name, old, new):
        print "local view changed {}".format((name, old, new))
        wi = next((x for x in self.workflow if obj in x.views))
        idx = self.workflow.index(wi)
        view_id = obj.id
        this.child_conn.send((Msg.UPDATE_VIEW, (idx, view_id, name, new)))

    # MAGIC: called when default_scale is changed
    def _default_scale_changed(self, new_scale):
        cytoflow.set_default_scale(new_scale)

        
class RemoteWorkflow(HasStrictTraits):
    
    workflow = List(WorkflowItem)
    update_queue = Instance(UniquePriorityQueue, ())
    selected = Instance(WorkflowItem)
    
    def run(self):
        # plt.ioff()
        threading.Thread(target = self._process_queue, args = ()).start()

        while True:
            (msg, payload) = this.parent_conn.recv()
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
                self.selected = self.workflow[idx]
                
            elif msg == Msg.UPDATE_OP:
                (idx, trait, new_value) = payload
                wi = self.workflow[idx]
                if wi.operation.trait_get(trait)[trait] != new_value:
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
                view = next((x for x in wi.views if x.id == view_id))
                if view.trait_get(trait)[trait] != new_value:
                    view.trait_set(**{trait : new_value})
                
            else:
                raise RuntimeError("Bad command in the remote workflow")
            
    def _process_queue(self):
        while True:
            _, wi = self.update_queue.get()
            wi.update()
        
    @on_trait_change('workflow')
    def _on_new_workflow(self, obj, name, old, new):        
        for wi in self.workflow:
            wi.status = "invalid"
            self.update_queue.put_nowait((self.workflow.index(wi), wi))
            
            
    @on_trait_change('workflow_items')
    def _on_workflow_add_remove_items(self, event):
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


    @on_trait_change('workflow:[status,channels,conditions,conditions_names,conditions_values,error,warning]')
    def _on_workflow_item_status_changed(self, obj, name, old, new):
        idx = self.workflow.index(obj)
        this.parent_conn.send((Msg.UPDATE_WI, (idx, name, new)))
            
        
    @on_trait_change('workflow:operation:-transient')
    def _on_operation_trait_changed(self, obj, name, old, new):
        print "remote operation changed {}".format((name, old, new))

        wi = next((x for x in self.workflow if x.operation == obj))
        idx = self.workflow.index(wi)
        this.parent_conn.send((Msg.UPDATE_OP, (idx, name, new)))

        for wi in self.workflow[idx:]:
            wi.status = "invalid"
            self.update_queue.put_nowait((self.workflow.index(wi), wi))
        
  
    @on_trait_change('workflow:views:-transient')
    def _on_view_trait_changed(self, obj, name, old, new):
        print "remote view changed {}".format((name, old, new))

        wi = next((x for x in self.workflow if obj in x.views))
        idx = self.workflow.index(wi)
        this.parent_conn.send((Msg.UPDATE_VIEW, (idx, obj.id, name, new)))

        if wi == self.selected and wi.current_view == obj:
            self.plot(wi)
            
    @on_trait_change('workflow:views:[error,warning]')
    def _on_view_status_changed(self, obj, name, old, new):
        wi = next((x for x in self.workflow if obj in x.views))
        idx = self.workflow.index(wi)
        this.parent_conn.send((Msg.UPDATE_VIEW, (idx, obj.id, name, new)))

            
    def plot(self, wi):
        print "remote plot"
        
        wi.current_view.warning = ""
        wi.current_view.error = ""
         
        with warnings.catch_warnings(record = True) as w:
            try:
                wi.current_view.plot_wi(wi)
                 
                # the remote canvas/pyplot interface of the multiprocess backend
                # is NOT interactive.  this call lets us batch together all 
                # the plot updates
                plt.show()
                 
                if w:
                    wi.current_view.warning = w[-1].message.__str__()
            except util.CytoflowViewError as e:
                wi.current_view.error = e.__str__()                

