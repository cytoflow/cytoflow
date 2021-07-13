#!/usr/bin/env python3.8
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

import os.path, pathlib

from traits.api import Instance, Event, CFloat, CInt, observe, provides, List
from traitsui.api import ButtonEditor, View, TextEditor, Item

from pyface.tasks.api import Task, TaskLayout, PaneItem, TraitsDockPane, VSplitter, ITaskPane, TaskPane
from pyface.tasks.action.api import SMenuBar, SMenu, TaskToggleGroup
from envisage.api import Plugin, ExtensionPoint
from envisage.ui.tasks.api import TaskFactory
from pyface.api import FileDialog, OK, error
from pyface.qt import QtGui

from .op_plugins import IOperationPlugin, OP_PLUGIN_EXT
from .view_plugins import IViewPlugin, VIEW_PLUGIN_EXT

from .workflow import LocalWorkflow
from .workflow_controller import WorkflowController
from .matplotlib_backend_local import FigureCanvasQTAggLocal
from .view_pane import PlotParamsPane

    
class ExportPane(TraitsDockPane):
    
    id = 'edu.mit.synbio.cytoflowgui.export_pane'
    name = 'Export'
    
    # the task serving as the dock pane's controller
    task = Instance(Task)
    
    closable = False
    dock_area = 'right'
    floatable = False
    movable = False
    visible = True
    
    def default_traits_view(self):
        return View(Item('width',
                         editor = TextEditor(auto_set = False)),
                    Item('height',
                         editor = TextEditor(auto_set = False)),
                    Item('dpi',
                         editor = TextEditor(auto_set = False)),
                    Item('do_export',
                         editor = ButtonEditor(value = True,
                                               label = "Export figure..."),
                         show_label = False),
                    Item('do_exit',
                         editor = ButtonEditor(value = True,
                                               label = "Return to Cytoflow"),
                         show_label = False))
        
    def create_contents(self, parent):
        """ Create and return the toolkit-specific contents of the dock pane.
        """
        self.ui = self.edit_traits(kind="subpanel", 
                                   parent=parent,
                                   context = self.model)
        return self.ui.control

    
# the central pane
@provides(ITaskPane)
class ExportTaskPane(TaskPane):
    """
    The center pane for the UI; contains the matplotlib canvas for plotting
    data views.
    """
    
    id = 'edu.mit.synbio.cytoflow.export_task_pane'
    name = 'Cytometry Data Viewer'
    
    model = Instance(LocalWorkflow)
    handler = Instance(WorkflowController)
    
    layout = Instance(QtGui.QVBoxLayout)                    # @UndefinedVariable
    canvas = Instance(FigureCanvasQTAggLocal)
        
    def create(self, parent):      
        # create a layout for the tab widget and the main view
        self.layout = layout = QtGui.QVBoxLayout()          # @UndefinedVariable
        self.control = QtGui.QWidget()                      # @UndefinedVariable
        self.control.setLayout(layout)

        # usually we would add the main plot here -- but a Qt widget
        # can only be part of one layout at a time.  so instead we
        # need to create that layout here, then dynamically add
        # the canvas when the task is activated (see activate(), below)
        
    def activate(self):
        if self.canvas.layout():
            self.canvas.layout().removeWidget(self.canvas)
        self.layout.addWidget(self.canvas)


