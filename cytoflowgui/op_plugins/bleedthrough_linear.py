#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
    
.. note::

    You cannot have any operations before this one which estimate model
    parameters based on experimental conditions.  (Eg, you can't use a
    **Density Gate** to choose morphological parameters and set *by* to an
    experimental condition.)  If you need this functionality, you can access it 
    using the Python module interface.
    
.. plot:: 
   :include-source: False

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
from natsort import natsorted
import itertools as it

from traits.api import HasTraits, provides, Event, Property, List, Str, BaseFloat
from traitsui.api import View, Item, VGroup, ButtonEditor, FileEditor, HGroup, \
                         EnumEditor, Controller, OKCancelButtons, TableEditor, \
                         ObjectColumn


from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..view_plugins import ViewHandler
from ..editors import ColorTextEditor, InstanceHandlerEditor, VerticalListEditor, SubsetListEditor
from ..workflow.operations import BleedthroughLinearWorkflowOp, BleedthroughLinearWorkflowView, BleedthroughChannel
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class ChannelHandler(Controller):
    channel_view = View(HGroup(Item('channel',
                                    editor = EnumEditor(name = 'context_handler.channels')),
                               Item('file',
                                    editor = FileEditor(dialog_style = 'open'),
                                    show_label = False)))
    
    
class BleedthroughLinearHandler(OpHandler):
    add_channel = Event
    remove_channel = Event
    edit_matrix = Event
        
    channels = Property(List(Str), observe = 'context.channels')
     
    operation_traits_view = \
        View(VGroup(VGroup(
             Item('channels_list',
                  editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'channel_view',
                                                                             handler_factory = ChannelHandler),
                                              style = 'custom',
                                              mutable = False)),
             Item('handler.add_channel',
                  editor = ButtonEditor(value = True,
                                        label = "Add a control")),
             Item('handler.remove_channel',
                  editor = ButtonEditor(value = True,
                                        label = "Remove a control")),
             label = "Channels",
             show_labels = False),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "context_handler.previous_conditions",
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory))),
                    label = "Subset",
                    show_border = False,
                    show_labels = False),
             HGroup(Item('handler.edit_matrix',
                         editor = ButtonEditor(value = True,
                                               label = "Edit matrix..."),
                         show_label = False),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False)),
             shared_op_traits_view))
        

    # MAGIC: called when add_control is set
    def _add_channel_fired(self):
        self.model.channels_list.append(BleedthroughChannel())
        
    # MAGIC: called when remove_control is set
    def _remove_channel_fired(self):
        if self.model.channels_list:
            self.model.channels_list.pop()
            
    # MAGIC: called when edit_matrix is set
    def _edit_matrix_fired(self):
        handler = BleedthroughMatrixHandler(model = self.model)
        handler.edit_traits(kind = 'livemodal') 
            
    # MAGIC: returns the value of the 'channels' property
    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return [] 


class BleedthroughLinearViewHandler(ViewHandler):
    view_traits_view = \
        View(Item('context.view_warning',
                  resizable = True,
                  visible_when = 'context.view_warning',
                  editor = ColorTextEditor(foreground_color = "#000000",
                                          background_color = "#ffff99")),
             Item('context.view_error',
                  resizable = True,
                  visible_when = 'context.view_error',
                  editor = ColorTextEditor(foreground_color = "#000000",
                                           background_color = "#ff9191")))

    view_params_view = View()
    
    
class UnitFloat(BaseFloat):
    def validate(self, obj, name, value):
        value = super().validate(obj, name, value)
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value
    
    
class Spillover(HasTraits):
    from_channel = Str
    to_channel = Str
    spillover = UnitFloat
    

class BleedthroughMatrixHandler(Controller):
    
    spillover_list = List(Spillover)
        
    matrix_view = \
        View(Item('handler.spillover_list',
                  editor = TableEditor(columns = [ObjectColumn(name = 'from_channel',
                                                               label = "From",
                                                               editable = False),
                                                  ObjectColumn(name = 'to_channel',
                                                               label = "To",
                                                               editable = False),
                                                  ObjectColumn(name = 'spillover',
                                                               label = "Spillover")],
                                       rows = 5,
                                       editable = True,
                                       auto_size = True,
                                       configurable = False),
                  show_label = False),
             buttons = OKCancelButtons)
        
    def init(self, _) -> bool:
        channels = list(it.permutations([c.channel for c in self.model.channels_list], 2))
        self.spillover_list = [Spillover(from_channel = c[0],
                                         to_channel = c[1],
                                         spillover = self.model.spillover.get(c, 0.0)) for c in channels]
        return True
    
    def closed(self, _, is_ok):
        if is_ok:
            self.model.spillover = {(s.from_channel, s.to_channel) : s.spillover for s in self.spillover_list}
        
        return True


@provides(IOperationPlugin)
class BleedthroughLinearPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.bleedthrough_linear'
    operation_id = 'edu.mit.synbio.cytoflow.operations.bleedthrough_linear'
    view_id = 'edu.mit.synbio.cytoflow.view.linearbleedthroughdiagnostic'

    short_name = "Linear Compensation"
    menu_group = "Gates"
    
    def get_operation(self):
        return BleedthroughLinearWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, BleedthroughLinearWorkflowOp):
            return BleedthroughLinearHandler(model = model, context = context)
        elif isinstance(model, BleedthroughLinearWorkflowView):
            return BleedthroughLinearViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('bleedthrough_linear')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
