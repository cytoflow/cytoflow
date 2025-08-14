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
Registration
------------

Use functional data analysis to *register* different data sets with eachother.


The algorithm identifies areas of high density that are shared across all most 
of the data sets, then applies a warp function to align those areas of high
density. This is commonly used to correct sample-to-sample variation
across large data sets. This is *not* a multidimensional algorithm --
if you apply it to multiple channels, each channel is warped 
independently.

        
.. object:: Channels

    The channels to apply the decomposition to.

.. object:: Scale

    Re-scale the data in the specified channels before fitting.
    
    **Smoothing parameters**

    
.. object:: Kernel

    The kernel to use for the smoothing.
    
.. object:: Bandwidth

    The bandwidth for the kernel, controls how lumpy or smooth the
    kernel estimate is.  Choices are:
    
        - ``scott`` (the default)
        - ``silverman``
        - A floating point number. Note that this is in scaled units, not data units.
    
.. object:: Grid Size

    The number of times to evaluate the smoothed histogram.
    
    
.. object:: By

    A list of metadata attributes to aggregate the data before estimating
    the model.  For example, if the experiment has two pieces of metadata,
    ``Time`` and ``Dox``, setting **By** to ``["Time", "Dox"]`` will 
    fit the model separately to each subset of the data with a unique 
    combination of ``Time`` and ``Dox``.
    
.. plot::
   :include-source: False

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "module_examples/itn_02.fcs",
                                 conditions = {'Sample' : 2}),
                       flow.Tube(file = "module_examples/itn_03.fcs",
                                 conditions = {'Sample' : 3})]
    import_op.conditions = {'Sample' : 'category'}
    ex = import_op.apply()
        
    op = flow.RegistrationOp(channels = ['CD3', 'CD4'],
                             scale = {'CD3' : 'log',
                                      'CD4' : 'log'},
                             by = ['Sample'])
        
    op.estimate(ex)
        
    op.default_view().plot(ex, plot_name = 'CD3')

'''
from natsort import natsorted

from traits.api import provides, Event, Property, List, Str
from traitsui.api import (View, Item, EnumEditor, HGroup, VGroup, 
                          CheckListEditor, ButtonEditor, Controller)
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..view_plugins import ViewHandler
from ..editors import ColorTextEditor, SubsetListEditor, InstanceHandlerEditor, VerticalListEditor
from ..workflow.operations import RegistrationWorkflowOp, RegistrationChannel, RegistrationDiagnosticWorkflowView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class ChannelHandler(Controller):
    channel_view = View(HGroup(Item('channel',
                                    editor = EnumEditor(name = 'context_handler.channels')),
                               Item('scale')))

class RegistrationHandler(OpHandler):
    
    add_channel = Event
    remove_channel = Event
    channels = Property(List(Str), observe = 'context.channels')
    
    operation_traits_view = \
        View(VGroup(Item('channels_list',
                         editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'channel_view',
                                                                                    handler_factory = ChannelHandler),
                                                     style = 'custom',
                                                     mutable = False)),
             Item('handler.add_channel',
                  editor = ButtonEditor(value = True,
                                        label = "Add a channel"),
                  show_label = False),
             Item('handler.remove_channel',
                  editor = ButtonEditor(value = True,
                                        label = "Remove a channel")),
             show_labels = False),
             VGroup(Item('kernel'),
                    Item('bw', 
                         label = "Bandwidth",
                         editor = EnumEditor(values = ["scott", "silverman"])),
                    Item('gridsize', label = "Grid Size"),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context_handler.previous_conditions_names'),
                         label = 'Group\nEstimates\nBy',
                         style = 'custom'),
                    label = "Estimate parameters"),
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

    # MAGIC: called when add_channel is set
    def _add_channel_fired(self):
        self.model.channels_list.append(RegistrationChannel())
        
    def _remove_channel_fired(self):
        if self.model.channels_list:
            self.model.channels_list.pop()   
            
    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return []
        
class RegistrationDiagnosticViewHandler(ViewHandler):
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
class RegistrationPlugin(Plugin, PluginHelpMixin):

    id = 'cytoflowgui.op_plugins.register'
    operation_id = 'cytoflow.operations.register'
    view_id = 'cytoflow.views.registrationdiagnosticview'

    name = "Registration"
    menu_group = "Quantitative"
    
    def get_operation(self):
        return RegistrationWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, RegistrationWorkflowOp):
            return RegistrationHandler(model = model, context = context)
        elif isinstance(model, RegistrationDiagnosticWorkflowView):
            return RegistrationDiagnosticViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('register')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
