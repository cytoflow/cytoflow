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
    # would use a direct listener, but valid gets changed outside
    # the UI thread and we can't change UI things from other threads.
    enabled = Bool(True)
    
    # actions associated with views
    _actions = Dict(Str, TaskAction)
    
    # the default action
    _default_action = Instance(TaskAction)

    def create_contents(self, parent):
        """ 
        Create and return the toolkit-specific contents of the dock pane.
        """
        
        self.toolbar = ToolBarManager(orientation = 'vertical',
                                      show_tool_names = False,
                                      image_size = (32, 32))
        
        self._default_action = TaskAction(name = "Setup View",
                                          on_perform = lambda: self.task.set_current_view("default"),
                                          image = ImageResource('setup'),
                                          style = 'toggle',
                                          visible = False)
        self._actions["default"] = self._default_action
        self.toolbar.append(self._default_action)
        
        for plugin in self.plugins:
            task_action = TaskAction(name = plugin.short_name,
                                     on_perform = lambda view_id=plugin.view_id:
                                                    self.task.set_current_view(view_id),
                                     image = plugin.get_icon(),
                                     style = 'toggle')
            self._actions[plugin.view_id] = task_action
            self.toolbar.append(task_action)
            
        window = QtGui.QMainWindow()
        window.addToolBar(QtCore.Qt.RightToolBarArea, 
                          self.toolbar.create_tool_bar(window))
        
        self.ui = self.model.edit_traits(view = 'current_view_view',
                                         kind = 'subpanel', 
                                         parent = window)
        window.setCentralWidget(self.ui.control)
        
        window.setParent(parent)
        parent.setWidget(window)
        
        return window
        
    # MAGIC: called when enabled is changed
    def _enabled_changed(self, name, old, new):
        self.ui.control.setEnabled(new)

    @on_trait_change('task:model:selected.current_view')
    def _model_current_view_changed(self, obj, name, old, new):
        # at the moment, this only gets called from the UI thread, so we can
        # do UI things.   we get notified if *either* the currently selected 
        # workflowitem *or* the current view changes.
         
        # untoggle everything on the toolbar
        for action in self._actions.itervalues():
            action.checked = False
   
        if name == 'selected':
            old = old.current_view if old else None
            new = new.current_view if new else None
        
        # toggle the right button
        try:
            self.current_view_handler = new.handler
            if new == self.task.model.selected.default_view:
                self._default_action.checked = True
            else:
                self._actions[new.id].checked = True
        except AttributeError:
            self.current_view_handler = None
            
    @on_trait_change('task:model:selected.default_view')
    def _default_view_changed(self, obj, name, old, new):
        # TODO - this is ugly.  fixme.
        new_view = (new.default_view 
                    if isinstance(obj, LocalWorkflow) 
                       and isinstance(new, WorkflowItem)
                    else new)
         
        if new_view is None:
            self._default_action.visible = False
        else:
            self._default_action.visible = True
