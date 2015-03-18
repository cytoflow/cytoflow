"""
Created on Feb 11, 2015

@author: brian
"""

import os.path

from traits.api import Instance, List
from pyface.tasks.api import Task, TaskLayout, PaneItem
from envisage.api import Plugin, Application
from envisage.ui.tasks.api import TaskFactory
from flow_task_pane import FlowTaskPane
from cytoflowgui.workflow_pane import WorkflowDockPane
from cytoflowgui.view_traits_pane import ViewTraitsDockPane
from cytoflowgui.workflow import Workflow
from cytoflowgui.import_workflow_item import ImportWorkflowItem
from envisage.extension_point import contributes_to
from cytoflowgui.op_factory import OperationFactory
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin
from cytoflowgui.workflow_item import WorkflowItem

class FlowTask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflow.flow_task"
    name = "Cytometry analysis"
    
    # the main workflow instance.
    # THIS IS WHERE IT'S INITIALLY INSTANTIATED (note the args=())
    model = Instance(Workflow, args = ())
    
    application = Instance(Application)
    
    op_plugins = List(IOperationPlugin)
        
    def initialized(self):
        self.model.workflow.append(ImportWorkflowItem())
        #self.op_plugins = self.application.get_extensions("edu.mit.synbio.cytoflow.op_plugins")
        print "ops"
        print len(self.op_plugins)
    
    def prepare_destroy(self):
        self.model = None
    
    def _default_layout_default(self):
        return TaskLayout(left = PaneItem("edu.mit.synbio.workflow_pane"),
                          right = PaneItem("edu.mit.synbio.view_traits_pane"))
     
    def create_central_pane(self):
        return FlowTaskPane(model = self.model)
     
    def create_dock_panes(self):
        return [WorkflowDockPane(model = self.model, 
                                 application = self.application,
                                 task = self), 
                ViewTraitsDockPane(model = self.model,
                                   application = self.application,
                                   task = self)]
        
    def add_operation(self, plugin, after):
        idx = self.model.workflow.index(after)
        new_item = WorkflowItem(operation = plugin.get_operation(),
                                handler = plugin.get_handler())
        self.model.workflow.insert(idx+1, new_item)
        
        
class FlowTaskPlugin(Plugin):
    """
    An Envisage plugin wrapping FlowTask
    """

    # Extension point IDs.
    PREFERENCES       = 'envisage.preferences'
    PREFERENCES_PANES = 'envisage.ui.tasks.preferences_panes'
    TASKS             = 'envisage.ui.tasks.tasks'

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
                            factory = lambda **x: FlowTask(application = self.application, **x))]
