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
FlowPeaks
---------

This module uses the **flowPeaks** algorithm to assign events to clusters in
an unsupervized manner.
    
.. object:: Name
        
    The operation name; determines the name of the new metadata
        
.. object:: X Channel, Y Channel
    
    The channels to apply the mixture model to.

.. object:: X Scale, Y Scale 

    Re-scale the data in **Channel** before fitting. 

.. object:: h, h0

    Scalar values that control the smoothness of the estimated distribution.
    Increasing **h** makes it "rougher," while increasing **h0** makes it
    smoother.
    
.. object:: tol

    How readily should clusters be merged?  Must be between 0 and 1.
    
.. object:: Merge Distance

    How far apart can clusters be before they are merged?
    
.. object:: By 

    A list of metadata attributes to aggregate the data before estimating
    the model.  For example, if the experiment has two pieces of metadata,
    ``Time`` and ``Dox``, setting :attr:`by` to ``["Time", "Dox"]`` will fit 
    the model separately to each subset of the data with a unique combination of
    ``Time`` and ``Dox``.

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
    

    fp_op = flow.FlowPeaksOp(name = 'Flow',
                             channels = ['V2-A', 'Y2-A'],
                             scale = {'V2-A' : 'log',
                                      'Y2-A' : 'log'})
    fp_op.estimate(ex)   
    ex2 = fp_op.apply(ex)
    fp_op.default_view(density = True).plot(ex2)
    fp_op.default_view().plot(ex2)

'''

from traits.api import provides
from traitsui.api import (View, Item, EnumEditor, VGroup, TextEditor, 
                          CheckListEditor, ButtonEditor)
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from ..view_plugins import ViewHandler
from ..view_plugins.scatterplot import ScatterplotParamsHandler
from ..view_plugins.density import DensityParamsHandler
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..workflow.operations import FlowPeaksWorkflowOp, FlowPeaksWorkflowView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin

class FlowPeaksHandler(OpHandler):
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('xchannel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "X Channel"),
             Item('ychannel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "Y Channel"),
             Item('xscale',
                  label = "X Scale"),
             Item('yscale',
                  label = "Y Scale"),
             VGroup(
             Item('h', 
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None")),
             Item('h0',
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None")),
             Item('tol',
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None")),
             Item('merge_dist',
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "Merge\nDistance"),
             Item('by',
                  editor = CheckListEditor(cols = 2,
                                           name = 'context_handler.previous_conditions_names'),
                  label = 'Group\nEstimates\nBy',
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
             label = "Estimation parameters",
             show_border = False),
             shared_op_traits_view)



class FlowPeaksViewHandler(ViewHandler):
    view_traits_view = \
        View(VGroup(
             VGroup(Item('xchannel',
                         style = 'readonly'),
                    Item('ychannel',
                         style = 'readonly'),
                    Item('show_density',
                         label = "Show density plot?"),
                    label = "Flow Peaks Default Plot",
                    show_border = False)),
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
        
    view_params_view = View(Item('scatterplot_plot_params',
                                 editor = InstanceHandlerEditor(view = 'view_params_view',
                                                                handler_factory = ScatterplotParamsHandler),
                                 style = 'custom',
                                 show_label = False,
                                 visible_when = 'not object.show_density'),
                            Item('density_plot_params',
                                 editor = InstanceHandlerEditor(view = 'view_params_view',
                                                                handler_factory = DensityParamsHandler),
                                 style = 'custom',
                                 show_label = False,
                                 visible_when = 'object.show_density'))



@provides(IOperationPlugin)
class FlowPeaksPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.flowpeaks'
    operation_id = 'edu.mit.synbio.cytoflow.operations.flowpeaks'
    view_id = 'edu.mit.synbio.cytoflowgui.op_plugins.flowpeaks'

    short_name = "Flow Peaks"
    menu_group = "Gates"
    
    def get_operation(self):
        return FlowPeaksWorkflowOp()

    def get_handler(self, model, context):
        if isinstance(model, FlowPeaksWorkflowOp):
            return FlowPeaksHandler(model = model, context = context)
        elif isinstance(model, FlowPeaksWorkflowView):
            return FlowPeaksViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('flowpeaks')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
