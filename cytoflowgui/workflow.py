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
import threading, multiprocessing

from traits.api import HasStrictTraits, Instance, List, on_trait_change
                       
from traitsui.api import View, Item, InstanceEditor, Spring, Label

import cytoflow
import cytoflow.utility as util

from cytoflowgui.vertical_notebook_editor import VerticalNotebookEditor
from cytoflowgui.workflow_item import WorkflowItem
                    
class Workflow(HasStrictTraits):
    """
    A list of WorkflowItems.
    """

    workflow = List(WorkflowItem)
    selected = Instance(WorkflowItem)
    default_scale = util.ScaleEnum
    
    # a view for the entire workflow's list of operations
    operations_view = View(Item(name = 'workflow',
                                id = 'table',
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
        
        # insert it into the model 
        if self.workflow:
            # default to inserting at the end of the list if none selected
            after = self.selected
            if self.selected is None:
                after = self.model.workflow[-1]
             
            idx = self.workflow.index(after)
     
            wi.next = after.next
            after.next = wi
            wi.previous = after
            if wi.next:
                wi.next.previous = wi

            self.workflow.insert(idx+1, wi)
        else:
            self.workflow.append(wi)
 
        # select (open) the new workflow item
        self.selected = wi
        if wi.default_view:
            wi.current_view = wi.default_view
    
    def set_current_view(self, view):
        try:
            self.selected.current_view = next((x for x in self.selected.views if x.id == view.id))
        except StopIteration:
            self.selected.current_view = view
        
    @on_trait_change('workflow')
    def _on_new_workflow(self, obj, name, old, new):
        print "new workflow"
        
        self.selected = None
        
        for wi in self.workflow:
            wi.status = "invalid"
            
        for wi in self.workflow:
            wi.update()

        
    @on_trait_change('workflow_items')
    def _on_workflow_add_remove_items(self, event):
        print "workflow items changed"
        idx = event.index
        for wi in self.workflow[idx:]:
            wi.status = "invalid"
            
        for wi in self.workflow[idx:]:
            wi.update()      
                
    
    @on_trait_change('workflow.operation.-transient')
    def _on_workflow_item_changed(self, obj, name, old, new):
        # search the workflow for the appropriate wi
        wi = next((x for x in self.workflow if x.operation == obj))
        idx = self.workflow.index(wi)
        
        for wi in self.workflow[idx:]:
            wi.status = "invalid"
            
        for wi in self.workflow[idx:]:
            wi.update()


    # MAGIC: called when default_scale is changed
    def _default_scale_changed(self, new_scale):
        cytoflow.set_default_scale(new_scale)
