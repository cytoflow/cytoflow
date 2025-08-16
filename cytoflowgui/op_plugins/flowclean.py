#!/usr/bin/env python3.11
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2025
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
FlowClean
---------

This module gates events from time slices whose density is low or
whose events' fluorescence intensity varies substantially from other slices. 
This is often due to a bubble or transient clog in the flow cell.
    
The operation assesses whether a tube is "clean" by looking for changes in 
fluorescence over time, both fast changes (discontinuities) and slow changes
(drift). If the tube is clean, only low-density slices are removed. If the 
tube is not clean, then a cleaning is attempted, removing slices that are 
substantially statistically different than the majority. Cleanliness is then 
assessed again. 

This operation is applied to every tube independently -- that is, to every
subset of events with a unique combination of experimental metadata.

.. object:: Name

   The name of the gate you can subsequently use to exclude "unclean" events.
    
.. object:: Time channel

   The channel that represents time -- often ``HDR-T`` or similar.
        
.. object:: Channels 

   Which fluorescence channel or channels are analyzed for variation,
   and how should they be scaled before cleaning, and how they should
   be scaled.
        
   .. important:: This algorithm works *much* better when fluorescence
      channels are using a scale other than ``linear``!
    
.. object:: Segment Size (default = 500)

   The number of events in each bin in the analysis.

.. object:: Density Cutoff (default = 0.05)

    The minimum density CDF to keep.
        
.. object:: Max Discontinuity (default = 0.1)

   The critical "continuity" -- determines how "different" an adjacent
   segment must be to be for a tube to be flagged as suspicious.

.. object:: Max Drift : Float (default = 0.15)

   The maximum any individual channel can drift before being flagged as
   needing cleaning.
        
.. object:: Max Mean Drift : Float (default = 0.13)

   The maximum the mean of all channels' drift can be before the tube is
   flagged as needing to be cleaned.
        
.. object:: Segment Cutoff (default = 0.05)

   The minimum sum-of-measures' CDF to keep.
   
.. object:: Detect Worst Channels (Range) (default = 0)   
 
   Try to detect the worst channels and use them to flag tubes 
   / trim events. If this attribute is greater than 0, choose channels
   using the range of the mean of the bins' fluorescence distribution.
   Often used in combination with **Detect Worst Channels (SD)**.

.. object:: Detect Worst Channels (SD) (default = 0)

   Try to detect the worst channels and use them to flag tubes 
   / trim events. If this attribute is greater than 0, choose channels
   using the standard deviation of the mean of the bins' fluorescence distribution.
   Often used in combination with **Detect Worst Channels (Range)**.
               
.. object:: Measures (default = ("5th percentile", "20th percentile", "50th percentile", "80th percentile", "95th percentile", "mean", "variance", "skewness") ).

   Which measures should be considered when comparing segments?
        
.. object:: Don't Clean (default = False)

   If ``True``, never clean -- just remove low-density bins.
      
.. object:: Force Clean (default = False)  

   If ``True``, force cleaning even if the tube passes the original quality checks.
   Remember, the operation **always** removes low-density bins.
   

.. plot::
   :include-source: False
    
    import cytoflow as flow
    tube = flow.Tube(file = "module_examples/stabilize.fcs")
    ex = flow.ImportOp(tubes = [tube]).apply()
    
    fc = flow.FlowCleanOp(name = "fc",
                          time_channel = "HDR-T",
                          channels = ["Venus-A",
                                      "mRuby-A",
                                      "mTurquoise2-A"],
                          scale = {"Venus-A" : "logicle",
                                   "mRuby-A" : "logicle",
                                   "mTurquoise2-A" : "logicle"})
                                   
    fc.estimate(ex) 
    fc.default_view().plot(experiment = ex, plot_name = "module_examples/stabilize.fcs")
