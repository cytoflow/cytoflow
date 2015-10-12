"""
Created on Feb 11, 2015

@author: brian
"""
from pyface.tasks.api import TaskPane
from matplotlib_editor import MPLFigureEditor
from traits.api import Instance, provides
from pyface.tasks.i_task_pane import ITaskPane
import matplotlib.pyplot as plt

from cytoflow.utility import CytoflowViewError

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
        self.editor.clear = True
        self.editor.draw = True
        
    def plot(self, wi):
        """
        Plot the an experiment in the center pane.
        
        Arguments
        ---------
        wi : WorkflowItem
            The WorkflowItem (data + current view) to plot
        """
         
#         # TODO - make this multithreaded.  atm this returns "Cannot set parent,
#         # new parent is in a different thread."
#         def do_plot(view, experiment):
#             view.plot(experiment)
#                  
#         t = threading.Thread(target = do_plot,
#                              args = (view, experiment))
#         t.start()
#         t.join()
#         
#         self.editor.clear = True
#         self.editor.figure = plt.gcf()
#         self.editor.draw = True
        
        # TODO - view.plot is going to create a new figure.  get the new
        # figure with plt.gcf() and keep track of the mapping between figure
        # and view; then, set the editor to the new figure.
        
        # TODO - make the plotting responsive to the view params.  ie,
        # after a new view is created, watch it so that if its params change
        # we can make a new plot (figure); but if the params stay the same
        # and the plot is re-selected, we can just reuse the existing figure.
        
        if not wi.current_view:
            self.clear_plot()
            return
        
        if wi.current_view == wi.default_view:
            # plotting the default view
            try:
                wi.current_view.plot(wi.previous.result)
            except CytoflowViewError as e:
                wi.current_view.error = e.__str__()
            else:
                wi.current_view.error = ""
        else:
            if not wi.result:
                self.clear_plot()
                return
            
            try:
                wi.current_view.plot(wi.result)
            except CytoflowViewError as e:
                wi.current_view.error = e.__str__()
            else:
                wi.current_view.error = ""

        self.editor.figure = plt.gcf()
           
        if "interactive" in wi.current_view.traits():
            # we have to re-bind the Cursor to the new Axes object by twiddling
            # the "interactive" trait
            wi.current_view.interactive = False
            wi.current_view.interactive = True 
            
    def export(self, filename):
        # TODO - eventually give a preview, allow changing size, dpi, aspect 
        # ratio, plot layout, etc.  at the moment, just export exactly what's
        # on the screen
        plt.savefig(filename, bbox_inches = 'tight')
        