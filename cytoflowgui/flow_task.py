"""
Created on Feb 11, 2015

@author: brian
"""

from pyface.tasks.api import Task, TaskLayout, PaneItem
from example_panes import PythonScriptBrowserPane
from flow_task_pane import FlowTaskPane

class FlowTask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbiocenter.flow_task"
    name = "Flow cytometry analysis pane"
    
    def _default_layout_default(self):
        return TaskLayout( left = PaneItem("browser_l"),
                           right = PaneItem("browser_r"))
    
    def create_central_pane(self):
        return FlowTaskPane()
    
    def create_dock_panes(self):
        browser_l = PythonScriptBrowserPane()
        browser_l.id = "browser_l"
        browser_r = PythonScriptBrowserPane()
        browser_r.id = "browser_r"
        return [browser_l, browser_r]
        