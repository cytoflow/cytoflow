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

from traits.api import (provides, Instance, Str, Property, observe,
                        List, Dict, Any, DelegatesTo, Array)

import numpy as np

from cytoflow.operations.density import DensityGateOp, DensityGateView
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowByView, DensityPlotParams
from ..serialization import camel_registry, traits_str, traits_repr, dedent
from ..subset import ISubset
from .. import Changed

from .operation_base import IWorkflowOperation, WorkflowOperation

DensityGateOp.__repr__ = traits_repr


@provides(IWorkflowOperation)
class DensityGateWorkflowOp(WorkflowOperation, DensityGateOp):    
    # add 'estimate' and 'apply' metadata
    name = Str(apply = True)
    xchannel = Str(estimate = True)
    ychannel = Str(estimate = True)
    keep = util.PositiveCFloat(0.9, allow_zero = False, estimate = True)
    by = List(Str, estimate = True)
    xscale = util.ScaleEnum(estimate = True)
    yscale = util.ScaleEnum(estimate = True)
        
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, estimate = True)
    
    # add 'estimate_result' metadata
    _histogram = Dict(Any, Array, transient = True, estimate_result = True)

    # bits to support the subset editor
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    def default_view(self, **kwargs):
        return DensityGateWorkflowView(op = self, **kwargs)
    
    def clear_estimate(self):
        self._xscale = self._yscale = None
        self._xbins = np.empty(1)
        self._ybins = np.empty(1)
        self._keep_xbins = dict()
        self._keep_ybins = dict()
        self._histogram = {}
            
        
    def apply(self, experiment):
        if not self._histogram:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        return DensityGateOp.apply(self, experiment)
            
    def get_notebook_code(self, idx):
        op = DensityGateOp()
        op.copy_traits(self, op.copyable_trait_names())      

        return dedent("""
        op_{idx} = {repr}
        
        op_{idx}.estimate(ex_{prev_idx}{subset})
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1,
                subset = ", subset = " + repr(self.subset) if self.subset else ""))
        

@provides(IWorkflowView)
class DensityGateWorkflowView(WorkflowByView, DensityGateView):
    op = Instance(IWorkflowOperation, fixed = True)
    subset = DelegatesTo('op')
    by = DelegatesTo('op')
    xchannel = DelegatesTo('op')
    xscale = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    yscale = DelegatesTo('op')
    
    plot_params = Instance(DensityPlotParams, ())
    
    def should_plot(self, changed, payload):
        if changed == Changed.RESULT:
            return False
        
        return True
            
    def get_notebook_code(self, idx):
        view = DensityGateView()
        view.copy_traits(self, view.copyable_trait_names())
        view.subset = self.subset
        plot_params_str = traits_str(self.plot_params)
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{idx}{plot_params})
        """
        .format(traits = traits_str(view),
                idx = idx,
                plot_params = ", " + plot_params_str if plot_params_str else ""))
    
@camel_registry.dumper(DensityGateWorkflowOp, 'density-gate', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                ychannel = op.ychannel,
                xscale = op.xscale,
                yscale = op.yscale,
                keep = op.keep,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('density-gate', version = 1)
def _load(data, version):
    return DensityGateWorkflowOp(**data)

@camel_registry.dumper(DensityGateWorkflowView, 'density-gate-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(DensityGateWorkflowView, 'density-gate-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op)

@camel_registry.loader('density-gate-view', version = any)
def _load_view(data, ver):
    return DensityGateWorkflowView(**data)



