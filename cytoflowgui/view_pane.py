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

from traits.api import Instance, List, on_trait_change, Str, Dict, Bool
from pyface.tasks.api import TraitsDockPane, Task
from pyface.action.api import ToolBarManager
from pyface.tasks.action.api import TaskAction
from pyface.api import ImageResource
from pyface.qt import QtGui, QtCore

from cytoflowgui.view_plugins import IViewPlugin
from cytoflowgui.workflow import WorkflowItem
from cytoflowgui.workflow import LocalWorkflow

class ViewDockPane(TraitsDockPane):
    """
    A DockPane to manipulate the traits of the currently selected view.
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.view_traits_pane'
    name = 'View Properties'

    # the Task that serves as the controller
    task = Instance(Task)

    # the IViewPlugins that the user can possibly choose.  set by the controller
    # as we're instantiated
    view_plugins = List(IViewPlugin)
    
    # changed depending on whether the selected wi in the model is valid.
    enabled = Bool(True)
    
    # the currently selected view id
    selected_view = Str
    
    # if there is a default view for the currently selected operation, this
    # is its view id
    default_view_id = Str

    # task actions associated with views
    _actions = Dict(Str, TaskAction)
    
    # the default task action
    _default_action = Instance(TaskAction)

    def create_contents(self, parent):
        """ 
        Create and return the toolkit-specific contents of the dock pane.
        """
        
        self.toolbar = ToolBarManager(orientation = 'vertical',
                                      show_tool_names = False,
                                      image_size = (32, 32))
        
        self._default_action = TaskAction(name = "Setup View",
                                          on_perform = lambda s=self: 
                                                         self.trait_set(selected_view = s._default_view_id),
                                          image = ImageResource('setup'),
                                          style = 'toggle',
                                          visible = False)
        self.toolbar.append(self._default_action)
        
        for plugin in self.plugins:
            task_action = TaskAction(name = plugin.short_name,
                                     on_perform = lambda view_id=plugin.view_id:
                                                    self.trait_set(selected_view = view_id),
                                     image = plugin.get_icon(),
                                     style = 'toggle')
            self._actions[plugin.view_id] = task_action
            self.toolbar.append(task_action)
            
        window = QtGui.QMainWindow()
        window.addToolBar(QtCore.Qt.RightToolBarArea, 
                          self.toolbar.create_tool_bar(window))
        
        self.ui = self.model.edit_traits(view = 'selected_view_traits',
                                         kind = 'subpanel', 
                                         parent = window)
        window.setCentralWidget(self.ui.control)
        
        window.setParent(parent)
        parent.setWidget(window)
        
        return window
        
    @on_trait_change('enabled', enabled)
    def _enabled_changed(self, enabled):
        self.window.setEnabled(enabled)
        self.ui.control.setEnabled(enabled)
    
    @on_trait_change('default_view_id')
    def set_default_view(self, _, _, old_view_id, new_view_id):
        if old_view_id:
            del self._actions[old_view_id]
            
        if new_view_id:
            self._actions[new_view_id] = self._default_action 
            
        self._default_action.visible = (new_view_id is not None)
            
    @on_trait_change('selected_view')
    def _selected_view_changed(self, view_id):         
        # untoggle everything on the toolbar
        for action in self._actions.itervalues():
            action.checked = False

        # toggle the right button
        self._actions[view_id].checked = True
