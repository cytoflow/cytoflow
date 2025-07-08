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
cytoflowgui.workflow.operations.polygon
---------------------------------------

"""

from traits.api import provides, Instance, Str, List, Float, Bool, Callable

from cytoflow.operations.mst import MSTOp, MSTSelectionView

from ..views import IWorkflowView, WorkflowView, MSTPlotParams
from ..serialization import camel_registry, traits_str, cytoflow_class_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

MSTOp.__repr__ = cytoflow_class_repr


@provides(IWorkflowView)
class MSTWorkflowSelectionView(WorkflowView, MSTSelectionView):
    op = Instance(IWorkflowOperation, fixed = True)
    plot_params = Instance(MSTPlotParams, ()) 
    
    # callables aren't picklable, so make this one transient 
    # and send scale_by_events instead
    size_function = Callable(transient = True)
    scale_by_events = Bool(False)
    
    _polygon = List((Float, Float), status = True)

    # data flow: user choose polygon. upon closing, the remote 
    # canvas calls _onselect, sets _vertices. _vertices is copied back to 
    # local view (because it's  "status = True"). _update_polygon is called, 
    # and because self.interactive is false, then the operation is updated.  the
    # operation's vertices is sent back to the remote operation (because 
    # "apply = True"), where the remote operation is updated.    
    
    # def _onselect(self, vertices):
    #     self._vertices = vertices
        
    # @observe('_polygon')
    # def _update_polygon(self, _):
    #     if not self.interactive:
    #         pass
            # self.op.vertices = self._vertices
        
    def clear_estimate(self):
        # no-op
        return
        
    def get_notebook_code(self, idx):
        view = MSTSelectionView()
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
class MSTWorkflowOp(WorkflowOperation, MSTOp):
    name = Str(apply = True)
    
    condition = Str(apply = True)
    condition_values = List(Str, apply = True)
    
    def default_view(self, **kwargs):
        return MSTWorkflowSelectionView(op = self, **kwargs)
    
    def get_notebook_code(self, idx):
        op = MSTOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        
        
# ### Serialization
# @camel_registry.dumper(MSTWorkflowOp, 'mst-op', version = 1)
# def _dump(op):
#     return dict(name = op.name,
#                 xchannel = op.xchannel,
#                 ychannel = op.ychannel,
#                 vertices = op.vertices,
#                 xscale = op.xscale,
#                 yscale = op.yscale)
#
# @camel_registry.loader('mst-op', version = 1)
# def _load(data, version):
#     # data['vertices'] = [(v[0], v[1]) for v in data['vertices']]
#     return MSTWorkflowOp(**data)
#
# @camel_registry.dumper(MSTSelectionView, 'mst-selection-view', version = 2)
# def _dump_view(view):
#     return dict(op = view.op,
#                 huefacet = view.huefacet,
#                 subset_list = view.subset_list,
#                 plot_params = view.plot_params,
#                 current_plot = view.current_plot)
#
# @camel_registry.dumper(PolygonSelectionView, 'polygon-view', version = 1)
# def _dump_view_v1(view):
#     return dict(op = view.op,
#                 huefacet = view.huefacet,
#                 subset_list = view.subset_list)
#
# @camel_registry.loader('polygon-view', version = any)
# def _load_view(data, version):
#     return PolygonSelectionView(**data)
