#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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

from traits.api import Instance, Bool, Any, on_trait_change, HTML
from traitsui.api import View, Item, InstanceEditor
from pyface.tasks.api import Task, TaskLayout, PaneItem, TraitsDockPane
from pyface.tasks.action.api import SMenuBar, SMenu, TaskToggleGroup
from envisage.api import Plugin, contributes_to
from envisage.ui.tasks.api import TaskFactory
from pyface.qt import QtGui

from cytoflow.operations import IOperation

# from cytoflowgui.flow_task_pane import FlowTaskPane, getFlowTaskPane
from cytoflowgui.workflow import LocalWorkflow, WorkflowItem
from cytoflowgui.help_pane import HelpDockPane

from cytoflowgui.tasbe_calibration import TasbeCalibrationOp
from cytoflowgui.util import HintedWidget

class CalibrationPane(TraitsDockPane):
    
    id = 'edu.mit.synbio.cytoflowgui.calibration_pane'
    name = "TASBE Calibration"

    # the task serving as the dock pane's controller
    task = Instance(Task)
    
    closable = False
    dock_area = 'left'
    floatable = False
    movable = False
    visible = True
    
    single_operation = View(Item('selected',
                                 editor = InstanceEditor(view = 'operation_traits'),
                                 style = 'custom',
                                 show_label = False))
    
    def create_contents(self, parent):
        """ Create and return the toolkit-specific contents of the dock pane.
        """
        self.ui = self.model.edit_traits(view = self.single_operation,
                                         kind='subpanel', 
                                         parent=parent,
                                         scrollable = True)
        layout = QtGui.QHBoxLayout()
        control = HintedWidget()
        
        layout.addWidget(self.ui.control)
        control.setLayout(layout)
        control.setParent(parent)
        parent.setWidget(control)
        return control

class TASBETask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflowgui.tasbe_task"
    name = "TASBE calibration"
    
    menu_bar = SMenuBar(SMenu(TaskToggleGroup(),
                              id = 'View', name = '&View'))
    
    # the main workflow instance.
    model = Instance(LocalWorkflow)
    
    op = Instance(IOperation)
        
    calibration_pane = Instance(CalibrationPane)
    help_pane = Instance(HelpDockPane)
    
    _cached_help = HTML

    
    def activated(self):
        self.model.backup_workflow = self.model.workflow
        self.model.workflow = []
        self.model.modified = False
        
        # add the op
        self.op = TasbeCalibrationOp()
        
        # make a new workflow item
        wi = WorkflowItem(operation = self.op,
                          deletable = False)
       
        wi.default_view = self.op.default_view() 
        wi.views.append(wi.default_view)
        wi.current_view = wi.default_view
             
        self.model.workflow.append(wi)
        self.model.selected = wi
        
        self.help_pane.html = self.op.get_help()
    
    def _default_layout_default(self):
        return TaskLayout(left = PaneItem("edu.mit.synbio.cytoflowgui.calibration_pane", width = 350),
                          right = PaneItem("edu.mit.synbio.cytoflowgui.help_pane", width = 350))
     
    def create_central_pane(self):
        raise NotImplementedError("Implement me!")
        pass
        #return self.application.plot_pane
     
    def create_dock_panes(self):
        self.calibration_pane = CalibrationPane(model = self.model, 
                                                task = self)
         
        self.help_pane = HelpDockPane(task = self)
        
        return [self.calibration_pane, self.help_pane]
    
    @on_trait_change('op:do_exit', post_init = True)
    def activate_cytoflow_task(self):
        task = next(x for x in self.window.tasks if x.id == 'edu.mit.synbio.cytoflowgui.flow_task')
        self.window.activate_task(task)

        
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
    
    # the local process's model
    model = Instance(LocalWorkflow)

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
        return [TaskFactory(id = 'edu.mit.synbio.cytoflowgui.tasbe_task',
                            name = 'TASBE Calibration',
                            factory = lambda **x: TASBETask(application = self.application,
                                                            model = self.application.model,
                                                            **x))]
