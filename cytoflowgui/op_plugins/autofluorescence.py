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
Autofluorescence correction
---------------------------

Apply autofluorescence correction to a set of fluorescence channels.

This module estimates the arithmetic median fluorescence from cells that are
not fluorescent, then subtracts the median from the experimental data.

Check the diagnostic plot to make sure that the sample is actually 
non-fluorescent, and that the module found the population median.

.. object:: Channels

    The channels to correct

.. object:: Blank file

    The FCS file containing measurements of blank cells.
    
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
    af_op.default_view().plot(ex) 

'''
from traits.api import provides, List
from traitsui.api import View, Item, VGroup, CheckListEditor, ButtonEditor, FileEditor
from envisage.api import Plugin
from pyface.api import ImageResource

from ..view_plugins import ViewHandler
from ..editors import SubsetListEditor, ColorTextEditor, InstanceHandlerEditor
from ..workflow.operations import AutofluorescenceWorkflowOp, AutofluorescenceWorkflowView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin

class AutofluorescenceHandler(OpHandler):
    
    operation_traits_view = \
        View(Item('blank_file',
                  editor = FileEditor(dialog_style = 'open')),
             Item('channels',
                  editor = CheckListEditor(cols = 2,
                                           name = 'context_handler.previous_channels'),
                  style = 'custom'),
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


class AutofluorescenceViewHandler(ViewHandler):
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
class AutofluorescencePlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.op_plugins.autofluorescence'
    operation_id = 'edu.mit.synbio.cytoflow.operations.autofluorescence'
    view_id = 'edu.mit.synbio.cytoflow.view.autofluorescencediagnosticview'

    short_name = "Autofluorescence correction"
    menu_group = "Calibration"
    
    def get_operation(self):
        return AutofluorescenceWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, AutofluorescenceWorkflowOp):
            return AutofluorescenceHandler(model = model, context = context)
        elif isinstance(model, AutofluorescenceWorkflowView):
            return AutofluorescenceViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('autofluorescence')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]

