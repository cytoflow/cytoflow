"""
Created on Feb 11, 2015

@author: brian
"""

import os.path

from traits.api import List, Instance
from pyface.tasks.api import Task, TaskLayout, PaneItem
from envisage.api import Plugin
from envisage.ui.tasks.api import TaskFactory
from example_panes import PythonScriptBrowserPane
from flow_task_pane import FlowTaskPane
from cytoflowgui.workflow_pane import WorkflowDockPane
from cytoflowgui.view_traits_pane import ViewTraitsDockPane
from cytoflowgui.workflow import Workflow

class FlowTask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflow.flow_task"
    name = "Cytometry analysis"
    
    # the main workflow instance
    model = Instance(Workflow)
        
    def initialized(self):
        pass
    
    def prepare_destroy(self):
        self.model = None
    
    def _default_layout_default(self):
        return TaskLayout( left = PaneItem("edu.mit.synbio.workflow_pane"),
                           right = PaneItem("edu.mit.synbio.view_traits_pane"))
     
    def create_central_pane(self):
        return FlowTaskPane(model = self.model)
     
    def create_dock_panes(self):
        if not self.model:
            self.model = Workflow()
        return [WorkflowDockPane(model = self.model), 
                ViewTraitsDockPane(model = self.model)]
        
        
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
    name = 'Attractors'

    #### Contributions to extension points made by this plugin ################

    preferences = List(contributes_to=PREFERENCES)
    preferences_panes = List(contributes_to=PREFERENCES_PANES)
    tasks = List(contributes_to=TASKS)

    ###########################################################################
    # Protected interface.
    ###########################################################################

    def _preferences_default(self):
        filename = os.path.join(os.path.dirname(__file__), 'preferences.ini')
        return [ 'file://' + filename ]
    
    def _preferences_panes_default(self):
        from preferences import CytoflowPreferencesPane
        return [ CytoflowPreferencesPane ]

    def _tasks_default(self):
        return [ TaskFactory(id = 'edu.mit.synbio.cytoflow.flow_task',
                             name = 'Cytometry analysis',
                             factory = FlowTask) ]
