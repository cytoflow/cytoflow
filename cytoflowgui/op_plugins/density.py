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
Density 
-------

Computes a gate based on a 2D density plot.  The user chooses what proportion
of events to keep, and the module creates a gate that selects those events in
the highest-density bins of a 2D density histogram.
    
A single gate may not be appropriate for an entire experiment.  If this is the 
case, you can use **By** to specify metadata by which to aggregate the data 
before computing and applying the gate.  
    
.. object:: Name
        
    The operation name; determines the name of the new metadata
        
.. object:: X Channel, Y Channel
    
    The channels to apply the mixture model to.

.. object:: X Scale, Y Scale 

    Re-scale the data in **Channel** before fitting. 

.. object:: Keep

    The proportion of events to keep in the gate.  Defaults to 0.9.
    
.. object:: By 

    A list of metadata attributes to aggregate the data before estimating
    the model.  For example, if the experiment has two pieces of metadata,
    ``Time`` and ``Dox``, setting :attr:`by` to ``["Time", "Dox"]`` will fit 
    the model separately to each subset of the data with a unique combination of
    ``Time`` and ``Dox``.

.. plot::

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()
    

    density_op = flow.DensityGateOp(name = 'Density',
                                    xchannel = 'FSC-A',
                                    xscale = 'log',
                                    ychannel = 'SSC-A',
                                    yscale = 'log',
                                    keep = 0.5)
    density_op.estimate(ex)   
    density_op.default_view().plot(ex)
    ex2 = density_op.apply(ex)
'''

from traits.api import provides
from traitsui.api import (View, Item, EnumEditor, VGroup, TextEditor, 
                          CheckListEditor, ButtonEditor)
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from ..view_plugins import ViewHandler
from ..view_plugins.density import DensityParamsHandler
from ..editors import SubsetListEditor, ColorTextEditor, InstanceHandlerEditor
from ..workflow.operations import DensityGateWorkflowOp, DensityGateWorkflowView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin

class DensityGateHandler(OpHandler):
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
             Item('keep', 
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "Proportion\nto keep"),
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



class DensityGateViewHandler(ViewHandler):
    view_traits_view = \
        View(VGroup(
             VGroup(Item('xchannel',
                         label = "X channel",
                         style = 'readonly'),
                    Item('ychannel',
                         label = "Y channel",
                         style = 'readonly'),
                    Item('xscale',
                         label = "X scale",
                         style = 'readonly'),
                    Item('yscale',
                         label = "Y scale",
                         style = 'readonly'),
                    Item('huescale',
                         label = "Hue scale"),
                    label = "Density Gate Default Plot",
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
        
    view_params_view = \
        View(Item('plot_params',
                  editor = InstanceHandlerEditor(view = 'view_params_view',
                                                 handler_factory = DensityParamsHandler),
                  style = 'custom',
                  show_label = False))



@provides(IOperationPlugin)
class DensityGatePlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.density'
    operation_id = 'edu.mit.synbio.cytoflow.operations.density'
    view_id = 'edu.mit.synbio.cytoflow.view.densitygateview'

    short_name = "2D Mixture Model"
    menu_group = "Gates"
    
    def get_operation(self):
        return DensityGateWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, DensityGateWorkflowOp):
            return DensityGateHandler(model = model, context = context)
        elif isinstance(model, DensityGateWorkflowView):
            return DensityGateViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('density')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

