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
cytoflowgui.help_pane
---------------------

Defines the dock pane to show a help page for the currently-selected
operation or view.
"""

import pathlib

from traits.api import Instance, List, observe, Str, HTML
from traitsui.api import View, Item
from pyface.tasks.api import TraitsDockPane, Task
from pyface.qt import QtGui

from cytoflowgui.view_plugins.i_view_plugin import IViewPlugin
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin
from cytoflowgui.util import HintedWidget
from cytoflowgui.editors import ZoomableHTMLEditor

class HelpDockPane(TraitsDockPane):
    """
    A `pyface.tasks.i_dock_pane.IDockPane` to view help 
    for the current `IWorkflowOperation` or `IWorkflowView`.
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.cytoflowgui.help_pane'
    """This pane's GUID"""
    
    name = 'Help'
    """This pane's name"""

    task = Instance(Task)
    """The Task that serves as the controller"""

    view_plugins = List(IViewPlugin)
    """The `IViewPlugin`\s to search for help pages"""
    
    op_plugins = List(IOperationPlugin)
    """The `IOperationPlugin`\s to search for help pages"""
    
    help_id = Str
    """The GUID of the operation or view whose help we're currently showing"""
    
    html = HTML("<b>Welcome to Cytoflow!</b>")
    """The HTML trait containing the current help page"""
    
    traits_view = View(Item('pane.html',
                            editor = ZoomableHTMLEditor(base_url = pathlib.PurePath(__file__).parent.joinpath('help').joinpath('operations').as_posix()),
                            show_label = False))
    
    def create_contents(self, parent):
        """Create the pane's contents, which is just the view's UI"""
        self.ui = self.edit_traits(kind='subpanel', parent=parent)
        
        layout = QtGui.QHBoxLayout()
        control = HintedWidget()
        
        layout.addWidget(self.ui.control)
        control.setLayout(layout)
        control.setParent(parent)
        parent.setWidget(control)

        return control
    
    @observe('model:selected', post_init = True)
    def _on_select_op(self, _):
        if self.model.selected:
            self.help_id = self.model.selected.operation.id
            
    @observe('model:selected:current_view', post_init = True)
    def _on_select_view(self, _):
        if self.model.selected:
            self.help_id = self.model.selected.current_view.id
    
    @observe('help_id', post_init = True)
    def _on_help_id_changed(self, _):
        for plugin in self.view_plugins:
            if self.help_id == plugin.view_id:
                try:
                    self.html = plugin.get_help()
                except AttributeError:
                    pass
                finally:
                    return
                
        for plugin in self.op_plugins:
            if self.help_id == plugin.operation_id:
                try:
                    self.html = plugin.get_help()
                except AttributeError:
                    pass
                finally:
                    return