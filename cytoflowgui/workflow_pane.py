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
cytoflowgui.workflow_pane
-------------------------

The pane that has the operation toolbar and the workflow.
"""

from traits.api import provides, Instance, List, Tuple

from pyface.qt import QtCore
from pyface.tasks.api import TraitsDockPane, IDockPane
from pyface.action.api import ToolBarManager
from pyface.tasks.action.api import TaskAction

from .op_plugins import IOperationPlugin
from .util import HintedMainWindow
from .workflow_controller import WorkflowController

@provides(IDockPane)
class WorkflowDockPane(TraitsDockPane):
    """
    Workflow dock pane
    """
    
    id = 'edu.mit.synbio.cytoflowgui.workflow_pane'
    name = "Workflow"
    
    # the application instance from which to get plugin instances
    plugins = List(IOperationPlugin)
    
    # controller
    handler = Instance(WorkflowController)
    
    # the size of the plugin toolbar images IN INCHES
    image_size = Tuple((0.33, 0.33))

    def create_contents(self, parent):
        """ 
        Create and return the toolkit-specific contents of the dock pane.
        """
         
        dpi = self.control.physicalDpiX()
        image_size = (int(self.image_size[0] * dpi),
                      int(self.image_size[1] * dpi))
 
        self.toolbar = ToolBarManager(orientation='vertical',
                                      show_tool_names = False,
                                      image_size = image_size)
                 
        for plugin in self.plugins:
            
            # don't include the import plugin
            if plugin.id == 'edu.mit.synbio.cytoflowgui.op_plugins.import':
                continue
            
            task_action = TaskAction(name=plugin.short_name,
                                     on_perform = lambda plugin_id = plugin.operation_id: 
                                        self.handler.add_operation(plugin_id),
                                     image = plugin.get_icon())
            self.toolbar.append(task_action)
             
        # see the comment in cytoflowgui.view_pane for an explanation of this
        # HintedMainWindow business.
        window = HintedMainWindow()                    
        window.addToolBar(QtCore.Qt.LeftToolBarArea,    # @UndefinedVariable
                          self.toolbar.create_tool_bar(window))
        
        # construct the view 
        self.ui = self.handler.edit_traits(view = 'workflow_traits_view', 
                                           context = self.model,
                                           kind = 'subpanel', 
                                           parent = window)
        
        window.setCentralWidget(self.ui.control)
         
        window.setParent(parent)
        parent.setWidget(window)
         
        return window
