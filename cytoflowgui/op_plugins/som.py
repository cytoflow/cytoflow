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
Self-Organizing Map Clustering
------------------------------

Use a self-organizing map to cluster events. Often combined with a minimum
spanning tree to visualize clusters.

.. object:: Name
    
    The operation name; determines the name of the new metadata column.
        
.. object:: Channels

    The channels to apply the clustering algorithm to.

.. object:: Scale

    Re-scale the data in the specified channels before fitting.
    
.. object:: Consensus cluster

    Should we use consensus clustering to find the "natural" number of
    clusters? Defaults to ``True``.
    
    
.. object:: Sample

    What proportion of the data set to use for training? Defaults to 1% of the
    dataset to help with runtime.
    
.. object:: By

    A list of metadata attributes to aggregate the data before estimating
    the model.  For example, if the experiment has two pieces of metadata,
    ``Time`` and ``Dox``, setting **By** to ``["Time", "Dox"]`` will 
    fit the model separately to each subset of the data with a unique 
    combination of ``Time`` and ``Dox``.
    
**Advanced parameters**

.. object:: Width, Height

    The width and height of the map. The number of clusters is the product
    of **Width** and **Height**.
    
.. object:: Distance

    The distance measure that activates the map. Defaults to ``euclidean``.
    ``cosine`` is recommended for >3 channels.
    
.. object:: Learning Rate

    The initial step size for updating the self-organizing map weights. Changes
    as the map is learned.
    
.. object:: Sigma

    The magnitude of each update. Fixed over the course of the run -- 
    higher values mean more aggressive updates.
    
.. object:: Iterations

    How many times to update neuron weights.
    
.. object: Min clusters

    The minimum number of consensus clusters to form.
    
.. object: Max clusters
    
    The maximum number of consensus clusters to form.
    
.. object:: Resamples

    The number of times to attempt making consensus clusters.
    
.. object:: Resample Fraction

    The fraction of points in the map to sample for each clustering.
    Defaults to 80%.
    
If you'd like to learn more about self-organizing maps and how to use them
effectively, check out https://rubikscode.net/2018/08/20/introduction-to-self-organizing-maps/
    
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
    
    som_op = flow.SOMOp(name = 'SOM',                
                        channels = ['V2-A', 'Y2-A'], 
                        scale = {'V2-A' : 'log',     
                                 'Y2-A' : 'log'})    
                                
    som_op.estimate(ex)
    som_op.default_view().plot(ex)
    
    ex2 = som_op.apply(ex)
    
    som_op.default_view().plot(ex2)

