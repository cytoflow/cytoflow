#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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
Created on Oct 9, 2015

@author: brian
'''

import numpy as np
import scipy.stats

from traitsui.api import (View, Item, EnumEditor, Controller, VGroup,
                          CheckListEditor, TextEditor)
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, List, on_trait_change
from pyface.api import ImageResource

from cytoflow.operations.channel_stat import ChannelStatisticOp
import cytoflow.utility as util

from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import SubsetListEditor, ISubset
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

mean_95ci = lambda x: util.ci(x, np.mean, boots = 100)
geomean_95ci = lambda x: util.ci(x, util.geom_mean, boots = 100)

summary_functions = {"Mean" : np.mean,
                     "Geom.Mean" : util.geom_mean,
                     "Count" : len,
                     "Std.Dev" : np.std,
                     "Geom.SD" : util.geom_sd_range,
                     "SEM" : scipy.stats.sem,
                     "Geom.SEM" : util.geom_sem_range,
                     "Mean 95% CI" : mean_95ci,
                     "Geom.Mean 95% CI" : geomean_95ci
                     }


class ChannelStatisticHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('channel',
                         editor=EnumEditor(name='context.previous_channels'),
                         label = "Channel"),
                    Item('statistic_name',
                                editor = EnumEditor(values = summary_functions.keys()),
                                label = "Function"),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context.previous_conditions_names'),
                         label = 'Group\nBy',
                         style = 'custom'),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous_conditions")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    shared_op_traits)

class ChannelStatisticPluginOp(PluginOpMixin, ChannelStatisticOp):
    handler_factory = Callable(ChannelStatisticHandler)
    
    # functions aren't picklable, so make this one transient 
    # and send the name instead
    function = Callable(transient = True)
    
    def apply(self, experiment):
        if not self.statistic_name:
            raise util.CytoflowOpError("Summary function isn't set")
        
        self.function = summary_functions[self.statistic_name]
        
        return ChannelStatisticOp.apply(self, experiment) 

@provides(IOperationPlugin)
class ChannelStatisticPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.channel_statistic'
    operation_id = 'edu.mit.synbio.cytoflow.operations.channel_statistic'

    short_name = "Channel Statistic"
    menu_group = "Gates"
    
    def get_operation(self):
        return ChannelStatisticPluginOp()
    
    def get_icon(self):
        return ImageResource('channel_stat')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    