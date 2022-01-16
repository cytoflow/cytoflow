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
cytoflowgui.workflow.operations.quad
------------------------------------

"""

from traits.api import provides, Instance, Str, Property, Tuple, observe

from cytoflow.operations.quad import QuadOp, ScatterplotQuadSelectionView
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowView, ScatterplotPlotParams
from ..serialization import camel_registry, traits_str, traits_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

QuadOp.__repr__ = traits_repr


@provides(IWorkflowView)
class QuadSelectionView(WorkflowView, ScatterplotQuadSelectionView):
    op = Instance(IWorkflowOperation, fixed = True)
    plot_params = Instance(ScatterplotPlotParams, ()) 
    
    _xy = Tuple(util.FloatOrNone(None), util.FloatOrNone(None), status = True)
    xthreshold = Property(util.FloatOrNone(None), observe = '_xy')
    ythreshold = Property(util.FloatOrNone(None), observe = '_xy')
        
    # data flow: user clicks cursor. remote canvas calls _onclick, sets 
    # _xy. _xy is copied back to local view (because it's "status = True").
    # _update_xy is called, and because self.interactive is false, then
    # the operation is updated (atomically, both x and y at once.)  the
    # operation's _xy is sent back to the remote operation (because 
    # "apply = True"), where the operation is updated. 
    
    # xthreshold and ythreshold are properties (both in the view and
    # in the operation) so that x and y update can happen atomically. 
    # otherwise, they happen one after the other, which is noticably
    # slow!
    
    def _onclick(self, event):
        """Update the threshold location"""
        self._xy = (event.xdata, event.ydata)        
        
    @observe('_xy')
    def _update_xy(self, _):
        if not self.interactive:
            self.op._xy = self._xy

    def _get_xthreshold(self):
        return self._xy[0]

    def _get_ythreshold(self):
        return self._xy[1]
    
    def clear_estimate(self):
        # no-op
        return
        
    def get_notebook_code(self, idx):
        view = ScatterplotQuadSelectionView()
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
class QuadWorkflowOp(WorkflowOperation, QuadOp):
    name = Str(apply = True)
    xchannel = Str(apply = True)
    ychannel = Str(apply = True)
    
    _xy = Tuple(util.FloatOrNone(None), util.FloatOrNone(None), apply = True)
    xthreshold = Property(util.FloatOrNone(None), observe = '_xy')
    ythreshold = Property(util.FloatOrNone(None), observe = '_xy')
    
    def _get_xthreshold(self):
        return self._xy[0]
    
    def _set_xthreshold(self, val):
        self._xy = (val, self._xy[1])

    def _get_ythreshold(self):
        return self._xy[1]
    
    def _set_ythreshold(self, val):
        self._xy = (self._xy[0], val)

    def default_view(self, **kwargs):
        return QuadSelectionView(op = self, **kwargs)
    
    def clear_estimate(self):
        # no-op
        return
    
    def get_notebook_code(self, idx):
        op = QuadOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        
        
### Serialization
@camel_registry.dumper(QuadWorkflowOp, 'quad', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                xthreshold = op.xthreshold,
                ychannel = op.ychannel,
                ythreshold = op.ythreshold)
    
@camel_registry.loader('quad', version = 1)
def _load(data, version):
    return QuadWorkflowOp(**data)

@camel_registry.dumper(QuadSelectionView, 'quad-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                xscale = view.xscale,
                yscale = view.yscale,
                huefacet = view.huefacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(QuadSelectionView, 'quad-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op,
                xscale = view.xscale,
                yscale = view.yscale,
                huefacet = view.huefacet,
                subset_list = view.subset_list)
    
@camel_registry.loader('quad-view', version = any)
def _load_view(data, version):
    return QuadSelectionView(**data)

