"""
Created on Feb 11, 2015

@author: brian
"""

import os.path

from traits.api import Instance, List, Bool, Float, on_trait_change
from pyface.tasks.api import Task, TaskLayout, PaneItem
from pyface.tasks.action.api import SMenu, SMenuBar, SToolBar, TaskAction
from pyface.api import FileDialog, OK, ImageResource
from envisage.api import Plugin, ExtensionPoint, contributes_to
from envisage.ui.tasks.api import TaskFactory
from flow_task_pane import FlowTaskPane
from cytoflowgui.workflow_pane import WorkflowDockPane
from cytoflowgui.view_pane import ViewDockPane
from cytoflowgui.workflow import Workflow

from cytoflowgui.op_plugins import IOperationPlugin, ImportPlugin, OP_PLUGIN_EXT
from cytoflowgui.view_plugins import IViewPlugin, VIEW_PLUGIN_EXT
from cytoflowgui.workflow_item import WorkflowItem



from util import UniquePriorityQueue
import threading
import pickle as pickle

class FlowTask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflow.flow_task"
    name = "Cytometry analysis"
    
    # the main workflow instance.
    # THIS IS WHERE IT'S INITIALLY INSTANTIATED (note the args=())
    model = Instance(Workflow, args = ())
    
    # the center pane
    view = Instance(FlowTaskPane)
    
    # plugin lists, to setup the interface
    op_plugins = List(IOperationPlugin)
    view_plugins = List(IViewPlugin)
    
    menu_bar = SMenuBar(SMenu(TaskAction(name='Open...', method='open',
                                         accelerator='Ctrl+O'),
                              TaskAction(name='Save', method='save',
                                         accelerator='Ctrl+S'),
                              id='File', name='&File'))
    
    tool_bars = [ SToolBar(TaskAction(method='open',
                                      tooltip='Open a file',
                                      image=ImageResource('document_open')),
                           TaskAction(method='save',
                                      tooltip='Save the current file',
                                      image=ImageResource('document_save'))) ]
    
    # are we debugging?  ie, do we need a default setup?
    debug = Bool
    
    #worker = Instance(threading.Thread)
    to_update = Instance(UniquePriorityQueue, ())
    worker_flag = Instance(threading.Event, args = ())
    worker_lock = Instance(threading.Lock, args = ())
        
    def initialized(self):
        
        # setup the worker thread
        def update_model(flag, lock, to_update):
            while flag.wait():
                flag.clear()
                while not to_update.empty():
                    with lock:
                        prio, wi = to_update.get_nowait()
                    wi.update()
    
        worker = threading.Thread(target = update_model, 
                                  args = (self.worker_flag, 
                                          self.worker_lock,
                                          self.to_update))
        worker.start()
        
        # add an import plugin
        plugin = ImportPlugin()
        wi = WorkflowItem(task = self)
        wi.operation = plugin.get_operation()

        self.model.workflow.append(wi)
        self.model.selected = wi
        
        # if we're debugging, add a few data bits
