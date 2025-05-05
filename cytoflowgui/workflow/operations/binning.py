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

"""
cytoflowgui.workflow.operations.binning
---------------------------------------

"""

from traits.api import (provides, Instance, Str, DelegatesTo)

from cytoflow.operations.binning import BinningOp, BinningView
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowFacetView, HistogramPlotParams
from ..serialization import camel_registry, traits_str, cytoflow_class_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

BinningOp.__repr__ = cytoflow_class_repr

@provides(IWorkflowOperation)
class BinningWorkflowOp(WorkflowOperation, BinningOp):
    name = Str(apply = True)
    channel = Str(apply = True)
    bin_width = util.PositiveCFloat(None, allow_zero = False, allow_none = True, apply = True)
    scale = util.ScaleEnum(apply = True)
    
    def default_view(self, **kwargs):
        return BinningWorkflowView(op = self, **kwargs)
    
    def clear_estimate(self):
        # no-op
        return
    
    def get_notebook_code(self, idx):
        op = BinningOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        

@provides(IWorkflowView)
class BinningWorkflowView(WorkflowFacetView, BinningView):
    op = Instance(IWorkflowOperation, fixed = True)
    channel = DelegatesTo('op')
    scale = DelegatesTo('op')
    huescale = DelegatesTo('op', 'scale', status = True)
    
    plot_params = Instance(HistogramPlotParams, ())
    
    # huefacet is overwritten by the call to plot() -- make sure
    # it's transient, so it doesn't get sync'ed.
    huefacet = Str(transient = True)
            
    def get_notebook_code(self, idx):
        view = BinningView()
        view.copy_traits(self, view.copyable_trait_names())
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{idx}{plot})
        """
        .format(idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.current_plot else "",
                traits = traits_str(view)))


### Serialization
@camel_registry.dumper(BinningWorkflowOp, 'binning', version = 1)
def _dump(op):
    return dict(name = op.name,
                channel = op.channel,
                scale = op.scale,
                bin_width = op.bin_width)
    
@camel_registry.loader('binning', version = 1)
def _load(data, version):
    if data['bin_width'] == 0:
        data['bin_width'] = None 
    
    return BinningWorkflowOp(**data)

@camel_registry.dumper(BinningWorkflowView, 'binning-view', version = 1)
def _dump_view(view):
    return dict(op = view.op,
                subset_list = view.subset_list)

@camel_registry.loader('binning-view', version = 1)
def _load_view(data, version):
    return BinningWorkflowView(**data)

