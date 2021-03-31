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

import pathlib

from traits.api import Instance, List, observe, Str, HTML
from traitsui.api import View, Item, HTMLEditor
from pyface.tasks.api import TraitsDockPane, Task
from pyface.qt import QtGui

from cytoflowgui.view_plugins.i_view_plugin import IViewPlugin
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin
from cytoflowgui.util import HintedWidget

class HelpDockPane(TraitsDockPane):
    """
    A DockPane to view help for the current module
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.cytoflowgui.help_pane'
    name = 'Help'

    # the Task that serves as the controller
    task = Instance(Task)
    
    view_plugins = List(IViewPlugin)
    op_plugins = List(IOperationPlugin)
    
    help_id = Str
    
    html = HTML("<b>Welcome to Cytoflow!</b>")
    
    traits_view = View(Item('pane.html',
                            editor = HTMLEditor(base_url = pathlib.Path(__file__).parent.joinpath('help').as_posix()),
                            show_label = False))
    
    def create_contents(self, parent):
        
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