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
Range Gate
----------

Draw a range gate.  To draw a new range, click-and-drag across the plot.

.. object:: Name

    The operation name.  Used to name the new metadata field that's created by 
    this module.
    
.. object:: Channel

    The name of the channel to apply the gate to.

.. object:: Low

    The low threshold of the gate.
    
.. object:: High

    The high threshold of the gate.
    
.. object:: Scale

    The scale of the axis for the interactive plot
    
.. object:: Hue facet

    Show different experimental conditions in different colors.
    
.. object:: Subset

    Show only a subset of the data.
   
.. plot::
   :include-source: False

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()

    range_op = flow.RangeOp(name = 'Range',
                            channel = 'Y2-A',
                            low = 2000,
                            high = 10000)

    range_op.default_view(scale = 'log').plot(ex)

'''

from traits.api import provides, List
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor
from envisage.api import Plugin
from pyface.api import ImageResource

from ..view_plugins import ViewHandler
from ..view_plugins.histogram import HistogramParamsHandler
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..workflow.operations import RangeWorkflowOp, RangeSelectionView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class RangeHandler(OpHandler):
    
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False)),
             Item('channel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "Channel"),
             Item('low',
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "Low"),
             Item('high',
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "High"),
             shared_op_traits_view) 
        
class RangeViewHandler(ViewHandler):
    view_traits_view = \
        View(VGroup(
             VGroup(Item('channel', 
                         label = "Channel",
                         style = "readonly"),
                    Item('scale'),
                    Item('huefacet',
                         editor=ExtendableEnumEditor(name='context_handler.previous_conditions_names',
                                                     extra_items = {"None" : ""}),
                         label="Color\nFacet"),
                     label = "Range Setup View",
                     show_border = False),
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
                                           background_color = "#ff9191"))))

    view_params_view = \
        View(Item('plot_params',
                  editor = InstanceHandlerEditor(view = 'view_params_view',
                                                 handler_factory = HistogramParamsHandler),
                  style = 'custom',
                  show_label = False))
    


@provides(IOperationPlugin)
class RangePlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.range'
    operation_id = 'edu.mit.synbio.cytoflow.operations.range'
    view_id = 'edu.mit.synbio.cytoflow.views.range'

    short_name = "Range"
    menu_group = "Gates"
    
    def get_operation(self):
        return RangeWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, RangeWorkflowOp):
            return RangeHandler(model = model, context = context)
        elif isinstance(model, RangeSelectionView):
            return RangeViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('range')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
