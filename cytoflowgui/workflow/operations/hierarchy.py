#!/usr/bin/env python3.8
# coding: latin-1
from traits.has_traits import HasStrictTraits

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
cytoflowgui.workflow.operations.hierarchy
-----------------------------------------
"""

from traits.api import provides, Str, List, Tuple, Any, Property, observe

from cytoflow.operations.hierarchy import HierarchyOp

from ..serialization import camel_registry, cytoflow_class_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

HierarchyOp.__repr__ = cytoflow_class_repr

class HierarchyGate(HasStrictTraits):
    gate = Str
    value = Any
    category = Str

@provides(IWorkflowOperation)
class HierarchyWorkflowOp(WorkflowOperation, HierarchyOp):
    name = Str(apply = True)
    gates = Property(List(Tuple(Str, Any, Str)),
                     observe = '[gates_list.items,gates_list.items.gate,gates_list.items.value,gates_list.items.category]')
    gates_list = List(HierarchyGate, apply = True)
    default = Str("Unknown", apply = True)
     
    # bits for gates
    @observe('[gates_list:items,gates_list:items.gate,gates_list:items.value,gates_list:items.category]')
    def _channels_updated(self, _):
        self.changed = 'gates_list'
        
    def _get_gates(self):
        return [(g.gate, g.value, g.category) for g in self.gates_list]
    
    def get_notebook_code(self, idx):
        op = HierarchyOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))

    
### Serialization
@camel_registry.dumper(HierarchyWorkflowOp, 'hierarchy', version = 1)
def _dump(op):
    return dict(name = op.name,
                gates_list = op.gates_list,
                default = op.default)
    
@camel_registry.loader('hierarchy', version = 1)
def _load(data, version):
    return HierarchyWorkflowOp(**data)


