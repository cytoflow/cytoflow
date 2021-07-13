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

"""
Quadrant Gate
-------------

Draw a "quadrant" gate.  To create a new gate, just click where you'd like the
intersection to be.  Creates a new metadata **Name**, with values ``name_1``,
``name_2``, ``name_3``, ``name_4`` ordered **clockwise from upper-left.**

.. note::

    This matches the order of FACSDiva quad gates.
    

.. object:: Name

    The operation name.  Used to name the new metadata field that's created by 
    this operation.
        
.. object:: X channel

    The name of the channel on the X axis.
        
.. object:: X threshold

    The threshold in the X channel.

.. object:: Y channel

    The name of the channel on the Y axis.
        
.. object:: Y threshold

    The threshold in the Y channel.

.. object:: X Scale

    The scale of the X axis for the interactive plot.
    
.. object:: Y Scale

    The scale of the Y axis for the interactive plot
    
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

    quad = flow.QuadOp(name = "Quad",
                       xchannel = "V2-A",
                       xthreshold = 100,
                       ychannel = "Y2-A",
                       ythreshold = 1000)

    qv = quad.default_view(xscale = 'log', yscale = 'log')
    qv.plot(ex)
"""


from traits.api import provides, List
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor
from envisage.api import Plugin
from pyface.api import ImageResource

from ..view_plugins import ViewHandler
from ..view_plugins.scatterplot import ScatterplotParamsHandler
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..workflow.operations import QuadWorkflowOp, QuadSelectionView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class QuadHandler(OpHandler):
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('xchannel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "X Channel"),
             Item('xthreshold',
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "X Threshold"),
             Item('ychannel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "Y Channel"),
             Item('ythreshold',
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "Y Threshold"),
             shared_op_traits_view) 
        
        
class QuadViewHandler(ViewHandler):
    view_traits_view = \
        View(VGroup(
             VGroup(Item('xchannel', 
                         label = "X Channel",
                         style = "readonly"),
                    Item('xthreshold', 
                         label = "X Threshold",
                         style = "readonly"),
                    Item('xscale',
                         label = "X scale"),
                    Item('ychannel', 
                         label = "Y Channel",
                         style = "readonly"),
                    Item('ythreshold', 
                         label = "Y Threshold",
                         style = "readonly"),
                    Item('yscale',
                         label = "Y Scale"),
                    Item('huefacet',
                         editor=ExtendableEnumEditor(name='context_handler.previous_conditions_names',
                                                     extra_items = {"None" : ""}),
                         label="Color\nFacet"),
                    label = "Quad Setup View",
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
                                                 handler_factory = ScatterplotParamsHandler),
                  style = 'custom',
                  show_label = False))


@provides(IOperationPlugin)
class QuadPlugin(Plugin, PluginHelpMixin): 
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.quad'
    operation_id = 'edu.mit.synbio.cytoflow.operations.quad'
    view_id = 'edu.mit.synbio.cytoflow.views.quad'

    short_name = "Quad"
    menu_group = "Gates"
    
    def get_operation(self):
        return QuadWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, QuadWorkflowOp):
            return QuadHandler(model = model, context = context)
        elif isinstance(model, QuadSelectionView):
            return QuadViewHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('quad')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
