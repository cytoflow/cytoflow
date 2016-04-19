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

from traits.api import HasStrictTraits, Instance, List, on_trait_change
                       
from traitsui.api import View, Item, InstanceEditor, Spring, Label

import cytoflow
import cytoflow.utility as util

from cytoflowgui.vertical_notebook_editor import VerticalNotebookEditor
from cytoflowgui.workflow_item import WorkflowItem
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
    UPDATE_OP = 3
    PLOT = 4
    
    OP_STATUS = 5
    VIEW_STATUS = 6
                    
class LocalWorkflow(HasStrictTraits):
    """
    A list of WorkflowItems.
    """
    
    selected = Instance(WorkflowItem)
    default_scale = util.ScaleEnum
    workflow = List(WorkflowItem)
    
    # a view for the entire workflow's list of operations
    operations_view = View(Item(name = 'workflow',
                                editor = VerticalNotebookEditor(view = 'operation_view',
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
    current_view_view = View(Item(name = 'selected',
                                  editor = InstanceEditor(view = "current_view_view"),
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
            if this.child_conn.poll(0.3):
                msg = this.child_conn.recv()
                if msg == Msg.OP_STATUS:
                    idx = this.child_conn.recv()
                    wi = self.workflow[idx]
                    wi.channels = this.child_conn.recv()
                    wi.conditions = this.child_conn.recv()
                    wi.conditions_names = this.child_conn.recv()
                    wi.warning = this.child_conn.recv()
                    wi.error = this.child_conn.recv()
                    wi.status = this.child_conn.recv()
                elif msg == Msg.VIEW_STATUS:
                    idx = this.child_conn.recv()
                    wi = self.workflow[idx]
                    view_id = this.child_conn.recv()
                    view = next((x for x in wi.views if x.id == view_id))
                    view.warning = this.child_conn.recv()
                    view.error = this.child_conn.recv()

    def add_operation(self, operation, default_view):
        # add the new operation after the selected workflow item or at the end
        # of the workflow if no wi is selected
        
        # make a new workflow item
        wi = WorkflowItem(operation = operation,
                          default_view = default_view,
                          deletable = (operation.id != "edu.mit.synbio.cytoflow.operations.import"))

        # set up the default view
        if wi.default_view is not None:
            wi.default_view.op = wi.operation
            wi.views.append(wi.default_view)
            
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
        this.child_conn.send(Msg.NEW_WORKFLOW)
        this.child_conn.send(self.workflow)
        
        
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
            
            this.child_conn.send(Msg.REMOVE_ITEMS)
            this.child_conn.send(idx)
        
        # add new items to the linked list
        if event.added:
            assert len(event.added) == 1
            if idx > 0:
                self.workflow[idx - 1].next = self.workflow[idx]
                self.workflow[idx].previous = self.workflow[idx - 1]
                
            if idx < len(self.workflow) - 1:
                self.workflow[idx].next = self.workflow[idx + 1]
                self.workflow[idx + 1].previous = self.workflow[idx]
                
            this.child_conn.send(Msg.ADD_ITEMS)
            this.child_conn.send(idx)
            this.child_conn.send(event.added[0])
                
    
    @on_trait_change('selected:operation.-transient')
    def _on_workflow_operation_changed(self, obj, name, old, new):
        print "op changed"
        # search the workflow for the appropriate wi
        #wi = next((x for x in self.workflow if x.operation == obj))
        idx = self.workflow.index(self.selected)
        
        this.child_conn.send(Msg.UPDATE_OP)
        this.child_conn.send(idx)
        this.child_conn.send(self.selected.operation)
        
    @on_trait_change('selected.current_view.-transient')
    def _on_workflow_view_changed(self, obj, name, old, new):
        print "view changed"
        # search the workflow for the appropriate wi
        if type(obj) is WorkflowItem:
            wi = obj
        else: # a view
            wi = next((x for x in self.workflow if x.current_view == obj))
        
        idx = self.workflow.index(wi)
        
        this.child_conn.send(Msg.PLOT)
        this.child_conn.send(idx)
        this.child_conn.send(wi.current_view)

    # MAGIC: called when default_scale is changed
    def _default_scale_changed(self, new_scale):
        cytoflow.set_default_scale(new_scale)

        
class RemoteWorkflow(HasStrictTraits):
    workflow = List(WorkflowItem)
    
    def run(self):
        while True:
            cmd = this.parent_conn.recv()
            if cmd == Msg.NEW_WORKFLOW:
                new_items = this.parent_conn.recv()
                self.new_workflow(new_items)
            elif cmd == Msg.ADD_ITEMS:
                idx = this.parent_conn.recv()
                new_item = this.parent_conn.recv()
                self.add_item(idx, new_item)
            elif cmd == Msg.REMOVE_ITEMS:
                idx = this.parent_conn.recv()
                self.remove_item(idx)
            elif cmd == Msg.UPDATE_OP:
                idx = this.parent_conn.recv()
                op = this.parent_conn.recv()
                self.update_op(idx, op)
            elif cmd == Msg.PLOT:
                idx = this.parent_conn.recv()
                view = this.parent_conn.recv()
                self.plot(idx, view)
            else:
                raise RuntimeError("Bad command in the remote workflow")
            
    def new_workflow(self, new_items):
        self.workflow = new_items

        for wi in self.workflow:
            wi.status = "invalid"
        
        for wi in self.workflow:
            wi.update()
            
    def add_item(self, idx, new_item):
        self.workflow.insert(idx, new_item)
        
        if idx > 0:
            self.workflow[idx - 1].next = self.workflow[idx]
            self.workflow[idx].previous = self.workflow[idx - 1]
            
        if idx < len(self.workflow) - 1:
            self.workflow[idx].next = self.workflow[idx + 1]
            self.workflow[idx + 1].previous = self.workflow[idx]
            
        for wi in self.workflow[idx:]:
            wi.status = "invalid"

        for wi in self.workflow[idx:]:
            wi.update()        
    
    def remove_item(self, idx):
        removed = self.workflow[idx]
        
        if removed.previous:
            removed.previous.next = removed.next
            
        if removed.next:
            removed.next.previous = removed.previous
            
        for wi in self.workflow[idx:]:
            wi.status = "invalid"

        for wi in self.workflow[idx:]:
            wi.update()   
    
    def update_op(self, idx, op):
        self.workflow[idx].operation = op
        
        for wi in self.workflow[idx:]:
            wi.status = "invalid"

        for wi in self.workflow[idx:]:
            wi.update()     
            
    def plot(self, idx, view):
        print "remote plot"
        wi = self.workflow[idx]
        error = ""
        warning = ""
        
        with warnings.catch_warnings(record = True) as w:
            try:
                view.plot_wi(wi)
                if w:
                    warning = w[-1].message.__str__()
            except util.CytoflowViewError as e:
                error = e.__str__()
        
        this.parent_conn.send(Msg.VIEW_STATUS)
        this.parent_conn.send(idx)
        this.parent_conn.send(view.id)
        this.parent_conn.send(warning)
        this.parent_conn.send(error)
            
    @on_trait_change("workflow.status")
    def _on_status_change(self, obj, name, old, new):
        idx = self.workflow.index(obj)
        this.parent_conn.send(Msg.OP_STATUS)
        this.parent_conn.send(idx)
        this.parent_conn.send(obj.channels)
        this.parent_conn.send(obj.conditions)
        this.parent_conn.send(obj.conditions_names)
        this.parent_conn.send(obj.warning)
        this.parent_conn.send(obj.error)
        this.parent_conn.send(obj.status)
