"""
Created on Feb 11, 2015

@author: brian
"""

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import os.path

from traits.api import Instance, List, Bool, on_trait_change
from pyface.tasks.api import Task, TaskLayout, PaneItem
from pyface.tasks.action.api import SMenu, SMenuBar, SToolBar, TaskAction
from pyface.api import FileDialog, OK, ImageResource, AboutDialog
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
    
    menu_bar = SMenuBar(SMenu(TaskAction(name='Open...',
                                         method='on_open',
                                         accelerator='Ctrl+O'),
                              TaskAction(name='Save',
                                         #image='save', 
                                         method='on_save',
                                         accelerator='Ctrl+S'),
                              TaskAction(name='Save As...',
                                         method='on_save_as',
                                         accelerator='Ctrl+e'),
                              TaskAction(name='Export...',
                                         method='on_export',
                                         accelerator='Ctrl+x'),
                              TaskAction(name='Preferences...',
                                         method='on_prefs',
                                         accelerator='Ctrl+P'),
                              id='File', name='&File'),
                        SMenu(TaskAction(name='About...',
                                         method='on_about',
                                         accelerator="Ctrl+A"),
                              id="Help", name ="&Help"))
    
    tool_bars = [ SToolBar(TaskAction(method='on_new',
                                      name = "New",
                                      tooltip='New workflow',
                                      image=ImageResource('new')),
                           TaskAction(method='on_open',
                                      name = "Open",
                                      tooltip='Open a file',
                                      image=ImageResource('open')),
                           TaskAction(method='on_save',
                                      name = "Save",
                                      tooltip='Save the current file',
                                      image=ImageResource('save')),
                           TaskAction(method='on_export',
                                      name = "Export",
                                      tooltip='Export the current plot',
                                      image=ImageResource('export')),
                           TaskAction(method='on_prefs',
                                      name = "Prefs",
                                      tooltip='Preferences',
                                      image=ImageResource('prefs')),
                           image_size = (32, 32))]
    
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
        worker.daemon = True
        worker.start()
        
        # make sure that when the result changes we get notified
        # can't use a static notifier because selected.result gets updated
        # on the worker thread, but we need to dispatch on the UI thread
        self.model.on_trait_change(self._result_updated, 
                                   "selected:result",
                                   dispatch = 'ui')

            
    def activated(self):
        # add an import plugin
        plugin = ImportPlugin()
        wi = WorkflowItem(task = self)
        wi.operation = plugin.get_operation()

        self.model.workflow.append(wi)
        self.model.selected = wi
        
        # if we're debugging, add a few data bits
        if self.debug:
            from cytoflow import Tube
                     
            wi.operation.conditions["Dox"] = "log"
        
            tube1 = Tube(name = "Tube 1",
                         file = "../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs",
                         conditions = {"Dox" : 0.1})
        
            tube2 = Tube(name = "Tube 2",
                         file = "../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs",
                         conditions = {"Dox" : 1.0})
        
            wi.operation.tubes.append(tube1)
            wi.operation.tubes.append(tube2)
                        
            self.add_operation('edu.mit.synbio.cytoflowgui.op_plugins.hlog')
            self.model.selected.operation.channels = ["V2-A", "Y2-A"]
            self.model.selected.operation.name = "H"
              
            self.add_operation('edu.mit.synbio.cytoflowgui.op_plugins.threshold')
            self.model.selected.operation.channel = "Y2-A"
            self.model.selected.operation.threshold = 2000
            self.model.selected.operation.name = "T"        
    
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
        
    def on_new(self):
        self.model.workflow = []
        
        # add an import plugin
        plugin = ImportPlugin()
        wi = WorkflowItem(task = self)
        wi.operation = plugin.get_operation()

        self.model.workflow.append(wi)
        self.model.selected = wi
        
    def on_open(self):
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

        # update the link back to the controller (ie, self)
        for wi in new_model.workflow:
            wi.task = self
            
            # and set up the view handlers
            for view in wi.views:
                view.handler = view.handler_factory(model = view, wi = wi)
                  
        # replace the current workflow with the one we just loaded
        
        if False:
            from event_tracer import record_events 
            
            with record_events() as container:
                self.model.workflow[:] = new_model.workflow
                self.model.selected = new_model.selected
                
            container.save_to_directory(os.getcwd()) 
        else:
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
        
    def on_save(self):
        """ Shows a dialog to open a file.
        """
        dialog = FileDialog(parent=self.window.control,
                            action = 'save as', 
                            wildcard='*.flow')
        if dialog.open() == OK:
            self.save_file(dialog.path)
            
    def on_save_as(self):
        pass
            
    def save_file(self, path):
        # TODO - error handling
        f = open(path, 'w')
        pickler = pickle.Pickler(f, 0)  # text protocol for now
        pickler.dump(self.model)
        
    def on_export(self):
        """
        Shows a dialog to export a file
        """
        dialog = FileDialog(parent = self.window.control,
                            action = 'save as')
        if dialog.open() == OK:
            self.view.export(dialog.path)
    
    def on_prefs(self):
        pass
    
    def on_about(self):
        from cytoflow import __version__ as cf_version
        from FlowCytometryTools import __version__ as fct_version
        from GoreUtilities import __version__ as gu_version
        from pandas.version import version as pd_version
        from numpy.version import version as np_version
        from numexpr import version as numexp_version
        from seaborn import __version__ as sns_version
        from matplotlib import __version__ as mpl_version
        from pyface import __version__ as py_version
        from envisage import __version__ as env_version
        from traits import __version__ as trt_version
        from traitsui import __version__ as trt_ui_version

        text = ["<b>Cytoflow {0}</b>".format(cf_version),
                "<p>",
                "FlowCytometryTools {0}".format(fct_version),
                "GoreUtilities {0}".format(gu_version),
                "pandas {0}".format(pd_version),
                "numpy {0}".format(np_version),
                "numexpr {0}".format(numexp_version),
                "seaborn {0}".format(sns_version),
                "matplotlib {0}".format(mpl_version),
                "pyface {0}".format(py_version),
                "envisage {0}".format(env_version),
                "traits {0}".format(trt_version),
                "traitsui {0}".format(trt_ui_version),
                "Icons from the <a href=http://tango.freedesktop.org/>Tango Desktop Project</a>",
                "Cuvette image from Wikimedia Commons user <a href=http://commons.wikimedia.org/wiki/File:Hellma_Large_cone_cytometry_cell.JPG>HellmaUSA</a>"]
        dialog = AboutDialog(parent = self.window.control,
                             title = "About",
                             image = ImageResource('cuvette'),
                             additions = text)
        dialog.open()
    
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
        self.operation_parameters_updated()
        
    @on_trait_change("model:workflow[]")
    def _on_remove_operation(self, obj, name, old, new):
        if name == "workflow_items" and len(new) == 0 and len(old) > 0:
            assert len(old) == 1
            wi = old[0]
            
            if self.model.selected == wi:
                self.model.selected = wi.previous
            
            wi.previous.next = wi.next
            if wi.next:
                wi.next.previous = wi.previous
            
            del wi.default_view
            del wi.views
            del wi

            self.operation_parameters_updated()
        
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
            
            # and if the old view was interactive, turn off its interactivity
            # to remove the matplotlib event handlers
            if "interactive" in old.traits():
                old.interactive = False
            
        # whenever the view parameters change, we need to know so we can
        # update the plot(s)
        if new:
            new.on_trait_change(self.view_parameters_updated)
            
            if self.model.selected and self.model.selected.is_plottable:
                self.model.selected.plot(self.view)
            else:
                self.clear_current_view()
        else:
            self.clear_current_view()

    def _result_updated(self, obj, name, old, new):
        print "result updated"
        if self.model.selected and self.model.selected.is_plottable:
            self.model.selected.plot(self.view)
        else:
            self.clear_current_view()
        
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
        else:
            self.clear_current_view()
        
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
