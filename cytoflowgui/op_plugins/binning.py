#!/usr/bin/env python3.8
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

'''
Binning
-------

Bin data along an axis.

This operation creates equally spaced bins (in linear or log space)
along an axis and adds a condition assigning each event to a bin.  The
value of the event's condition is the left end of the bin's interval in
which the event is located.

.. object:: Name

    The name of the new condition created by this operation.
    
.. object:: Channel

    The channel to apply the binning to.
    
.. object:: Scale

    The scale to apply to the channel before binning.
    
.. object:: Bin Width

    How wide should each bin be?  Can only set if **Scale** is *linear* or
    *log* (in which case, **Bin Width** is in log10-units.)

.. plot::

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "tasbe/rby.fcs")]
    ex = import_op.apply()

    bin_op = flow.BinningOp()
    bin_op.name = "Bin"
    bin_op.channel = "FITC-A"
    bin_op.scale = "log"
    bin_op.bin_width = 0.2

    ex2 = bin_op.apply(ex)

    bin_op.default_view().plot(ex2) 
'''

from traits.api import provides
from traitsui.api import (View, Item, EnumEditor, VGroup, TextEditor, 
                          CheckListEditor, ButtonEditor)
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from ..view_plugins import ViewHandler
from ..view_plugins.histogram import HistogramParamsHandler
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..workflow.operations import BinningWorkflowOp, BinningWorkflowView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin

class BinningHandler(OpHandler):
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('channel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "Channel"),
             Item('scale',
                  editor = EnumEditor(values = ['linear', 'log'])),
             Item('bin_width',
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "Bin Width"),
             shared_op_traits_view)


class BinningViewHandler(ViewHandler):
    view_traits_view = \
        View(VGroup(
             VGroup(Item('channel',
                         style = 'readonly'),
                    label = "Binning Default Plot",
                    show_border = False)),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "context_handler.previous_conditions",
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory),
                                                   mutable = False)),
                    label = "Subset",
                    show_border = False,
                    show_labels = False),
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

    view_params_view = \
        View(Item('plot_params',
                  editor = InstanceHandlerEditor(view = 'view_params_view',
                                                 handler_factory = HistogramParamsHandler),
                  style = 'custom',
                  show_label = False))
        

@provides(IOperationPlugin)
class BinningPlugin(Plugin, PluginHelpMixin):
 
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.binning'
    operation_id = 'edu.mit.synbio.cytoflow.operations.binning'
    view_id = 'edu.mit.synbio.cytoflow.views.binning'

    short_name = "Binning"
    menu_group = "Gates"
    
    def get_operation(self):
        return BinningWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, BinningWorkflowOp):
            return BinningHandler(model = model, context = context)
        elif isinstance(model, BinningWorkflowView):
            return BinningViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('binning')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

