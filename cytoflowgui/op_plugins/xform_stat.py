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
import pandas as pd
import scipy.stats

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, \
                         CheckListEditor, TextEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Str, List, Dict, Property
from pyface.api import ImageResource

from cytoflow.operations.xform_stat import TransformStatisticOp
import cytoflow.utility as util

from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

mean_95ci = lambda x: util.ci(x, np.mean, boots = 100)
geomean_95ci = lambda x: util.ci(x, util.geom_mean, boots = 100)

transform_functions = {"Mean" : np.mean,
                       "Geom.Mean" : util.geom_mean,
                       "Count" : len,
                       "Std.Dev" : np.std,
                       "Geom.SD" : util.geom_sd_range,
                       "SEM" : scipy.stats.sem,
                       "Geom.SEM" : util.geom_sem_range,
                       "Mean 95% CI" : mean_95ci,
                       "Geom.Mean 95% CI" : geomean_95ci,
                       "Sum" : np.sum,
                       "Proportion" : lambda a: pd.Series(a / a.sum()),
                       "Percentage" : lambda a: pd.Series(a / a.sum()) * 100.0,
                       "Fold" : lambda a: pd.Series(a / a.min())
                       }


class TransformStatisticHandler(Controller, OpHandlerMixin):
    
    prev_statistics = Property(depends_on = "info.ui.context")
    indices = Property(depends_on = "model.statistic, model.subset")
    levels = Property(depends_on = "model.statistic")    
    
    def _get_prev_statistics(self):
        context = self.info.ui.context['context']
        if context and context.previous:
            return context.previous.statistics.keys()
        else:
            return []

    # MAGIC: gets the value for the property indices
    def _get_indices(self):
        context = self.info.ui.context['context']
        
        if not (context and context.previous and context.previous.statistics and self.model and self.model.statistic[0]):
            return []
        
        stat = context.previous.statistics[self.model.statistic]
        data = pd.DataFrame(index = stat.index)
        
        if self.model.subset:
            data = data.query(self.model.subset)
            
        if len(data) == 0:
            return []       
        
        names = list(data.index.names)
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                data.index = data.index.droplevel(name)
        
        return list(data.index.names)
    
    # MAGIC: gets the value for the property 'levels'
    # returns a Dict(Str, pd.Series)
    
    def _get_levels(self):
        context = self.info.ui.context['context']
        
        if not (context and context.previous and context.previous.statistics 
                and self.model and self.model.statistic[0]):
            return []
        
        stat = context.previous.statistics[self.model.statistic]
        index = stat.index
        
        names = list(index.names)
        for name in names:
            unique_values = index.get_level_values(name).unique()
            if len(unique_values) == 1:
                index = index.droplevel(name)

        names = list(index.names)
        ret = {}
        for name in names:
            ret[name] = pd.Series(index.get_level_values(name)).sort_values()
            
        return ret
    
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('statistic',
                         editor=EnumEditor(name='handler.prev_statistics'),
                         label = "Statistic"),
                    Item('statistic_name',
                         editor = EnumEditor(values = transform_functions.keys()),
                         label = "Function"),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'handler.indices'),
                         
                         label = 'Group\nBy',
                         style = 'custom'),
                    VGroup(Item('subset_dict',
                                show_label = False,
                                editor = SubsetEditor(conditions = "handler.levels")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    shared_op_traits)

class TransformStatisticPluginOp(TransformStatisticOp, PluginOpMixin):
    handler_factory = Callable(TransformStatisticHandler)
    subset_dict = Dict(Str, List)
    
    # functions aren't picklable, so send the name instead
    function = Callable(transient = True)
    
    def apply(self, experiment):
        if not self.statistic_name:
            raise util.CytoflowOpError("Transform function not set")
        
        self.function = transform_functions[self.statistic_name]
        
        return TransformStatisticOp.apply(self, experiment)

@provides(IOperationPlugin)
class TransformStatisticPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.transform_statistic'
    operation_id = 'edu.mit.synbio.cytoflow.operations.transform_statistic'

    short_name = "Transform Statistic"
    menu_group = "Gates"
    
    def get_operation(self):
        return TransformStatisticPluginOp()
    
    def get_icon(self):
        return ImageResource('xform_stat')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    