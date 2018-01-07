#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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

# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'qt4'

import os.path

from traits.api import Instance, List, Bool, on_trait_change, Any, Unicode, TraitError
from pyface.tasks.api import Task, TaskLayout, PaneItem, TraitsDockPane
from pyface.tasks.action.api import SMenu, SMenuBar, SToolBar, TaskAction
from pyface.api import FileDialog, ImageResource, AboutDialog, information, error, confirm, OK, YES
from envisage.api import Plugin, ExtensionPoint, contributes_to
from envisage.ui.tasks.api import TaskFactory

from cytoflowgui.flow_task_pane import FlowTaskPane
from cytoflowgui.workflow_pane import WorkflowDockPane
from cytoflowgui.view_pane import ViewDockPane
from cytoflowgui.help_pane import HelpDockPane
from cytoflowgui.workflow import Workflow
from cytoflowgui.op_plugins import IOperationPlugin, ImportPlugin, ChannelStatisticPlugin, OP_PLUGIN_EXT
from cytoflowgui.view_plugins import IViewPlugin, VIEW_PLUGIN_EXT
from cytoflowgui.notebook import JupyterNotebookWriter
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.util import DefaultFileDialog

# from . import mailto

from traits.api import provides, Instance, List

from pyface.qt import QtGui, QtCore
from pyface.tasks.api import TraitsDockPane, IDockPane, Task
from pyface.action.api import ToolBarManager
from pyface.tasks.action.api import TaskAction

from cytoflowgui.op_plugins import IOperationPlugin

from cytoflowgui.tasbe_calibration import TasbeCalibrationOp

class CalibrationPane(TraitsDockPane):
    
    id = 'edu.mit.synbio.calibration_pane'
    name = "TASBE Calibration"

    # the task serving as the dock pane's controller
    task = Instance(Task)
    
    closable = False
    dock_area = 'left'
    floatable = False
    movable = False
    visible = True
    
    def create_contents(self, parent):
        """ Create and return the toolkit-specific contents of the dock pane.
        """
        self.ui = self.model.edit_traits(view = 'single_operation',
                                         kind='subpanel', 
                                         parent=parent)
        return self.ui.control

class TASBETask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflow.tasbe_task"
    name = "TASBE calibration"
    
    # the main workflow instance.
    model = Instance(Workflow)
        
    # the center pane
    plot_pane = Instance(FlowTaskPane)
    calibration_pane = Instance(TraitsDockPane)
#     help_pane = Instance(HelpDockPane)
    
    def prepare_destroy(self):
        self.model.shutdown_remote_process()
    
    def activated(self):
        
        self.model.workflow = []
        
        # add the op
        op = TasbeCalibrationOp()
        
        # make a new workflow item
        wi = WorkflowItem(operation = op,
                          deletable = False)
       
        wi.default_view = op.default_view() 
        wi.views.append(wi.default_view)
        wi.current_view = wi.default_view
             
        self.model.workflow.append(wi)
        
        # and make sure to actually select the new wi.  not that the UI
        # will be updated or anything...
        self.model.selected = wi
    
    def _default_layout_default(self):
        return TaskLayout(left = PaneItem("edu.mit.synbio.calibration_pane"))
     
    def create_central_pane(self):
        self.plot_pane = FlowTaskPane(model = self.model)
        return self.plot_pane
     
    def create_dock_panes(self):
        self.calibration_pane = CalibrationPane(model = self.model, 
                                                task = self)
#         
#         self.help_pane = HelpDockPane(view_plugins = self.view_plugins,
#                                       op_plugins = self.op_plugins,
#                                       task = self)
        
        return [self.calibration_pane]
     
        
class TASBETaskPlugin(Plugin):
    """
    An Envisage plugin wrapping TASBETask
    """

    # Extension point IDs.
    PREFERENCES       = 'envisage.preferences'
    PREFERENCES_PANES = 'envisage.ui.tasks.preferences_panes'
    TASKS             = 'envisage.ui.tasks.tasks'
    
    debug = Bool(False)
    remote_connection = Any

    #### 'IPlugin' interface ##################################################

    # The plugin's unique identifier.
    id = 'edu.mit.synbio.cytoflow.tasbe'

    # The plugin's name (suitable for displaying to the user).
    name = 'TASBE Calibration'

    ###########################################################################
    # Protected interface.
    ###########################################################################

    @contributes_to(PREFERENCES)
    def _get_preferences(self):
        filename = os.path.join(os.path.dirname(__file__), 'preferences.ini')
        return [ 'file://' + filename ]
    
    @contributes_to(PREFERENCES_PANES)
    def _get_preferences_panes(self):
        from .preferences import CytoflowPreferencesPane
        return [CytoflowPreferencesPane]

    @contributes_to(TASKS)
    def _get_tasks(self):
        return [TaskFactory(id = 'edu.mit.synbio.cytoflow.tasbe_task',
                            name = 'TASBE Calibration',
                            factory = lambda **x: TASBETask(application = self.application,
                                                            model = Workflow(self.remote_connection,
                                                                             debug = self.debug),
                                                            **x))]
