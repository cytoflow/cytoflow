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
Color Translation
-----------------

Translate measurements from one color's scale to another, using a two-color
or three-color control.
    
To use, set up the **Controls** list with the channels to convert and the FCS 
files to compute the mapping.  Click **Estimate** and make sure to check that 
the diagnostic plots look good.
    
.. object:: Add Control, Remove Control

    Add and remove controls to compute the channel mappings.
    
.. object:: Use mixture model?

    If ``True``, try to model the **from** channel as a mixture of expressing
    cells and non-expressing cells (as you would get with a transient
    transfection), then weight the regression by the probability that the
    the cell is from the top (transfected) distribution.  Make sure you 
    check the diagnostic plots to see that this worked!
    
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
    import_op.tubes = [flow.Tube(file = "tasbe/mkate.fcs")]
    ex = import_op.apply()

    color_op = flow.ColorTranslationOp()
    color_op.controls = {("Pacific Blue-A", "FITC-A") : "tasbe/rby.fcs",
                         ("PE-Tx-Red-YG-A", "FITC-A") : "tasbe/rby.fcs"}
    color_op.mixture_model = True

    color_op.estimate(ex)
    color_op.default_view().plot(ex)  
    ex = color_op.apply(ex)  
'''

from natsort import natsorted

from traits.api import provides, Event, Property, List, Str
from traitsui.api import View, Item, VGroup, ButtonEditor, FileEditor, HGroup, EnumEditor, Controller
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..view_plugins import ViewHandler
from ..editors import ColorTextEditor, InstanceHandlerEditor, VerticalListEditor, SubsetListEditor
from ..workflow.operations import ColorTranslationWorkflowOp, ColorTranslationWorkflowView, ColorTranslationControl
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class ControlHandler(Controller):
    control_view = View(HGroup(Item('from_channel',
                                    editor = EnumEditor(name = 'context_handler.channels')),
                               Item('to_channel',
                                    editor = EnumEditor(name = 'context_handler.channels')),
                               Item('file',
                                    editor = FileEditor(dialog_style = 'open'),
                                    show_label = False)))
    

class ColorTranslationHandler(OpHandler):
    add_control = Event
    remove_control = Event
    
    channels = Property(List(Str), observe = 'context.channels')

    operation_traits_view = \
        View(VGroup(
             Item('controls_list',
                  editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'control_view',
                                                                             handler_factory = ControlHandler),
                                                     style = 'custom',
                                                     mutable = False)),
             Item('handler.add_control',
                  editor = ButtonEditor(value = True,
                                        label = "Add a control")),
             Item('handler.remove_control',
                  editor = ButtonEditor(value = True,
                                        label = "Remove a control")),
             label = "Controls",
             show_labels = False),
             Item('mixture_model',
                  label = "Use mixture\nmodel?"),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "context_handler.previous_conditions",
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory))),
                    label = "Subset",
                    show_border = False,
                    show_labels = False),
             Item('do_estimate',
                  editor = ButtonEditor(value = True,
                                        label = "Estimate!"),
                  show_label = False),
             shared_op_traits_view)
        
        
    # MAGIC: called when add_control is set
    def _add_control_fired(self):
        self.model.controls_list.append(ColorTranslationControl())
        
    def _remove_control_fired(self):
        if self.model.controls_list:
            self.model.controls_list.pop()
            
    # MAGIC: returns the value of the 'channels' property
    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return [] 


class ColorTranslationViewHandler(ViewHandler):
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


@provides(IOperationPlugin)
class ColorTranslationPlugin(Plugin, PluginHelpMixin):
 
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.color_translation'
    operation_id = 'edu.mit.synbio.cytoflow.operations.color_translation'
    view_id = 'edu.mit.synbio.cytoflow.view.colortranslationdiagnostic'

    name = "Color Translation"
    menu_group = "Gates"
    
    def get_operation(self):
        return ColorTranslationWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, ColorTranslationWorkflowOp):
            return ColorTranslationHandler(model = model, context = context)
        elif isinstance(model, ColorTranslationWorkflowView):
            return ColorTranslationViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('color_translation')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
    
