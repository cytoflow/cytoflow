#!/usr/bin/env python3.4
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
Threshold Gate
--------------

Draw a threshold gate.  To set a new threshold, click on the plot.

.. object:: Name

    The operation name.  Used to name the new metadata field that's created by 
    this module.
    
.. object:: Channel

    The name of the channel to apply the gate to.

.. object:: Threshold

    The threshold of the gate.
    
.. object:: Scale

    The scale of the axis for the interactive plot
    
.. object:: Hue facet

    Show different experimental conditions in different colors.
    
.. object:: Subset

    Show only a subset of the data.
   
.. plot::

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()

    thresh_op = flow.ThresholdOp(name = 'Threshold',
                                 channel = 'Y2-A',
                                 threshold = 2000)

    thresh_op.default_view(scale = 'log').plot(ex)
    
'''

from traits.api import provides
from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflowgui.op_plugins.i_op_plugin \
    import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits, PluginHelpMixin
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin
from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.workflow.operations.threshold import ThresholdWorkflowOp, ThresholdSelectionView

class ThresholdHandler(OpHandlerMixin, Controller):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('channel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "Channel"),
                    Item('threshold',
                         editor = TextEditor(auto_set = False)),
                    shared_op_traits) 
        
class ThresholdViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('channel', 
                                label = "Channel",
                                style = "readonly"),
                           Item('threshold', 
                                label = "Threshold",
                                style = "readonly"),
                           Item('scale'),
                           Item('huefacet',
                                editor=ExtendableEnumEditor(name='handler.previous_conditions_names',
                                                            extra_items = {"None" : ""}),
                                label="Color\nFacet"),
                           label = "Threshold Setup View",
                           show_border = False),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous_wi.conditions")),
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



@provides(IOperationPlugin)
class ThresholdPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.threshold'
    operation_id = 'edu.mit.synbio.cytoflow.operations.threshold'

    short_name = "Threshold"
    menu_group = "Gates"
    
    def get_operation(self):
        return ThresholdWorkflowOp()
    
    def get_handler(self, model):
        if isinstance(model, ThresholdWorkflowOp):
            return ThresholdHandler(model = model)
        elif isinstance(model, ThresholdSelectionView):
            return ThresholdViewHandler(model = model)

    def get_icon(self):
        return ImageResource('threshold')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self

