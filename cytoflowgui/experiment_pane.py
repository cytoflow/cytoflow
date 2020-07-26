#!/usr/bin/env python3.6
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2020
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

from traits.api import Instance, List, on_trait_change, Str, HTML
from traitsui.api import View, Item, HTMLEditor
from pyface.tasks.api import TraitsDockPane, Task
from pyface.qt import QtGui

from cytoflowgui.view_plugins import IViewPlugin
from cytoflowgui.op_plugins import IOperationPlugin
from cytoflowgui.util import HintedWidget

class ExperimentDockPane(TraitsDockPane):
    """
    A DockPane to show the Experiment's conditions and statistics
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.cytoflowgui.experiment_pane'
    name = 'Experiment'

    # the Task that serves as the controller
    task = Instance(Task)
    
    view_plugins = List(IViewPlugin)
    op_plugins = List(IOperationPlugin)
    
    traits_view = View(Item('html',
                            editor = HTMLEditor(base_url = pathlib.Path(__file__).parent.joinpath('help').as_posix()),
                            show_label = False))