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
Gaussian Mixture Model (2D)
---------------------------

Fit a Gaussian mixture model with a specified number of components to two 
channels.

If **Num Components** is greater than 1, then this module creates a new 
categorical metadata variable named **Name**, with possible values 
``{name}_1`` .... ``name_n`` where ``n`` is the number of components.  
An event is assigned to  ``name_i`` category if it has the highest posterior 
probability of having been produced by component ``i``.  If an event has a 
value that is outside the range of one of the channels' scales, then it is 
assigned to ``{name}_None``.
    
Additionally, if **Sigma** is greater than 0, this module creates new boolean
metadata variables named ``{name}_1`` ... ``{name}_n`` where ``n`` is the 
number of components.  The column ``{name}_i`` is ``True`` if the event is less 
than **Sigma** standard deviations from the mean of component ``i``.  If 
**Num Components** is ``1``, **Sigma** must be greater than 0.
    
Finally, the same mixture model (mean and standard deviation) may not
be appropriate for every subset of the data.  If this is the case, you
can use **By** to specify metadata by which to aggregate the data before 
estimating and applying a mixture model.  

.. note:: 

    **Num Components** and **Sigma** will be the same for each subset. 
    
.. object:: Name
        
    The operation name; determines the name of the new metadata
        
.. object:: X Channel, Y Channel
    
    The channels to apply the mixture model to.

.. object:: X Scale, Y Scale 

    Re-scale the data in **Channel** before fitting. 

.. object:: Num Components
    
    How many components to fit to the data?  Must be a positive integer.

.. object:: Sigma 
    
    How many standard deviations on either side of the mean to include
    in the boolean variable ``{name}_i``?  Must be ``>= 0.0``.  If 
    **Num Components** is ``1``, must be ``> 0``.
    
.. object:: By 

    A list of metadata attributes to aggregate the data before estimating
    the model.  For example, if the experiment has two pieces of metadata,
    ``Time`` and ``Dox``, setting **By** to ``["Time", "Dox"]`` will fit 
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
    

    gm_op = flow.GaussianMixtureOp(name = 'Gauss',
                                   channels = ['V2-A', 'Y2-A'],
                                   scale = {'V2-A' : 'log',
                                            'Y2-A' : 'log'},
                                   num_components = 2)
    gm_op.estimate(ex)   
    ex2 = gm_op.apply(ex)
    gm_op.default_view().plot(ex2)
'''

from traits.api import provides, List
from traitsui.api import (View, Item, EnumEditor, VGroup, TextEditor, 
                          CheckListEditor, ButtonEditor)
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..view_plugins import ViewHandler
from ..view_plugins.scatterplot import ScatterplotParamsHandler
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..workflow.operations import GaussianMixture2DWorkflowOp, GaussianMixture2DWorkflowView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class GaussianMixture2DHandler(OpHandler):
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
             Item('num_components', 
                  editor = TextEditor(auto_set = False,
                                      evaluate = int,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "Num\nComponents"),
             Item('sigma',
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None")),
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


class GaussianMixture2DViewHandler(ViewHandler):
    view_traits_view = \
        View(VGroup(
             VGroup(Item('xchannel',
                         style = 'readonly'),
                    Item('ychannel',
                         style = 'readonly'),
                    Item('xfacet',
                         editor=ExtendableEnumEditor(name='by',
                                                     extra_items = {"None" : ""}),
                         label = "Horizontal\nFacet"),
                    Item('yfacet',
                         editor=ExtendableEnumEditor(name='by',
                                                     extra_items = {"None" : ""}),
                         label = "Vertical\nFacet"),
                    label = "2D Mixture Model Default Plot",
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
                                                 handler_factory = ScatterplotParamsHandler),
                  style = 'custom',
                  show_label = False))


@provides(IOperationPlugin)
class GaussianMixture2DPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.gaussian_2d'
    operation_id = 'edu.mit.synbio.cytoflowgui.operations.gaussian_2d'
    view_id = 'edu.mit.synbio.cytoflow.view.gaussianmixture2dview'

    name = "2D Mixture Model"
    menu_group = "Gates"
    
    def get_operation(self):
        return GaussianMixture2DWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, GaussianMixture2DWorkflowOp):
            return GaussianMixture2DHandler(model = model, context = context)
        elif isinstance(model, GaussianMixture2DWorkflowView):
            return GaussianMixture2DViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('gauss_2d')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]

