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
        pass
#         self.editor.figure.clear()
#         self.editor.control.draw()
        
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
        
        # TODO - view.plot is going to create a new figure.  get the new
        # figure with plt.gcf() and keep track of the mapping between figure
        # and view; then, set the editor to the new figure.
        
        # TODO - make the plotting responsive to the view params.  ie,
        # after a new view is created, watch it so that if its params change
        # we can make a new plot (figure); but if the params stay the same
        # and the plot is re-selected, we can just reuse the existing figure.
        
        self.editor.clear = True
        view.plot(experiment)
        self.editor.draw = True
           
#         if "interactive" in view.traits():
#             # we have to re-bind the Cursor to the new Axes object by twiddling
#             # the "interactive" trait
#             view.interactive = False
#             view.interactive = True 
            
            
    def export(self, filename):
        pass
        # TODO - eventually give a preview, allow changing size, dpi, aspect 
        # ratio, plot layout, etc.
        # plt.savefig(filename, bbox_inches = 'tight')
        
        