'''
from natsort import natsorted

from traits.api import provides, Event, Property, List, Str
from traitsui.api import (View, Item, EnumEditor, HGroup, VGroup, TextEditor, 
                          CheckListEditor, ButtonEditor, Controller, TupleEditor)
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..editors import SubsetListEditor, InstanceHandlerEditor, VerticalListEditor
from ..workflow.operations import SOMWorkflowOp, SOMWorkflowView, SOMChannel
from ..view_plugins.view_plugin_base import DataPlotParamsView
from ..subset_controllers import subset_handler_factory
from ..view_plugins import ViewHandler

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class ChannelHandler(Controller):
    channel_view = View(HGroup(Item('channel',
                                    editor = EnumEditor(name = 'context_handler.channels')),
                               Item('scale')))

class SOMHandler(OpHandler):
    
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
             VGroup(Item('consensus_cluster',
                         label = "Consensus\nCluster"),
                    Item('sample',
                         editor = TextEditor(auto_set = False,
                                             evaluate = float,
                                             format_func = lambda x: "" if x is None else str(x)),
                         label = "Sample"),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context_handler.previous_conditions_names'),
                         label = 'Group\nEstimates\nBy',
                         style = 'custom'),
                    label = "Estimate parameters"),
             VGroup(Item('width',
                         editor = TextEditor(auto_set = False,
                                             evaluate = int,
                                             format_func = lambda x: "" if x is None else str(x))),
                    Item('height',
                         editor = TextEditor(auto_set = False,
                                             evaluate = int,
                                             format_func = lambda x: "" if x is None else str(x))),
                    Item('learning_rate',
                         label = "Learning\nRate",
                         editor = TextEditor(auto_set = False,
                                             evaluate = float,
                                             format_func = lambda x: "" if x is None else str(x))),
                    Item('sigma',
                         editor = TextEditor(auto_set = False,
                                             evaluate = float,
                                             format_func = lambda x: "" if x is None else str(x))),
                    Item('num_iterations',
                         label = "Iterations",
                         editor = TextEditor(auto_set = False,
                                             evaluate = int,
                                             format_func = lambda x: "" if x is None else str(x))),
                    Item('min_clusters',
                         label = "Min Clusters",
                         editor = TextEditor(auto_set = False,
                                             evaluate = int,
                                             format_func = lambda x: "" if x is None else str(x))),
                    Item('max_clusters',
                         label = "Max Clusters",
                         editor = TextEditor(auto_set = False,
                                             evaluate = int,
                                             format_func = lambda x: "" if x is None else str(x))),
                    Item('n_resamples',
                         label = "Resamples",
                         editor = TextEditor(auto_set = False,
                                             evaluate = int,
                                             format_func = lambda x: "" if x is None else str(x))),
                    Item('resample_frac',
                         label = "Resample\nFraction",
                         editor = TextEditor(auto_set = False,
                                             evaluate = float,
                                             format_func = lambda x: "" if x is None else str(x))),
                    label = "Advanced Parameters"),
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
        self.model.channels_list.append(SOMChannel())
        
    def _remove_channel_fired(self):
        if self.model.channels_list:
            self.model.channels_list.pop()   
            
    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return []
        
class SOMViewParamsHandler(Controller):
    view_params_view = \
        View(
        # histogram-specific
        # TODO - figure out conditional view
        VGroup(Item('orientation'),
               Item('lim',
                    label = "Data\nLimits",
                    editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                               evaluate = float,
                                                               placeholder = "None",
                                                               format_func = lambda x: "" if x is None else str(x)),
                                                    TextEditor(auto_set = False,
                                                               evaluate = float,
                                                               placeholder = "None",
                                                               format_func = lambda x: "" if x is None else str(x))],
                                         labels = ["Min", "Max"],
                                         cols = 1)),
               Item('num_bins',
                    editor = TextEditor(auto_set = False,
                                        placeholder = "None",
                                        format_func = lambda x: "" if x is None else str(x))),
               Item('histtype'),
               Item('linestyle'),
               Item('linewidth',
                    editor = TextEditor(auto_set = False,
                                        placeholder = "None",
                                        format_func = lambda x: "" if x is None else str(x))),
               Item('alpha',
                    editor = TextEditor(auto_set = False))),
        # scatterplot-specific
        # TODO - figure out conditional view
        VGroup(Item('xlim',
                    label = "X Limits",
                    editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                               evaluate = float,
                                                               placeholder = "None",
                                                               format_func = lambda x: "" if x is None else str(x)),
                                                    TextEditor(auto_set = False,
                                                               evaluate = float,
                                                               placeholder = "None",
                                                               format_func = lambda x: "" if x is None else str(x))],
                                         labels = ["Min", "Max"],
                                         cols = 1)),
               Item('ylim',
                    label = "Y Limits",
                    editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                               evaluate = float,
                                                               placeholder = "None",
                                                               format_func = lambda x: "" if x is None else str(x)),
                                                    TextEditor(auto_set = False,
                                                               evaluate = float,
                                                               placeholder = "None",
                                                               format_func = lambda x: "" if x is None else str(x))],
                                         labels = ["Min", "Max"],
                                         cols = 1)),
               Item('alpha',
                    editor = TextEditor(auto_set = False)),
               Item('s',
                    editor = TextEditor(auto_set = False),
                    label = "Size"),
               Item('marker')),
             DataPlotParamsView.content)
        
class SOMViewHandler(ViewHandler):
    view_traits_view = \
        View()
        # TODO - figure this out!
        # TODO - make sure this works with an MST view!!
        
    view_params_view = \
        View(Item('plot_params',
                  editor = InstanceHandlerEditor(view = 'view_params_view',
                                                 handler_factory = SOMViewParamsHandler),
                  style = 'custom',
                  show_label = False))


@provides(IOperationPlugin)
class SOMPlugin(Plugin, PluginHelpMixin):

    id = 'cytoflowgui.op_plugins.som'
    operation_id = 'cytoflow.operations.som'
    view_id = 'cytoflowgui.workflow.operations.somworkflowview'

    name = "Self-Organizing Map"
    menu_group = "Clustering"
    
    def get_operation(self):
        return SOMWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, SOMWorkflowOp):
            return SOMHandler(model = model, context = context)
        elif isinstance(model, SOMWorkflowView):
            return SOMViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('som')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
