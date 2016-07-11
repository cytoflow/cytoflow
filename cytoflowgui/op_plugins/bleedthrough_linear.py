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

'''
Created on Oct 9, 2015

@author: brian
'''

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor, \
                         CheckListEditor, ButtonEditor, Heading, TableEditor, \
                         TableColumn, ObjectColumn
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Bool, CFloat, List, Str, HasTraits, \
                       File, Event
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations.bleedthrough_linear import BleedthroughLinearOp, BleedthroughLinearDiagnostic
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

class _Control(HasTraits):
    channel = Str
    file = File

class BleedthroughLinearHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('controls_list',
                         editor=TableEditor(
                            columns = 
                                [ObjectColumn(name = 'channel',
                                              editor = EnumEditor(name = 'context.previous.channels')),
                                 ObjectColumn(name = 'file')],
                            row_factory = _Control,
                            auto_size = False,
                            sortable = False),
                         show_label = False),
                    Item('add_control',
                         editor = ButtonEditor(value = True,
                                               label = "Add a control"),
                         show_label = False),
                    Item('context.estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    shared_op_traits)

class BleedthroughLinearPluginOp(BleedthroughLinearOp, PluginOpMixin):
    handler_factory = Callable(BleedthroughLinearHandler)

    add_control = Event
    controls_list = List(_Control)
    
    # MAGIC: called when add_control is set
    def _add_control_fired(self):
        self.controls_list.append(_Control())
    
    def default_view(self, **kwargs):
        return BleedthroughLinearPluginView(op = self, **kwargs)
    
    def estimate(self, experiment, subset = None):
        for i, control_i in enumerate(self.controls_list):
            for j, control_j in enumerate(self.controls_list):
                if control_i.channel == control_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(control_i.channel))
                                               
        controls = {}
        for control in self.controls_list:
            controls[control.channel] = control.file
            
        self.controls = controls
        
        BleedthroughLinearOp.estimate(self, experiment, subset)

class BleedthroughLinearViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         style = 'readonly'),
                    Item('warning',
                         resizable = True,
                         visible_when = 'warning',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                 background_color = "#ffff99")),
                    Item('error',
                         resizable = True,
                         visible_when = 'error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191")))

@provides(IView)
class BleedthroughLinearPluginView(BleedthroughLinearDiagnostic, PluginViewMixin):
    handler_factory = Callable(BleedthroughLinearViewHandler)
    
    def plot_wi(self, wi):
        if self.op.by and not wi.current_plot:
            return
        self.plot(wi.previous.result, wi.current_plot)

@provides(IOperationPlugin)
class BleedthroughLinearPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.bleedthrough_linear'
    operation_id = 'edu.mit.synbio.cytoflow.operations.bleedthrough_linear'

    short_name = "Linear Compensation"
    menu_group = "Gates"
    
    def get_operation(self):
        return BleedthroughLinearPluginOp()
    
    def get_icon(self):
        return ImageResource('bleedthrough_linear')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    