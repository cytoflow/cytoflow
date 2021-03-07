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

from traits.api import Instance, List, on_trait_change, Str, Dict, Bool, Tuple, observe
from pyface.tasks.api import TraitsDockPane, Task
from pyface.action.api import ToolBarManager
from pyface.tasks.action.api import TaskAction
from pyface.api import ImageResource
from pyface.qt import QtGui, QtCore

from .workflow_controller import WorkflowController
from .view_plugins import IViewPlugin
from .util import HintedMainWindow
    

class ViewDockPane(TraitsDockPane):
    """
    A DockPane to manipulate the traits of the currently selected view.
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.cytoflowgui.view_traits_pane'
    name = 'View Properties'

    # the Task that serves as the controller
    task = Instance(Task)

    # the IViewPlugins that the user can possibly choose.  set by the controller
    # as we're instantiated
    view_plugins = List(IViewPlugin)
    
    # controller
    handler = Instance(WorkflowController)
    
    # changed depending on whether the selected wi in the model is valid.
#     enabled = Bool(False)
    
    # the currently selected view id
#     selected_view = Str
    
    # if there is a default view for the currently selected operation, this
    # is its view id
#     default_view = Str

    # the size of the toolbar icons IN INCHES
    image_size = Tuple((0.33, 0.33))
    
    # task actions associated with views
    _actions = Dict(Str, TaskAction)
    
    # the default task action
    _default_action = Instance(TaskAction)
    
    _window = Instance(QtGui.QMainWindow)

    def create_contents(self, parent):
        """ 
        Create and return the toolkit-specific contents of the dock pane.
        """
        
        dpi = self.control.physicalDpiX()
        image_size = (int(self.image_size[0] * dpi),
                      int(self.image_size[1] * dpi))
        
        self.toolbar = ToolBarManager(orientation = 'vertical',
                                      show_tool_names = False,
                                      image_size = image_size)
        
        self._default_action = TaskAction(name = "Setup View",
                                          on_perform = lambda: self.handler.activate_view('default'),
                                          image = ImageResource('setup'),
                                          style = 'toggle',
                                          visible = False)
        self.toolbar.append(self._default_action)
        
        for plugin in self.plugins:
            task_action = TaskAction(name = plugin.short_name,
                                     on_perform = lambda view_id=plugin.view_id: self.handler.activate_view(view_id),
                                     image = plugin.get_icon(),
                                     style = 'toggle')
            self._actions[plugin.view_id] = task_action
            self.toolbar.append(task_action)
            
        self._window = window = HintedMainWindow()
        window.addToolBar(QtCore.Qt.RightToolBarArea, 
                          self.toolbar.create_tool_bar(window))
        
        self.ui = self.handler.edit_traits(view = 'selected_view_traits',
                                           context = self.model,
                                           kind = 'subpanel', 
                                           parent = window)
        
        window.setCentralWidget(self.ui.control)
        
        window.setParent(parent)
        parent.setWidget(window)
        window.setEnabled(False)
        
        return window
        
    @observe('model:selected:status')
    def _selected_status_changed(self, event):
        if event.new == 'valid':
            self._window.setEnabled(True)
            self.ui.control.setEnabled(True)
        else:
            self._window.setEnabled(False)
            self.ui.control.setEnabled(False)
            
#     @observe('model:selected')
#     def _selected_changed(self, event):
#         if event.new is None:
#             self._window.setEnabled(False)
#             self.ui.control.setEnabled(False)
#             return 
#         
#         if self.model.selected.default_view:
#             self._default_
#             self._default_action.visible = True
#             
#     
#     @on_trait_change('default_view')
#     def set_default_view(self, obj, name, old_view_id, new_view_id):
#         if old_view_id:
#             del self._actions[old_view_id]
#             
#         if new_view_id:
#             self._actions[new_view_id] = self._default_action 
#             
#         self._default_action.visible = (new_view_id != "")
#             
#     @on_trait_change('selected_view')
#     def _selected_view_changed(self, view_id):         
#         # untoggle everything on the toolbar
#         for action in self._actions.values():
#             action.checked = False
# 
#         # toggle the right button
#         if view_id:
#             self._actions[view_id].checked = True
            
class PlotParamsPane(TraitsDockPane):
    
    id = 'edu.mit.synbio.cytoflowgui.params_pane'
    name = "Plot Parameters"
    
    # controller
    handler = Instance(WorkflowController)
    
    closable = True
    dock_area = 'right'
    floatable = True
    movable = True
    visible = True

    
    def create_contents(self, parent):
        """ Create and return the toolkit-specific contents of the dock pane.
        """
    
        self.ui = self.handler.edit_traits(view = 'selected_view_params',
                                           context = self.model,
                                           kind='subpanel', 
                                           parent=parent,
                                           scrollable = True)
        return self.ui.control
