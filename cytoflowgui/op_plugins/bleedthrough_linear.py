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

'''
Linear Bleedthrough Compensation
--------------------------------

Apply matrix-based bleedthrough correction to a set of fluorescence channels.

This is a traditional matrix-based compensation for bleedthrough.  For each
pair of channels, the module estimates the proportion of the first channel
that bleeds through into the second, then performs a matrix multiplication to 
compensate the raw data.

This works best on data that has had autofluorescence removed first;
if that is the case, then the autofluorescence will be subtracted from
the single-color controls too.

To use, specify the single-color control files and which channels they should
be measured in, then click **Estimate**.  Check the diagnostic plot to make sure
the estimation looks good.  There must be at least two channels corrected.

.. object:: Add Control, Remove Control

    Add or remove single-color controls.
    
.. object: Subset

    If you specify a subset here, only that data will be used to calculate the
    bleedthrough matrix.  For example, if you applied a gate to the morphological
    channels, that gate can be specified here to restrict the estimation to
    only events that are in that gate.
    
.. plot:: 

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "tasbe/rby.fcs")]
    ex = import_op.apply()
    
    af_op = flow.AutofluorescenceOp()
    af_op.channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"]
    af_op.blank_file = "tasbe/blank.fcs"

    af_op.estimate(ex)
    ex2 = af_op.apply(ex)

    bl_op = flow.BleedthroughLinearOp()
    bl_op.controls = {'Pacific Blue-A' : 'tasbe/ebfp.fcs',
                      'FITC-A' : 'tasbe/eyfp.fcs',
                      'PE-Tx-Red-YG-A' : 'tasbe/mkate.fcs'}    

    bl_op.estimate(ex2)
    bl_op.default_view().plot(ex2)  

    ex2 = bl_op.apply(ex2)  
'''

import warnings

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, HGroup, \
                         ButtonEditor, InstanceEditor
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, List, Str, HasTraits, Property,
                        File, Event, Dict, Tuple, Float, on_trait_change)
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations.bleedthrough_linear import BleedthroughLinearOp as _BleedthroughLinearOp, BleedthroughLinearDiagnostic
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.vertical_list_editor import VerticalListEditor
from cytoflowgui.workflow import Changed
from cytoflowgui.serialization import camel_registry

class _Control(HasTraits):
    channel = Str
    file = File
    
class BleedthroughLinearHandler(OpHandlerMixin, Controller):
    
    add_control = Event
    remove_control = Event
        
    # MAGIC: called when add_control is set
    def _add_control_fired(self):
        self.model.controls_list.append(_Control())
        
    def _remove_control_fired(self):
        if self.model.controls_list:
            self.model.controls_list.pop()
            
    def control_traits_view(self):
        return View(HGroup(Item('channel',
                                editor = EnumEditor(name = 'handler.context.previous_wi.channels')),
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
                                editor = SubsetListEditor(conditions = "handler.context.previous_wi.conditions",
                                                          metadata = "handler.context.previous_wi.metadata",
                                                          when = "'experiment' not in vars() or not experiment")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    shared_op_traits)

class BleedthroughLinearOp(PluginOpMixin, _BleedthroughLinearOp):
    handler_factory = Callable(BleedthroughLinearHandler)

    controls = Dict(Str, File, transient = True)
    spillover = Dict(Tuple(Str, Str), Float, transient = True)

    controls_list = List(_Control, estimate = True)
        
    @on_trait_change('controls_list_items,controls_list.+', post_init = True)
    def _controls_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('controls_list', self.controls_list))
        
    subset_list = List(ISubset, estimate = True)    
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change('subset_list.str', post_init = True)
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('subset_list', self.subset_list))
    
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
                    
        _BleedthroughLinearOp.estimate(self, experiment, subset = self.subset)
        
        self.changed = (Changed.ESTIMATE_RESULT, self)
        
    def should_clear_estimate(self, changed):
        if changed == Changed.ESTIMATE:
            return True
        
        return False
        
    def clear_estimate(self):
        self.spillover.clear()
        self.changed = (Changed.ESTIMATE_RESULT, self)

class BleedthroughLinearViewHandler(ViewHandlerMixin, Controller):
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
class BleedthroughLinearPluginView(PluginViewMixin, BleedthroughLinearDiagnostic):
    handler_factory = Callable(BleedthroughLinearViewHandler)
    
    def plot_wi(self, wi):
        self.plot(wi.previous_wi.result)
        
    def should_plot(self, changed):
        if changed == Changed.ESTIMATE_RESULT:
            return True
        
        return False

@provides(IOperationPlugin)
class BleedthroughLinearPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.bleedthrough_linear'
    operation_id = 'edu.mit.synbio.cytoflow.operations.bleedthrough_linear'

    short_name = "Linear Compensation"
    menu_group = "Gates"
    
    def get_operation(self):
        return BleedthroughLinearOp()
    
    def get_icon(self):
        return ImageResource('bleedthrough_linear')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
### Serialization
@camel_registry.dumper(BleedthroughLinearOp, 'bleedthrough-linear', version = 1)
def _dump(op):
    return dict(controls_list = op.controls_list,
                subset_list = op.subset_list)
                
@camel_registry.loader('bleedthrough-linear', version = 1)
def _load(data, version):
    return BleedthroughLinearOp(**data)

@camel_registry.dumper(_Control, 'bleedthrough-linear-control', version = 1)
def _dump_control(control):
    return dict(channel = control.channel,
                file = control.file)
    
@camel_registry.loader('bleedthrough-linear-control', version = 1)
def _load_control(data, version):
    return _Control(**data)

@camel_registry.dumper(BleedthroughLinearPluginView, 'bleedthrough-linear-view', version = 1)
def _dump_view(view):
    return dict(op = view.op)

@camel_registry.loader('bleedthrough-linear-view', version = 1)
def _load_view(data, version):
    return BleedthroughLinearPluginView(**data)
                