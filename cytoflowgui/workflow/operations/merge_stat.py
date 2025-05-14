#!/usr/bin/env python3.8

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
cytoflowgui.workflow.operations.xform_stat
------------------------------------------

"""

from traits.api import (Str, Constant, provides)

import cytoflow.utility as util
                       
from cytoflowgui.workflow.serialization import camel_registry, cytoflow_class_repr
from .operation_base import IWorkflowOperation, WorkflowOperation

@provides(IWorkflowOperation)
class MergeStatisticsWorkflowOp(WorkflowOperation):
    id = Constant('cytoflowgui.workflow.operations.merge_statistics')
    friendly_id = Constant('Merge statistics')

    name = Str(apply = True)
    statistic_1 = Str(apply = True)
    statistic_2 = Str(apply = True)
        
    def apply(self, experiment):
        
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "Must specify a name")
        
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name)) 
        
        if not self.statistic_1:
            raise util.CytoflowOpError('statistic_1',
                                         "Statistic 1 not set")
            
        if not self.statistic_2:
            raise util.CytoflowOpError('statistic_2',
                                         "Statistic 2 not set")
            
        s1 = experiment.statistics[self.statistic_1]
        s2 = experiment.statistics[self.statistic_2]
        
        if not s1.index.equals(s2.index):
            raise util.CytoflowOpError('statistic_2',
                                       "Statistics must have the same index") 
        
        ret = experiment.clone(deep = False)
        new_stat = s1.join(s2)
        ret.statistics[self.name] = new_stat
        
        return ret
    
    def clear_estimate(self):
        # no-op
        return

    def get_notebook_code(self, idx):        
        return "\nex_{idx} = ex_{prev_idx}.clone(deep = False)\nex_{idx}.statistics['{name}'] = ex_{idx}.statistics['{s1}'].join(ex_{idx}.statistics['{s2}'])" \
            .format(idx = idx,
                    prev_idx = idx - 1,
                    name = self.name,
                    s1 = self.statistic_1,
                    s2 = self.statistic_2)

            
MergeStatisticsWorkflowOp.__repr__ = cytoflow_class_repr
            
### Serialization
@camel_registry.dumper(MergeStatisticsWorkflowOp, 'merge-statistics', version = 1)
def _dump(op):
    return dict(name = op.name,
                statistic_1 = op.statistic_1,
                statistic_2 = op.statistic_2)
        
@camel_registry.loader('merge-statistics', version = 1)
def _load(data, version):
    return MergeStatisticsWorkflowOp(**data)


