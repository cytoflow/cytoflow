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

from traits.api import Instance, List, on_trait_change, Str, Dict, Bool, HTML
from traitsui.api import View, Item, HTMLEditor
from pyface.tasks.api import TraitsDockPane, Task
from pyface.action.api import ToolBarManager
from pyface.tasks.action.api import TaskAction
from pyface.api import ImageResource
from pyface.qt import QtGui, QtCore

from cytoflowgui.view_plugins import IViewPlugin

class HelpDockPane(TraitsDockPane):
    """
    A DockPane to view help for the current module
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.help_pane'
    name = 'Help'

    # the Task that serves as the controller
    task = Instance(Task)
    
    html = HTML("Some default HTML")
    
    traits_view = View(Item('html',
                            show_label = False))