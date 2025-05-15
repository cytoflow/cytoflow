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
t-Stochastic Neighbor Embedding
-------------------------------

Use t-Stochastic Neighbor Embedding to decompose a multivariate data
into clusters that maintain underlying structure.

Creates new "channels" named ``{name}_1`` and ``{name}_2``,
where ``name`` is the **Name** attribute.

The same decomposition may not be appropriate for different subsets of the data set.
If this is the case, you can use the **By** attribute to specify 
metadata by which to aggregate the data before estimating (and applying) a 
model.  The tSNE parameters such as the distance metric.

.. object:: Name
    
    The operation name; determines the name of the new columns.
        
.. object:: Channels

    The channels to apply the decomposition to.

.. object:: Scale

    Re-scale the data in the specified channels before fitting.
    
.. object:: Metric

    How should we measure "distance"? Euclidean distance makes sense if the
    number of dimensions (ie, channels) is small, but as the number of 
    dimensions increases, maybe try ``cosine`` or one of the others.
    
.. object:: Perplexity

    The balance between the local and global structure of the data. Larger 
    datasets benefit from higher perplexity, but be warned -- runtime
    scales linearly with perplexity!
    
.. object:: Sample

    What proportion of the data set to use for training? Defaults to 1%
    of the dataset to help with runtime.
    
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
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()
    

    km_op = flow.tSNEOp(name = 'tSNE',
                        channels = ['V2-A', 'Y2-A'],
                        scale = {'V2-A' : 'log',
                                 'Y2-A' : 'log'})
    km_op.estimate(ex)   
    ex2 = km_op.apply(ex)
    flow.ScatterplotView(xchannel = "tSNE_1",
                         ychannel = "tSNE_2",
                         huefacet = "Dox").plot(ex2)


'''
from natsort import natsorted

from traits.api import provides, Event, Property, List, Str
from traitsui.api import (View, Item, EnumEditor, HGroup, VGroup, TextEditor, 
                          CheckListEditor, ButtonEditor, Controller)
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..editors import SubsetListEditor, InstanceHandlerEditor, VerticalListEditor
from ..workflow.operations import tSNEWorkflowOp, tSNEChannel
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class ChannelHandler(Controller):
    channel_view = View(HGroup(Item('channel',
                                    editor = EnumEditor(name = 'context_handler.channels')),
                               Item('scale')))

class tSNEHandler(OpHandler):
    
    add_channel = Event
    remove_channel = Event
    channels = Property(List(Str), observe = 'context.channels')
    
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False, placeholder = "None")),
             VGroup(Item('channels_list',
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
             VGroup(Item('perplexity',
                         editor = TextEditor(auto_set = False),
                         label = "Perplexity"),
                    Item('sample',
                         editor = TextEditor(auto_set = False,
                                             evaluate = float,
                                             format_func = lambda x: "" if x is None else str(x)),
                         label = "Sample"),
                    Item('metric'),
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
             Item('status', 
                  width = 1.0,
                  style = "readonly"),
             shared_op_traits_view)

    # MAGIC: called when add_channel is set
    def _add_channel_fired(self):
        self.model.channels_list.append(tSNEChannel())
        
    def _remove_channel_fired(self):
        if self.model.channels_list:
            self.model.channels_list.pop()   
            
    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return []


@provides(IOperationPlugin)
class tSNEPlugin(Plugin, PluginHelpMixin):

    id = 'cytoflowgui.op_plugins.tsne'
    operation_id = 'cytoflow.operations.tsne'
    view_id = None

    name = "t-Stochastic Neighbor Embedding"
    menu_group = "Calibration"
    
    def get_operation(self):
        return tSNEWorkflowOp()
    
    def get_handler(self, model, context):
        return tSNEHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('tsne')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
