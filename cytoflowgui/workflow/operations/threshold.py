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

"""
cytoflowgui.workflow.operations.threshold
-----------------------------------------

"""

from traits.api import provides, Instance, Str, observe

from cytoflow.operations.threshold import ThresholdOp, ThresholdSelection
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowView, HistogramPlotParams
from ..serialization import camel_registry, traits_str, traits_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

ThresholdOp.__repr__ = traits_repr

@provides(IWorkflowView)
class ThresholdSelectionView(WorkflowView, ThresholdSelection):
    op = Instance(IWorkflowOperation, fixed = True)
    threshold = util.FloatOrNone(None, status = True)
    plot_params = Instance(HistogramPlotParams, ())
    
    # data flow: user clicks cursor. remote canvas calls _onclick, sets 
    # threshold. threshold is copied back to local view (because it's 
    # "status = True"). _update_threshold is called, and because 
    # self.interactive is false, then the operation is updated.  the
    # operation's threshold is sent back to the remote operation (because 
    # "apply = True"), where the remote operation is updated.
    
    def _onclick(self, event):
        """Update the threshold location"""
        # sometimes the axes aren't set up and we don't get xdata (??)
        if event.xdata:
            self.threshold = event.xdata
    
    @observe('threshold')
    def _update_threshold(self, _):
        if not self.interactive:
            self.op.threshold = self.threshold
        
    def get_notebook_code(self, idx):
        view = ThresholdSelection()
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(self.plot_params)
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx}{plot_params})
        """
        .format(idx = idx, 
                traits = traits_str(view),
                prev_idx = idx - 1,
                plot_params = ", " + plot_params_str if plot_params_str else ""))
        
    
@provides(IWorkflowOperation)
class ThresholdWorkflowOp(WorkflowOperation, ThresholdOp):
    name = Str(apply = True)
    channel = Str(apply = True)
    threshold = util.FloatOrNone(None, apply = True)
     
    def default_view(self, **kwargs):
        return ThresholdSelectionView(op = self, **kwargs)
    
    def clear_estimate(self):
        # no-op
        return
    
    def get_notebook_code(self, idx):
        op = ThresholdOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))

    
### Serialization
@camel_registry.dumper(ThresholdWorkflowOp, 'threshold', version = 1)
def _dump(op):
    return dict(name = op.name,
                channel = op.channel,
                threshold = op.threshold)
    
@camel_registry.loader('threshold', version = 1)
def _load(data, version):
    return ThresholdWorkflowOp(**data)

@camel_registry.dumper(ThresholdSelectionView, 'threshold-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                scale = view.scale,
                huefacet = view.huefacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(ThresholdSelectionView, 'threshold-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op,
                scale = view.scale,
                huefacet = view.huefacet,
                subset_list = view.subset_list)
    
@camel_registry.loader('threshold-view', version = any)
def _load_view(data, version):
    return ThresholdSelectionView(**data)
