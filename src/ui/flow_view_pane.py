"""
Created on Feb 11, 2015

@author: brian
"""
from pyface.tasks.task_pane import TaskPane
from matplotlib_editor import MPLFigureEditor
from traits.api import Instance

class FlowViewPane(TaskPane):
    """
    classdocs
    """
    
    id = 'edu.mit.synbio.flow_view_pane'
    name = 'Cytometry Data Viewer'
    
    editor = Instance(MPLFigureEditor)
    
    def create(self, parent):
        self.editor = MPLFigureEditor()
        #self.control = self.editor.control

    def destroy(self):
        self.editor.destroy()
        #self.control = self.editor = None