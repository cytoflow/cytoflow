"""
Created on Feb 11, 2015

@author: brian
"""

import os.path

from traits.api import Instance, List, Bool, Float, on_trait_change
from pyface.api import error
from pyface.tasks.api import Task, TaskLayout, PaneItem
from envisage.api import Plugin, ExtensionPoint, contributes_to
from envisage.ui.tasks.api import TaskFactory
from flow_task_pane import FlowTaskPane
from cytoflowgui.workflow_pane import WorkflowDockPane
from cytoflowgui.view_pane import ViewDockPane
from cytoflowgui.workflow import Workflow

from cytoflowgui.op_plugins import IOperationPlugin, ImportPlugin, OP_PLUGIN_EXT
from cytoflowgui.view_plugins import IViewPlugin, VIEW_PLUGIN_EXT
from cytoflowgui.workflow_item import WorkflowItem

from cytoflow import Tube

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
    
    # are we debugging?  ie, do we need a default setup?
    debug = Bool
        
    def initialized(self):
        plugin = ImportPlugin()
        wi = WorkflowItem(task = self)
        wi.operation = plugin.get_operation()

        self.model.workflow.append(wi)
        self.model.selected = wi
        
        if self.debug:
            Tube.add_class_trait("Dox", Float)
            tube1 = Tube(Name = "Tube 1",
                         File = "../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs",
                         Dox = 0.01)
            tube2 = Tube(Name = "Tube 2",
                         File = "../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs",
                         Dox = 0.1)
            
            wi.operation.tubes.append(tube1)
            wi.operation.tubes.append(tube2)
            
            wi.update()
            
    
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

        after.next = wi
        wi.previous = after
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
            self.set_current_view(wi.default_view.id)
        
    def operation_parameters_updated(self, wi): #wi == "WorkflowItem"
        print "op parameters updated"
        wi.valid = "updating"
        
        prev_result = wi.previous.result if wi.previous else None
        is_valid = wi.operation.is_valid(prev_result)
        
        if not is_valid:
            wi.valid = "invalid"
            return
        
        # re-run the operation
        
        try:
            wi.result = wi.operation.apply(prev_result)
        except RuntimeError as e:
            error(None, e.strerror)       
        
        # update the center pane
        
        if wi.current_view and wi.current_view.is_valid(wi.result):
            self.view.plot(wi.result, wi.current_view)

        wi.valid = "valid"
        
        # tell the next WorkflowItem to go        
        if wi.next:
            wi.next.update = True
        
    def clear_current_view(self):
        self.view.clear_plot()
        
    def set_current_view(self, view_id): 
        wi = self.model.selected
        if wi is None:
            wi = self.model.workflow[-1]
            
        if wi.current_view and wi.current_view.id == view_id:
            return
            
        # remove the notifications from the current view
        if wi.current_view:
            wi.current_view.on_trait_change(self.view_parameters_updated,
                                            remove = True)
            
        view = next((x for x in wi.views if x.id == view_id), None)
        
        if not view:
            plugin = next((x for x in self.view_plugins if x.view_id == view_id))
            view = plugin.get_view()
            view.handler = view.handler_factory(model = view, wi = wi)
            wi.views.append(view)

        # whenever the view parameters change, we need to know so we can
        # update the plot(s)
        view.on_trait_change(self.view_parameters_updated)
        
        wi.current_view = view
        
        if wi.current_view.is_valid(wi.result):
            self.view.plot(wi.result, wi.current_view)
        
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
            
        if wi.current_view and wi.current_view.is_valid(wi.result):
            self.view.plot(wi.result, wi.current_view)
            
#     @on_trait_change('model.selected')
#     def _on_selected_wi_changed(self, obj, name, old, new):
#         if not new:
#             self.view.clear_plot()
#         else:
#             self.view.view = new.current_view
        
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
