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

import os, pathlib, urllib, urllib.parse

from traits.api import Instance, List, on_trait_change, Str, HTML
from traitsui.api import View, Item, HTMLEditor
from pyface.tasks.api import TraitsDockPane, Task

from cytoflowgui.view_plugins import IViewPlugin
from cytoflowgui.op_plugins import IOperationPlugin

class HelpDockPane(TraitsDockPane):
    """
    A DockPane to view help for the current module
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.help_pane'
    name = 'Help'

    # the Task that serves as the controller
    task = Instance(Task)
    
    view_plugins = List(IViewPlugin)
    op_plugins = List(IOperationPlugin)
    
    help_id = Str
    
    html = HTML("<b>Welcome to Cytoflow!</b>")
    
    traits_view = View(Item('html',
                            editor = HTMLEditor(base_url = pathlib.Path(__file__).parent.joinpath('help').as_posix()),
                            show_label = False))

    
    @on_trait_change('help_id', post_init = True)
    def _on_help_id_changed(self):
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