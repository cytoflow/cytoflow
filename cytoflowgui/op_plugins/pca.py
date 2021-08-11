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
Principal Component Analysis
----------------------------

Use principal components analysis (PCA) to decompose a multivariate data
set into orthogonal components that explain a maximum amount of variance.

Creates new "channels" named ``{name}_1 ... {name}_n``,
where ``name`` is the `name` attribute and ``n`` is `num_components`.

The same decomposition may not be appropriate for different subsets of the data set.
If this is the case, you can use the `by` attribute to specify 
metadata by which to aggregate the data before estimating (and applying) a 
model.  The PCA parameters such as the number of components and the kernel
are the same across each subset, though.

.. object:: Name
    
    The operation name; determines the name of the new columns.
        
.. object:: Channels

    The channels to apply the decomposition to.

.. object:: Scale

    Re-scale the data in the specified channels before fitting.

.. object:: Num components

    How many components to fit to the data?  Must be a positive integer.
    
.. object:: By

    A list of metadata attributes to aggregate the data before estimating
    the model.  For example, if the experiment has two pieces of metadata,
    ``Time`` and ``Dox``, setting `by` to ``["Time", "Dox"]`` will 
    fit the model separately to each subset of the data with a unique 
    combination of ``Time`` and ``Dox``.
        
.. object:: Whiten

    Scale each component to unit variance?  May be useful if you will
    be using unsupervized clustering (such as K-means).

'''
from natsort import natsorted

from traits.api import provides, Event, Property, List, Str
from traitsui.api import (View, Item, EnumEditor, HGroup, VGroup, TextEditor, 
                          CheckListEditor, ButtonEditor, Controller)
from envisage.api import Plugin
from pyface.api import ImageResource

from ..editors import SubsetListEditor, InstanceHandlerEditor, VerticalListEditor
from ..workflow.operations import PCAWorkflowOp, PCAChannel
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class ChannelHandler(Controller):
    channel_view = View(HGroup(Item('channel',
                                    editor = EnumEditor(name = 'context_handler.channels')),
                               Item('scale')))

class PCAHandler(OpHandler):
    
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
             VGroup(Item('num_components',
                         editor = TextEditor(auto_set = False),
                         label = "Num\nComponents"),
                    Item('whiten'),
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
        self.model.channels_list.append(PCAChannel())
        
    def _remove_channel_fired(self):
        if self.model.channels_list:
            self.model.channels_list.pop()   
            
    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return []


@provides(IOperationPlugin)
class PCAPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.op_plugins.pca'
    operation_id = 'edu.mit.synbio.cytoflow.operations.pca'
    view_id = None

    short_name = "Principal Component Analysis"
    menu_group = "Calibration"
    
    def get_operation(self):
        return PCAWorkflowOp()
    
    def get_handler(self, model, context):
        return PCAHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('pca')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
