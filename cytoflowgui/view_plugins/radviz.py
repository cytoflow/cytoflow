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

"""
Radviz Plot
-----------

Plots a radviz plot. Radviz plots project multivariate plots into two 
dimensions.  Good for looking for clusters.

.. object:: Channels

    The channels to plot, and their scales.  Drag the blue dot to re-order.
    
.. object:: Add Channel, Remove Channel

    Add or remove a channel
    
.. object:: Horizonal Facet

    Make multiple plots.  Each column has a unique value of this variable.
    
.. object:: Vertical Facet

    Make multiple plots.  Each row has a unique value of this variable.
    
.. object:: Color Facet

    Plot different values of a condition with different colors.

.. object:: Color Scale

    Scale the color palette and the color bar
    
.. object:: Tab Facet

    Make multiple plots in differen tabs; each tab's plot has a unique value
    of this variable.
    
.. object:: Subset

    Plot only a subset of the data in the experiment.
    
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
  
    flow.RadvizView(channels = ['B1-A', 'V2-A', 'Y2-A', 'FSC-A'],
                                scale = {'Y2-A' : 'log',
                                         'V2-A' : 'log',
                                         'B1-A' : 'log',
                                         'FSC-A' : 'log'},
                                huefacet = 'Dox').plot(ex)
"""

from natsort import natsorted

from traits.api import provides, Event, Property, List, Str
from traitsui.api import View, Item, EnumEditor, VGroup, HGroup, TextEditor, Controller, ButtonEditor
from envisage.api import Plugin
from pyface.api import ImageResource

from ..workflow.views import RadvizWorkflowView, RadvizPlotParams, RadvizChannel
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor, VerticalListEditor
from ..subset_controllers import subset_handler_factory

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler, PluginHelpMixin, DataPlotParamsView


class RadvizParamsHandler(Controller):
    view_params_view = \
        View(Item('alpha',
                  editor = TextEditor(auto_set = False)),
             Item('s',
                  editor = TextEditor(auto_set = False),
                  label = "Size"),
             Item('marker'),
             DataPlotParamsView.content)
        

class ChannelHandler(Controller):
    channel_view = View(HGroup(Item('channel',
                                    editor = EnumEditor(name = 'context_handler.channels')),
                               Item('scale')))
    

class RadvizHandler(ViewHandler):
    
    add_channel = Event
    remove_channel = Event
    channels = Property(List(Str), observe = 'context.channels')

    view_traits_view = \
        View(VGroup(
             VGroup(Item('channels_list',
                         editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'channel_view',
                                                                                    handler_factory = ChannelHandler),
                                                    style = 'custom',
                                                    mutable = False)),
                    Item('handler.add_channel',
                         editor = ButtonEditor(value = True,
                                               label = "Add a channel")),
                    Item('handler.remove_channel',
                         editor = ButtonEditor(value = True,
                                               label = "Remove a channel")),
                    show_labels = False),
             VGroup(Item('xfacet',
                         editor=ExtendableEnumEditor(name='context_handler.conditions_names',
                                                     extra_items = {"None" : ""}),
                         label = "Horizontal\nFacet"),
                    Item('yfacet',
                         editor=ExtendableEnumEditor(name='context_handler.conditions_names',
                                                     extra_items = {"None" : ""}),
                         label = "Vertical\nFacet"),
                    Item('huefacet',
                         editor=ExtendableEnumEditor(name='context_handler.conditions_names',
                                                     extra_items = {"None" : ""}),
                         label = "Color\nFacet"),
                    Item('huescale',
                         label = "Color\nScale"),
                    Item('plotfacet',
                         editor=ExtendableEnumEditor(name='context_handler.conditions_names',
                                                     extra_items = {"None" : ""}),
                         label = "Tab\nFacet"),
                    label = "Radviz plot",
                    show_border = False),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "context_handler.conditions",
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
                                                 handler_factory = RadvizParamsHandler),
                  style = 'custom',
                  show_label = False))
    

    # MAGIC: called when add_control is set
    def _add_channel_fired(self):
        self.model.channels_list.append(RadvizChannel())
        
    def _remove_channel_fired(self):
        if self.model.channels_list:
            self.model.channels_list.pop()   

    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return []

@provides(IViewPlugin)
class RadvizPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.view.radviz'
    view_id = 'edu.mit.synbio.cytoflow.view.radviz'
    short_name = "Radviz Plot"

    def get_view(self):
        return RadvizWorkflowView()
        
    def get_handler(self, model, context):
        if isinstance(model, RadvizWorkflowView):
            return RadvizHandler(model = model, context = context)
        elif isinstance(model, RadvizPlotParams):
            return RadvizParamsHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('radviz')

    plugin = List(contributes_to = VIEW_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
        