#         if self.debug:
#             from cytoflow import Tube
#             from cytoflow.operations.import_op import LogFloat
#             Tube.add_class_trait("Dox", LogFloat)
#             tube1 = Tube(Name = "Tube 1",
#                          File = "../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs",
#                          Dox = LogFloat(0.01))
#             tube2 = Tube(Name = "Tube 2",
#                          File = "../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs",
#                          Dox = LogFloat(0.1))
#                
#             wi.operation.tubes.append(tube1)
#             wi.operation.tubes.append(tube2)
#                
#             self.add_operation('edu.mit.synbio.cytoflowgui.op.hlog')
#             self.model.selected.operation.channels = ["V2-A", "Y2-A"]
#             self.model.selected.operation.name = "H"
    
    def prepare_destroy(self):
        self.model = None
    
    def _default_layout_default(self):
        return TaskLayout(left = PaneItem("edu.mit.synbio.workflow_pane"),
                          right = PaneItem("edu.mit.synbio.view_traits_pane"))
     
    def create_central_pane(self):
        self.view = FlowTaskPane(model = self.model)
        return self.view
     
    def create_dock_panes(self):
        return [WorkflowDockPane(model = self.model, 
                                 plugins = self.op_plugins,
                                 task = self), 
                ViewDockPane(plugins = self.view_plugins,
                             task = self)]
        
    def open(self):
        """ Shows a dialog to open a file.
        """
        dialog = FileDialog(parent=self.window.control, 
                            action = 'open',
                            wildcard='*.flow')
        if dialog.open() == OK:
            self.open_file(dialog.path)
            
    def open_file(self, path):
        f = open(path, 'r')
        unpickler = pickle.Unpickler(f)
        new_model = unpickler.load()

        for wi in self.model.workflow:
            wi.task = self
        
        self.model.workflow[:] = new_model.workflow
        self.model.selected = new_model.selected

        wi = self.model.workflow[0]
        while True:
            wi.valid = "invalid"
            with self.worker_lock:
                self.to_update.put_nowait((self.model.workflow.index(wi), wi))
            if wi.next:
                wi = wi.next
            else:
                break
            
        # start the worker thread processing
        with self.worker_lock:
            if not self.to_update.empty():
                self.worker_flag.set()
        
    def save(self):
        """ Shows a dialog to open a file.
        """
        dialog = FileDialog(parent=self.window.control,
                            action = 'save as', 
                            wildcard='*.flow')
        if dialog.open() == OK:
            self.save_file(dialog.path)
            
    def save_file(self, path):
        # TODO - error handling
        f = open(path, 'w')
        pickler = pickle.Pickler(f, 0)  # text protocol for now
        pickler.dump(self.model)
    
    def add_operation(self, op_id):
        # first, find the matching plugin
        plugin = next((x for x in self.op_plugins if x.id == op_id))
        
        # default to inserting at the end of the list if none selected
        after = self.model.selected
        if after is None:
            after = self.model.workflow[-1]
        
        idx = self.model.workflow.index(after)
        
        wi = WorkflowItem(task = self)
        wi.operation = plugin.get_operation()

        wi.next = after.next
        after.next = wi
        wi.previous = after
        if wi.next:
            wi.next.previous = wi
        self.model.workflow.insert(idx+1, wi)
        
        # set up the default view
        wi.default_view = plugin.get_default_view(wi.operation)
        if wi.default_view is not None:
            wi.default_view.handler = \
                wi.default_view.handler_factory(model = wi.default_view, wi = wi.previous)
            wi.views.append(wi.default_view)

        # select (open) the new workflow item
        self.model.selected = wi
        if wi.default_view:
            wi.current_view = wi.default_view
            
        # invalidate everything following
        #self.operation_parameters_updated()
        
    @on_trait_change("model:selected:operation:+")
    def operation_parameters_updated(self): 
        
        # invalidate this workflow item and all the ones following it
        wi = self.model.selected
        while True:
            wi.valid = "invalid"
            with self.worker_lock:
                self.to_update.put_nowait((self.model.workflow.index(wi), wi))
            if wi.next:
                wi = wi.next
            else:
                break
            
        # start the worker thread processing
        with self.worker_lock:
            if not self.to_update.empty():
                self.worker_flag.set()
              
    def clear_current_view(self):
        self.view.clear_plot()
        
    def set_current_view(self, view_id):
        """
        called by the view pane 
        """
        wi = self.model.selected
        
        view = next((x for x in wi.views if x.id == view_id), None)
        
        if not view:
            plugin = next((x for x in self.view_plugins if x.view_id == view_id))
            view = plugin.get_view()
            view.handler = view.handler_factory(model = view, wi = wi)
            wi.views.append(view)
        
        wi.current_view = view
        
    @on_trait_change("model:selected.current_view")
    def _current_view_changed(self, obj, name, old, new): 
        
        # we get notified if *either* the currently selected workflowitem
        # *or* the current view changes.
        
        if name == 'selected':
            new = new.current_view if new else None
            old = old.current_view if old else None
            
        # remove the notifications from the old view
        if old:
            old.on_trait_change(self.view_parameters_updated, remove = True)
            
        # whenever the view parameters change, we need to know so we can
        # update the plot(s)
        if new:
            new.on_trait_change(self.view_parameters_updated)
            
            if self.model.selected.is_plottable:
                self.model.selected.plot(self.view)
        
    def view_parameters_updated(self, obj, name, new):
        
        # i should be able to specify the metadata i want in the listener,
        # but there's an odd interaction (bug) between metadata, dynamic 
        # trait listeners and instance traits.
        
        if obj.trait(name).transient:
            return
        
        print "view parameters updated: {0}".format(name)
        wi = self.model.selected
        if wi is None:
            wi = self.model.workflow[-1]
            
        if wi.is_plottable:
            wi.plot(self.view)
        
class FlowTaskPlugin(Plugin):
    """
    An Envisage plugin wrapping FlowTask
    """

    # Extension point IDs.
    PREFERENCES       = 'envisage.preferences'
    PREFERENCES_PANES = 'envisage.ui.tasks.preferences_panes'
    TASKS             = 'envisage.ui.tasks.tasks'
    
    # these need to be declared in a Plugin instance; we pass them to h
    # the task instance thru its factory, below.
    op_plugins = ExtensionPoint(List(IOperationPlugin), OP_PLUGIN_EXT)
    view_plugins = ExtensionPoint(List(IViewPlugin), VIEW_PLUGIN_EXT)
    
    debug = Bool(False)

    #### 'IPlugin' interface ##################################################

    # The plugin's unique identifier.
    id = 'edu.mit.synbio.cytoflow'

    # The plugin's name (suitable for displaying to the user).
    name = 'Cytoflow'

    ###########################################################################
    # Protected interface.
    ###########################################################################

    @contributes_to(PREFERENCES)
    def _get_preferences(self):
        filename = os.path.join(os.path.dirname(__file__), 'preferences.ini')
        return [ 'file://' + filename ]
    
    @contributes_to(PREFERENCES_PANES)
    def _get_preferences_panes(self):
        from preferences import CytoflowPreferencesPane
        return [CytoflowPreferencesPane]

    @contributes_to(TASKS)
    def _get_tasks(self):
        return [TaskFactory(id = 'edu.mit.synbio.cytoflow.flow_task',
                            name = 'Cytometry analysis',
                            factory = lambda **x: FlowTask(application = self.application,
                                                           op_plugins = self.op_plugins,
                                                           view_plugins = self.view_plugins,
                                                           debug = self.debug,
                                                           **x))]
