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

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, HGroup, \
                         ButtonEditor, InstanceEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, List, Str, HasTraits, \
                       File, Event, Dict, Tuple, Float, on_trait_change, Instance
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations.bleedthrough_linear import BleedthroughLinearOp, BleedthroughLinearDiagnostic
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.vertical_list_editor import VerticalListEditor

class _Control(HasTraits):
    channel = Str
    file = File
    
class BleedthroughLinearHandler(Controller, OpHandlerMixin):
    
    add_control = Event
    remove_control = Event
    
    wi = Instance(WorkflowItem)
    
    def init_info(self, info):
        # this is ugly, but it works.
        if not self.wi:
            self.wi = info.ui.context['context']
    
    # MAGIC: called when add_control is set
    def _add_control_fired(self):
        self.model.controls_list.append(_Control())
        
    def _remove_control_fired(self):
        if self.model.controls_list:
            self.model.controls_list.pop()
            
    def control_traits_view(self):
        return View(HGroup(Item('channel',
                                editor = EnumEditor(name = 'handler.wi.previous.channels')),
                           Item('file',
                                show_label = False)),
                    handler = self)
    
    def default_traits_view(self):
        return View(VGroup(Item('controls_list',
                                editor = VerticalListEditor(editor = InstanceEditor(view = self.control_traits_view()),
                                                            style = 'custom',
                                                            mutable = False),
                                style = 'custom'),
                    Item('handler.add_control',
                         editor = ButtonEditor(value = True,
                                               label = "Add a control")),
                    Item('handler.remove_control',
                         editor = ButtonEditor(value = True,
                                               label = "Remove a control")),
                    label = "Controls",
                    show_labels = False),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous_conditions",
                                                          metadata = "context.previous_metadata",
                                                          when = "'experiment' not in vars() or not experiment")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('context.do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    shared_op_traits)

class BleedthroughLinearPluginOp(PluginOpMixin, BleedthroughLinearOp):
    handler_factory = Callable(BleedthroughLinearHandler)

    controls = Dict(Str, File, transient = True)
    spillover = Dict(Tuple(Str, Str), Float, transient = True)

    controls_list = List(_Control, estimate = True)
        
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
        
    def should_clear_estimate(self, changed):
        """
        Should the owning WorkflowItem clear the estimated model by calling
        op.clear_estimate()?  `changed` can be:
         - "estimate" -- the parameters required to call 'estimate()' (ie
            traits with estimate = True metadata) have changed
         - "prev_result" -- the previous WorkflowItem's result changed
        """
        if changed == "prev_result":
            return False
        
        return True
        
    def clear_estimate(self):
        self.spillover.clear()
        self.changed = "estimate_result"

class BleedthroughLinearViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('context.view_warning',
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
    