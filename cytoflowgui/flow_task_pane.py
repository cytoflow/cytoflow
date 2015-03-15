"""
Created on Feb 11, 2015

@author: brian
"""
from pyface.tasks.task_pane import TaskPane
from matplotlib_editor import MPLFigureEditor
from traits.api import Instance, provides
from pyface.tasks.i_task_pane import ITaskPane
from cytoflowgui.workflow import Workflow

@provides(ITaskPane)
class FlowTaskPane(TaskPane):
    """
    The center pane for the UI; contains the matplotlib canvas for plotting
    data views.  eventually, this will allow multiple views; for now, it's
    just one matplotlib canvas.
    """
    
    id = 'edu.mit.synbio.cytoflow.flow_task_pane'
    name = 'Cytometry Data Viewer'
    
    model = Instance(Workflow)
    editor = Instance(MPLFigureEditor)
    
    def create(self, parent):
        self.editor = MPLFigureEditor(parent)
        self.control = self.editor.control

    def destroy(self):
        self.editor.destroy()
        self.control = self.editor = None