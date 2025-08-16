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

from traits.api import provides, Instance, List, observe

from pyface.qt import QtCore
from pyface.tasks.api import TraitsDockPane, IDockPane  # @UnresolvedImport
from pyface.action.api import ToolBarManager  # @UnresolvedImport
from pyface.tasks.action.api import TaskAction
from pyface.qt import QtGui, QtCore

from .op_plugins import IOperationPlugin
from .util import HintedMainWindow
from .workflow_controller import WorkflowController

@provides(IDockPane)
class WorkflowDockPane(TraitsDockPane):
    """
    Workflow dock pane
    """
    
    id = 'cytoflowgui.workflow_pane'
    name = "Workflow"
    
    # the application instance from which to get plugin instances
    plugins = List(IOperationPlugin)
    
    # controller
    handler = Instance(WorkflowController)
    
    _window = Instance(QtGui.QMainWindow)
    
    def create_contents(self, parent):
        """ 
        Create and return the toolkit-specific contents of the dock pane.
        """
 
        self._toolbar_mgr = ToolBarManager(orientation='vertical',
                                           show_tool_names = self.task.application.preferences_helper.show_toolbar_names,
                                           image_size = (40, 40))
                 
        for plugin in self.plugins:
            
            # don't include the import plugin
            if plugin.id == 'cytoflowgui.op_plugins.import':
                continue
            
            task_action = TaskAction(name=plugin.short_name,
                                     on_perform = lambda plugin_id = plugin.operation_id: 
                                        self.handler.add_operation(plugin_id),
                                     image = plugin.get_icon())
            self._toolbar_mgr.append(task_action)
             
        # see the comment in cytoflowgui.view_pane for an explanation of this
        # HintedMainWindow business.
        self._window = HintedMainWindow()          
        self._toolbar = self._toolbar_mgr.create_tool_bar(self._window)
        self._window.addToolBar(QtCore.Qt.LeftToolBarArea,    # @UndefinedVariable
                                self._toolbar)
        
        # construct the view 
        self.ui = self.handler.edit_traits(view = 'workflow_traits_view', 
                                           context = self.model,
                                           kind = 'subpanel', 
                                           parent = self._window)
        
        self._window.setCentralWidget(self.ui.control)
         
        self._window.setParent(parent)
        parent.setWidget(self._window)
         
        return self._window
    
    @observe('task.application.preferences_helper.show_toolbar_names', post_init = True)
    def show_toolbar_names(self, _):
        self._window.removeToolBar(self._toolbar)
        self._toolbar.deleteLater()
        self._toolbar_mgr.show_tool_names = self.task.application.preferences_helper.show_toolbar_names
        self._toolbar = self._toolbar_mgr.create_tool_bar(self._window)
        self._window.addToolBar(QtCore.Qt.LeftToolBarArea,    # @UndefinedVariable
                                self._toolbar)
