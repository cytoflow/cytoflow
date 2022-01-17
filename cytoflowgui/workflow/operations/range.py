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
cytoflowgui.workflow.operations.range
-------------------------------------

"""

from traits.api import provides, Instance, Str, Tuple, Property, observe

from cytoflow.operations.range import RangeOp, RangeSelection
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowView, HistogramPlotParams
from ..serialization import camel_registry, traits_str, traits_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

RangeOp.__repr__ = traits_repr


@provides(IWorkflowView)
class RangeSelectionView(WorkflowView, RangeSelection):
    op = Instance(IWorkflowOperation, fixed = True)
    plot_params = Instance(HistogramPlotParams, ())
    
    _range = Tuple(util.FloatOrNone(None), util.FloatOrNone(None), status = True)
    low = Property(util.FloatOrNone(None), observe = '_range')
    high = Property(util.FloatOrNone(None), observe = '_range')
    
    # data flow: user drags cursor. remote canvas calls _onselect, sets 
    # _range. _range is copied back to local view (because it's 
    # "status = True"). _update_range is called, and because 
    # self.interactive is false, then the operation is updated.  the
    # operation's range is sent back to the remote operation (because 
    # "apply = True"), where the remote operation is updated.
    
    # low ahd high are properties (both in the view and in the operation) 
    # so that the update can happen atomically. otherwise, they happen 
    # one after the other, which is noticably slow!
    
    def _onselect(self, xmin, xmax): 
        """Update selection traits"""
        self._range = (xmin, xmax)
        
    @observe('_range')
    def _update_range(self, _):
        if not self.interactive:
            self.op._range = self._range

    def _get_low(self):
        return self._range[0]

    def _get_high(self):
        return self._range[1]
    
    def clear_estimate(self):
        # no-op
        return
        
    def get_notebook_code(self, idx):
        view = RangeSelection()
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
class RangeWorkflowOp(WorkflowOperation, RangeOp):
    name = Str(apply = True)
    channel = Str(apply = True)
    
    _range = Tuple(util.FloatOrNone(None), util.FloatOrNone(None), apply = True)
    low = Property(util.FloatOrNone(None), observe = '_range')
    high = Property(util.FloatOrNone(None), observe = '_range')
    
    def _get_low(self):
        return self._range[0]
    
    def _set_low(self, val):
        self._range = (val, self._range[1])

    def _get_high(self):
        return self._range[1]
    
    def _set_high(self, val):
        self._range = (self._range[0], val)
    
    def default_view(self, **kwargs):
        return RangeSelectionView(op = self, **kwargs)
    
    def get_notebook_code(self, idx):
        op = RangeOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        
        
### Serialization
@camel_registry.dumper(RangeWorkflowOp, 'range', version = 1)
def _dump(op):
    return dict(name = op.name,
                channel = op.channel,
                low = op.low,
                high = op.high)
    
@camel_registry.loader('range', version = 1)
def _load(data, version):
    return RangeWorkflowOp(**data)

@camel_registry.dumper(RangeSelectionView, 'range-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                scale = view.scale,
                huefacet = view.huefacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(RangeSelectionView, 'range-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op,
                scale = view.scale,
                huefacet = view.huefacet,
                subset_list = view.subset_list)
    
@camel_registry.loader('range-view', version = any)
def _load_view(data, version):
    return RangeSelectionView(**data)



    