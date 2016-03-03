#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Created on Feb 11, 2015

@author: brian
"""

#import threading, time

import warnings

from pyface.tasks.api import TaskPane
from traits.api import Instance, provides
from pyface.tasks.i_task_pane import ITaskPane
import matplotlib.pyplot as plt

from cytoflow.utility import CytoflowViewError

from matplotlib_editor import MPLFigureEditor

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
        
        wi.current_view.error = ""
        wi.current_view.warning = ""
        
        with warnings.catch_warnings(record = True) as w:
            try:
                if wi.current_view == wi.default_view:
                    # plotting the default view
                    wi.current_view.plot(wi.previous.result)
                else:
                    if not wi.result:
                        self.clear_plot()
                        return
                    
                    wi.current_view.plot(wi.result)
                    
                if w:
                    wi.current_view.warning = w[-1].message.__str__()
                    
            except CytoflowViewError as e:
                wi.current_view.error = e.__str__()

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
        