class ExportTask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflowgui.export_task"
    name = "Export figure"
    
    menu_bar = SMenuBar(SMenu(TaskToggleGroup(),
                              id = 'View', name = '&View'))
    
    # the main workflow instance.
    model = Instance(LocalWorkflow)
    
    # the handler that connects it to various views
    handler = Instance(WorkflowController)
           
    # side panes
    params_pane = Instance(TraitsDockPane)
    export_pane = Instance(TraitsDockPane)
    
    # additional parameters for exporting
    width = CFloat(11)
    height = CFloat(8.5)
    dpi = CInt(96)
    
    # events for exporting
    do_exit = Event
    do_export = Event
    
    def _default_layout_default(self):
        return TaskLayout(right = VSplitter(PaneItem("edu.mit.synbio.cytoflowgui.plot_params_pane", width = 350),
                                            PaneItem("edu.mit.synbio.cytoflowgui.export_pane", width = 350)))
     
    def create_central_pane(self):
        return ExportTaskPane(canvas = self.application.canvas,
                              model = self.model,
                              handler = self.handler)
     
    def create_dock_panes(self):
        self.params_pane = PlotParamsPane(model = self.model, 
                                          handler = self.handler,
                                          task = self)
         
        self.export_pane = ExportPane(model = self, task = self)
         
        return [self.params_pane, self.export_pane]

    def activated(self):
        self.window.central_pane.activate()
                                
    @observe('do_exit', post_init = True)
    def activate_cytoflow_task(self, _):
        task = next(x for x in self.window.tasks if x.id == 'edu.mit.synbio.cytoflowgui.flow_task')
        self.window.activate_task(task)
        
    @observe('do_export', post_init = True)
    def on_export(self, _):
        """
        Shows a dialog to export a file
        """
                  
        f = ""
        filetypes_groups = self.application.canvas.get_supported_filetypes_grouped()
        filename_exts = []
        for name, ext in filetypes_groups.items():
            if f:
                f += ";"
            f += FileDialog.create_wildcard(name, " ".join(["*." + e for e in ext])) #@UndefinedVariable  
            filename_exts.append(ext)
         
        dialog = FileDialog(parent = self.window.control,
                            action = 'save as',
                            wildcard = f)
         
        if dialog.open() == OK:
            filetypes = list(self.application.canvas.get_supported_filetypes().keys())
            if not [ext for ext in ["." + ext for ext in filetypes] if dialog.path.endswith(ext)]:
                selected_exts = filename_exts[dialog.wildcard_index]
                ext = sorted(selected_exts, key = len)[0]
                dialog.path += "."
                dialog.path += ext

            if (self.width * self.dpi  > 2**16 or \
                self.height * self.dpi > 2**16 or \
                self.width * self.height * self.dpi ** 2 > 2 ** 30) and \
                pathlib.Path(dialog.path).suffix in ['png', 'pgf', 'raw', 'rgba', 'jpg', 'jpeg', 'bmp', 'pcx', 'tif', 'tiff', 'xpm']:
                error(None, "Can't export raster images with a height or width larger than 65535 pixels, "
                            "or a total image size of greater than 2**30 pixels. "
                            "Decrease your image size or DPI, or use a vector format (like PDF or SVG).")
                return     
            
            self.application.canvas.print_figure(dialog.path, 
                                                 bbox_inches = 'tight', 
                                                 width = self.width,
                                                 height = self.height,
                                                 dpi = self.dpi)          
     
        
class ExportFigurePlugin(Plugin):
    """
    An Envisage plugin wrapping ExportTask
    """

    # Extension point IDs.
    PREFERENCES       = 'envisage.preferences'
    PREFERENCES_PANES = 'envisage.ui.tasks.preferences_panes'
    TASKS             = 'envisage.ui.tasks.tasks'
    
    # these need to be declared in a Plugin instance; we pass them to
    # the task instance thru its factory, below.
    op_plugins = ExtensionPoint(List(IOperationPlugin), OP_PLUGIN_EXT)
    view_plugins = ExtensionPoint(List(IViewPlugin), VIEW_PLUGIN_EXT)    

    #### 'IPlugin' interface ##################################################

    # The plugin's unique identifier.
    id = 'edu.mit.synbio.cytoflow.export'
    
    # the local process's model
    model = Instance(LocalWorkflow)

    # The plugin's name (suitable for displaying to the user).
    name = 'Export figure'
    
    ###########################################################################
    # Protected interface.
    ###########################################################################

    preferences = List(contributes_to = PREFERENCES)
    def _preferences_default(self):
        filename = os.path.join(os.path.dirname(__file__), 'preferences.ini')
        return [ 'file://' + filename ]
    
    preferences_panes = List(contributes_to = PREFERENCES_PANES)
    def _preferences_panes_default(self):
        from .preferences import CytoflowPreferencesPane
        return [CytoflowPreferencesPane]

    tasks = List(contributes_to = TASKS)
    def _tasks_default(self):
        return [TaskFactory(id = 'edu.mit.synbio.cytoflowgui.export_task',
                            name = 'Export figure',
                            factory = lambda **x: ExportTask(application = self.application,
                                                             model = self.application.model,
                                                             handler = WorkflowController(model = self.application.model,
                                                                                          op_plugins = self.op_plugins,
                                                                                          view_plugins = self.view_plugins),
                                                             **x))]
