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
cytoflowgui.workflow.operations.category
----------------------------------------
"""

from traits.api import provides, Str, List, Property, Dict, Any, observe

from cytoflow.operations.category import CategoryOp

from ..serialization import camel_registry, cytoflow_class_repr, dedent
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

CategoryOp.__repr__ = cytoflow_class_repr

class CategoryOpSubset(HasStrictTraits):
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, estimate = True)
    category = Str
    context = Any
          
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    def trait_context(self):
        """ Returns the default context to use for editing or configuring
            traits.
        """
        return {"object": self,
                "context" : self.context}


@provides(IWorkflowOperation)
class CategoryWorkflowOp(WorkflowOperation, CategoryOp):
    name = Str(apply = True)
    subsets = Property(Dict(Str, Str),
                       observe = '[subsets_list.items,subsets_list.items.category,subsets_list.items.subset]')
    subsets_list = List(CategoryOpSubset, apply = True)
    default = Str("Unknown", apply = True)
    
    def _get_subsets(self):
        return {s.subset : s.category for s in self.subsets_list}
    
    @observe('subsets_list:items,subsets_list:items.subset,subsets_list:items.category')
    def _on_subset_changed(self, _):
        self.changed = 'subsets_list'
    
    def get_notebook_code(self, idx):
        op = CategoryOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        
    def trait_context(self):
        """ Returns the default context to use for editing or configuring
            traits.
        """
        return {"object": self}

    
### Serialization
@camel_registry.dumper(CategoryWorkflowOp, 'category', version = 1)
def _dump(op):
    return dict(name = op.name,
                gates_list = op.gates_list,
                default = op.default)
    
@camel_registry.loader('category', version = 1)
def _load(data, version):
    return CategoryWorkflowOp(**data)

@camel_registry.dumper(CategoryOpSubset, 'categoryop-subset', version = 1)
def _dump_subset(subset):
    return dict(subset = subset.subset,
                category = subset.category)
    
@camel_registry.loader('categoryop-subset', version = 1)
def _load_subset(data, _):
    return CategoryOpSubset(**data)
