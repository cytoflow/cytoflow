"""
Created on Feb 11, 2015

@author: brian
"""

from pyface.tasks.api import Task, TaskLayout, PaneItem
from flow_view_pane import FlowViewPane

class FlowTask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbiocenter.flow_task"
    name = "Flow cytometry analysis pane"
    
    def create_central_pane(self):
        return FlowViewPane()
        