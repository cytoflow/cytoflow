#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflowgui.experiment_pane
---------------------------

A dock pane with an experiment browser.
"""

from traits.api import Instance
from pyface.tasks.api import TraitsDockPane

from .workflow_controller import WorkflowController

class ExperimentBrowserDockPane(TraitsDockPane):
    """
    A DockPane with a read-only view of some of the traits of the `Experiment` that
    results from the currently-selected `WorkflowItem`.
    """

    id = 'edu.mit.synbio.cytoflowgui.experiment_pane'
    name = "Experiment Browser"

    # controller
    handler = Instance(WorkflowController)
    
    closable = True
    dock_area = 'left'
    floatable = True
    movable = True
    visible = True
    
    def create_contents(self, parent):
        """ Create and return the toolkit-specific contents of the dock pane.
        """
    
        self.ui = self.handler.edit_traits(view = 'experiment_view',
                                           context = self.model,
                                           kind='subpanel', 
                                           parent=parent,
                                           scrollable = True)
        return self.ui.control