'''

from natsort import natsorted

from traits.api import provides, Event, Property, List, Str, Bool
from traitsui.api import (View, Item, EnumEditor, HGroup, VGroup, TextEditor, 
                          ButtonEditor, Controller, CheckListEditor)
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..view_plugins import ViewHandler
from ..editors import InstanceHandlerEditor, VerticalListEditor, ColorTextEditor, ToggleButtonEditor
from ..workflow.operations import FlowCleanWorkflowOp, FlowCleanChannel, FlowCleanWorkflowView

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class ChannelHandler(Controller):
    channel_view = View(HGroup(Item('channel',
                                    editor = EnumEditor(name = 'context_handler.channels')),
                               Item('scale')))
    
class FlowCleanHandler(OpHandler):

    add_channel = Event
    remove_channel = Event
    channels = Property(List(Str), observe = 'context.channels')
    
    show_advanced_options = Bool(False)
    
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
             Item('time_channel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "Time Channel"),
             VGroup(Item('handler.show_advanced_options',
                         editor = ToggleButtonEditor(label = "Advanced options..."),
                         show_label = False),
                    show_labels = False),
             VGroup(Item('segment_size',
                        editor = TextEditor(auto_set = False,
                                            evaluate = int,
                                            format_func = lambda x: "" if x is None else str(x),
                                            placeholder = "None"),
                        label = "Segment Size"),
                    Item('density_cutoff',
                        editor = TextEditor(auto_set = False,
                                            evaluate = float,
                                            format_func = lambda x: "" if x is None else str(x),
                                            placeholder = "None"),
                        label = "Density Cutoff"),
                    Item('max_drift',
                        editor = TextEditor(auto_set = False,
                                            evaluate = float,
                                            format_func = lambda x: "" if x is None else str(x),
                                            placeholder = "None"),
                        label = "Max Drift"),
                    Item('max_mean_drift',
                        editor = TextEditor(auto_set = False,
                                            evaluate = float,
                                            format_func = lambda x: "" if x is None else str(x),
                                            placeholder = "None"),
                        label = "Max Mean Drift"),
                    Item('max_discontinuity',
                        editor = TextEditor(auto_set = False,
                                            evaluate = float,
                                            format_func = lambda x: "" if x is None else str(x),
                                            placeholder = "None"),
                        label = "Max Discontinuity"),
                    Item('segment_cutoff',
                        editor = TextEditor(auto_set = False,
                                            evaluate = float,
                                            format_func = lambda x: "" if x is None else str(x),
                                            placeholder = "None"),
                        label = "Segment Cutoff"),
                    Item('detect_worst_channels_range',
                        editor = TextEditor(auto_set = False,
                                            evaluate = int,
                                            format_func = lambda x: "" if x is None else str(x),
                                            placeholder = "None"),
                        label = "Detect Worst\nChannels (Range)"),
                    Item('detect_worst_channels_sd',
                        editor = TextEditor(auto_set = False,
                                            evaluate = int,
                                            format_func = lambda x: "" if x is None else str(x),
                                            placeholder = "None"),
                        label = "Detect Worst\nChannels (StDev)"),
                    Item('measures',
                         editor = CheckListEditor(cols = 2,
                                                  values = ["5th percentile", "20th percentile", 
                                                            "50th percentile", "80th percentile", 
                                                            "95th percentile", "mean", 
                                                            "variance", "skewness"]),
                         label = "Measures"),
                    Item('force_clean',
                         label = "Force clean?"),
                    Item('dont_clean',
                         label = "Don't clean?"),
                    visible_when = "handler.show_advanced_options"),
             Item('do_estimate',
                  editor = ButtonEditor(value = True,
                                        label = "Estimate!"),
                  show_label = False),
             shared_op_traits_view)

    # MAGIC: called when add_channel is set
    def _add_channel_fired(self):
        self.model.channels_list.append(FlowCleanChannel())
        
    def _remove_channel_fired(self):
        if self.model.channels_list:
            self.model.channels_list.pop()   
            
    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return []
        
class FlowCleanViewHandler(ViewHandler):
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
class FlowCleanPlugin(Plugin, PluginHelpMixin):

    id = 'cytoflowgui.op_plugins.flowclean'
    operation_id = 'cytoflow.operations.flowclean'
    view_id = 'cytoflow.view.flowcleandiagnostic'

    short_name = name = "FlowClean"
    menu_group = "Preprocessing"
    
    def get_operation(self):
        return FlowCleanWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, FlowCleanWorkflowOp):
            return FlowCleanHandler(model = model, context = context)
        elif isinstance(model, FlowCleanWorkflowView):
            return FlowCleanViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('flowclean')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
