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

import os.path, pathlib

from traits.api import Instance, Bool, Any, Event, CFloat, CInt, on_trait_change
from traitsui.api import ButtonEditor, View, TextEditor, Item

from pyface.tasks.api import Task, TaskLayout, PaneItem, TraitsDockPane, VSplitter
from pyface.tasks.action.api import SMenuBar, SMenu, TaskToggleGroup
from envisage.api import Plugin, contributes_to
from envisage.ui.tasks.api import TaskFactory
from pyface.api import FileDialog, OK, error

from cytoflowgui.workflow import Workflow


class PlotParamsPane(TraitsDockPane):
    
    id = 'edu.mit.synbio.cytoflowgui.plot_params_pane'
    name = "Plot Parameters"

    # the task serving as the dock pane's controller
    task = Instance(Task)
    
    closable = False
    dock_area = 'right'
    floatable = False
    movable = False
    visible = True
    
    def create_contents(self, parent):
        """ Create and return the toolkit-specific contents of the dock pane.
        """
        self.ui = self.model.edit_traits(view = 'plot_params_traits',
                                         kind='subpanel', 
                                         parent=parent,
                                         scrollable = True)
        return self.ui.control
    
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

    # the dinky little model that this pane displays
    width = CFloat(11)
    height = CFloat(8.5)
    dpi = CInt(96)
    
    do_exit = Event
    do_export = Event
    
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
    

class ExportTask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflowgui.export_task"
    name = "Export figure"
    
    menu_bar = SMenuBar(SMenu(TaskToggleGroup(),
                              id = 'View', name = '&View'))
    
    # the main workflow instance.
    model = Instance(Workflow)
           
    params_pane = Instance(TraitsDockPane)
    export_pane = Instance(TraitsDockPane)
    
    def _default_layout_default(self):
        return TaskLayout(right = VSplitter(PaneItem("edu.mit.synbio.cytoflowgui.plot_params_pane", width = 350),
                                            PaneItem("edu.mit.synbio.cytoflowgui.export_pane", width = 350)))
     
    def create_central_pane(self):
        return self.application.plot_pane
     
    def create_dock_panes(self):
        self.params_pane = PlotParamsPane(model = self.model, 
                                          task = self)
        
        self.export_pane = ExportPane(task = self)
        
        return [self.params_pane, self.export_pane]
    
    @on_trait_change('export_pane:do_exit', post_init = True)
    def activate_cytoflow_task(self):
        task = next(x for x in self.window.tasks if x.id == 'edu.mit.synbio.cytoflowgui.flow_task')
        self.window.activate_task(task)
        
    @on_trait_change('export_pane:do_export', post_init = True)
    def on_export(self):
        """
        Shows a dialog to export a file
        """
                  
        f = ""
        filetypes_groups = self.application.plot_pane.canvas.get_supported_filetypes_grouped()
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
            filetypes = list(self.application.plot_pane.canvas.get_supported_filetypes().keys())
            if not [ext for ext in ["." + ext for ext in filetypes] if dialog.path.endswith(ext)]:
                selected_exts = filename_exts[dialog.wildcard_index]
                ext = sorted(selected_exts, key = len)[0]
                dialog.path += "."
                dialog.path += ext

            if (self.export_pane.width * self.export_pane.dpi  > 2**16 or \
                self.export_pane.height * self.export_pane.dpi > 2**16 or \
                self.export_pane.width * self.export_pane.height * self.export_pane.dpi ** 2 > 2 ** 30) and \
                pathlib.Path(dialog.path).suffix in ['png', 'pgf', 'raw', 'rgba', 'jpg', 'jpeg', 'bmp', 'pcx', 'tif', 'tiff', 'xpm']:
                error(None, "Can't export raster images with a height or width larger than 65535 pixels, "
                            "or a total image size of greater than 2**30 pixels. "
                            "Decrease your image size or DPI, or use a vector format (like PDF or SVG).")
                return                
            
                 
            self.application.plot_pane.export(dialog.path, 
                                              width = self.export_pane.width,
                                              height = self.export_pane.height,
                                              dpi = self.export_pane.dpi)
     
        
class ExportFigurePlugin(Plugin):
    """
    An Envisage plugin wrapping ExportTask
    """

    # Extension point IDs.
    PREFERENCES       = 'envisage.preferences'
    PREFERENCES_PANES = 'envisage.ui.tasks.preferences_panes'
    TASKS             = 'envisage.ui.tasks.tasks'
    
    debug = Bool(False)
    remote_connection = Any

    #### 'IPlugin' interface ##################################################

    # The plugin's unique identifier.
    id = 'edu.mit.synbio.cytoflow.export'
    
    # the local process's model
    model = Instance(Workflow)

    # The plugin's name (suitable for displaying to the user).
    name = 'Export figure'
    
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
        return [TaskFactory(id = 'edu.mit.synbio.cytoflowgui.export_task',
                            name = 'Export figure',
                            factory = lambda **x: ExportTask(application = self.application,
                                                            model = self.application.model,
                                                            **x))]
