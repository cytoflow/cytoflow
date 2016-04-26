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

from pyface.tasks.api import TaskPane
from traits.api import provides
from pyface.tasks.i_task_pane import ITaskPane

@provides(ITaskPane)
class FlowTaskPane(TaskPane):
    """
    The center pane for the UI; contains the matplotlib canvas for plotting
    data views.  eventually, this will allow multiple views; for now, it's
    just one matplotlib canvas.
    """
    
    id = 'edu.mit.synbio.cytoflow.flow_task_pane'
    name = 'Cytometry Data Viewer'
    
    def create(self, parent):
        
        self.ui = self.task.model.edit_traits(view = 'selected_view_plot',
                                              kind = 'subpanel', 
                                              parent = parent)
        self.control = self.ui.control

    def destroy(self):
#         self.ui.destroy()
        self.control = None 
#                   
#     def export(self, filename):
#         # TODO - eventually give a preview, allow changing size, dpi, aspect 
#         # ratio, plot layout, etc.  at the moment, just export exactly what's
#         # on the screen
#         self.editor.print_figure(filename, bbox_inches = 'tight')
        