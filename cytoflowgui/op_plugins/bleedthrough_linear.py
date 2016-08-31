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

import warnings

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor, \
                         CheckListEditor, ButtonEditor, Heading, TableEditor, \
                         TableColumn, ObjectColumn
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Bool, CFloat, List, Str, HasTraits, \
                       File, Event, Dict, Tuple, Float, on_trait_change
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
                                              editor = EnumEditor(name = 'context.previous.channels'),
                                              resize_mode = 'fixed',
                                              width = 80),
                                 ObjectColumn(name = 'file',
                                              # 'fixed' with no width stretches to fill table
                                              resize_mode = 'fixed')],
                            row_factory = _Control,
                            sortable = False),
                         show_label = False),
                    Item('add_control',
                         editor = ButtonEditor(value = True,
                                               label = "Add a control"),
                         show_label = False),
                    Item('remove_control',
                         editor = ButtonEditor(value = True,
                                               label = "Remove a control"),
                         show_label = False),
                    VGroup(Item('subset',
                                show_label = False,
                                editor = SubsetEditor(conditions_types = "context.previous.conditions_types",
                                                      conditions_values = "context.previous.conditions_values")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('context.do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    shared_op_traits)

class BleedthroughLinearPluginOp(BleedthroughLinearOp, PluginOpMixin):
    handler_factory = Callable(BleedthroughLinearHandler)

    add_control = Event
    remove_control = Event
    
    controls = Dict(Str, File, transient = True)
    spillover = Dict(Tuple(Str, Str), Float, transient = True)

    controls_list = List(_Control, estimate = True)
    subset = Str(estimate = True)
        
    # MAGIC: called when add_control is set
    def _add_control_fired(self):
        self.controls_list.append(_Control())
        
    def _remove_control_fired(self):
        self.controls_list.pop()
        
    @on_trait_change('controls_list_items,controls_list.+', post_init = True)
    def _controls_changed(self, obj, name, old, new):
        self.changed = "estimate"
    
    def default_view(self, **kwargs):
        return BleedthroughLinearPluginView(op = self, **kwargs)
    
    def estimate(self, experiment):
        for i, control_i in enumerate(self.controls_list):
            for j, control_j in enumerate(self.controls_list):
                if control_i.channel == control_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(control_i.channel))
                                               
        self.controls = {}
        for control in self.controls_list:
            self.controls[control.channel] = control.file
            
        if not self.subset:
            warnings.warn("Are you sure you don't want to specify a subset "
                          "used to estimate the model?",
                          util.CytoflowOpWarning)
                    
        BleedthroughLinearOp.estimate(self, experiment, subset = self.subset)
        
        self.changed = "estimate_result"
        
    def clear_estimate(self):
        self.spillover.clear()
        self.changed = "estimate_result"

class BleedthroughLinearViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         style = 'readonly'),
                    Item('context.view_warning',
                         resizable = True,
                         visible_when = 'context.view_warning',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                 background_color = "#ffff99")),
                    Item('context.view_error',
                         resizable = True,
                         visible_when = 'context.view_error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191")))

@provides(IView)
class BleedthroughLinearPluginView(BleedthroughLinearDiagnostic, PluginViewMixin):
    handler_factory = Callable(BleedthroughLinearViewHandler)
    
    def plot_wi(self, wi):
        self.plot(wi.previous.result)

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
    