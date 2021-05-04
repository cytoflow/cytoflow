#!/usr/bin/env python3.8

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


from textwrap import dedent
from traits.api import Str, provides

from cytoflow import RatioOp
                       
from cytoflowgui.workflow.serialization import camel_registry, traits_repr
from .operation_base import IWorkflowOperation, WorkflowOperation

RatioOp.__repr__ = traits_repr

@provides(IWorkflowOperation)
class RatioWorkflowOp(WorkflowOperation, RatioOp):
    
    name = Str(apply = True)
    numerator = Str(apply = True)
    denominator = Str(apply = True)
    
    def get_notebook_code(self, idx):
        op = RatioOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        
    
### Serialization
@camel_registry.dumper(RatioWorkflowOp, 'ratio', version = 1)
def _dump(op):
    return dict(name = op.name,
                numerator = op.numerator,
                denominator = op.denominator)
    
@camel_registry.loader('ratio', version = 1)
def _load(data, version):
    return RatioWorkflowOp(**data)
