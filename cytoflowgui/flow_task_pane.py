"""
Created on Feb 11, 2015

@author: brian
"""
from pyface.tasks.task_pane import TaskPane
from matplotlib_editor import MPLFigureEditor
from traits.api import Instance, provides
from pyface.tasks.i_task_pane import ITaskPane
import matplotlib.pyplot as plt

import threading, time

@provides(ITaskPane)
class FlowTaskPane(TaskPane):
    """
    The center pane for the UI; contains the matplotlib canvas for plotting
    data views.  eventually, this will allow multiple views; for now, it's
    just one matplotlib canvas.
    """
    
    id = 'edu.mit.synbio.cytoflow.flow_task_pane'
    name = 'Cytometry Data Viewer'
    
    editor = Instance(MPLFigureEditor)
    
    def create(self, parent):
        self.editor = MPLFigureEditor(parent)
        self.control = self.editor.control

    def destroy(self):
        self.editor.destroy()
        self.control = self.editor = None 
        
    def clear_plot(self):
        self.editor.figure.clear()
        self.editor.control.draw()
        
    def plot(self, experiment, view):
        """
        Plot the an experiment in the center pane.
        
        Arguments
        ---------
        experiment : cytoflow.Experiment
            The data to plot
            
        view : cytoflow.IView
            The view to use for the plotting
        """
#         
#         def do_plot(editor, view, experiment, fig_num):
#             editor.clear = True
#             time.sleep(0)
#             view.plot(experiment, fig_num = fig_num)
#             time.sleep(0)
#             editor.draw = True
#                
#             if "interactive" in view.traits():
#                 # we have to re-bind the Cursor to the new Axes object by twiddling
#                 # the "interactive" trait
#                 view.interactive = False
#                 view.interactive = True 
#                 
#         t = threading.Thread(target = do_plot,
#                              args = (self.editor, 
#                                      view, 
#                                      experiment, 
#                                      self.editor.fig_num))
#         t.start()
         
        
        # TODO - figure out how to make this threaded.  unfortunately, it 
        # probably involves moving away from the pyplot stateful interface,
        # which opens a huge can of worms.
        
        self.editor.clear = True
        view.plot(experiment, fig_num = self.editor.fig_num)
        self.editor.draw = True
           
        if "interactive" in view.traits():
            # we have to re-bind the Cursor to the new Axes object by twiddling
            # the "interactive" trait
            view.interactive = False
            view.interactive = True 
            
            
    def export(self, filename):
        # TODO - eventually give a preview, allow changing size, dpi, aspect 
        # ratio, plot layout, etc.
        plt.savefig(filename, bbox_inches = 'tight')
        
        