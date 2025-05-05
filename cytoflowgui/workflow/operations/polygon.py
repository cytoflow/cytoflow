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

from traits.api import provides, Instance, Str, observe, List, Float

from cytoflow.operations.polygon import PolygonOp, ScatterplotPolygonSelectionView
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowView, ScatterplotPlotParams
from ..serialization import camel_registry, traits_str, cytoflow_class_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

PolygonOp.__repr__ = cytoflow_class_repr


@provides(IWorkflowView)
class PolygonSelectionView(WorkflowView, ScatterplotPolygonSelectionView):
    op = Instance(IWorkflowOperation, fixed = True)
    plot_params = Instance(ScatterplotPlotParams, ()) 
    
    _vertices = List((Float, Float), status = True)

    # data flow: user choose polygon. upon double click, the remote 
    # canvas calls _onselect, sets _vertices. _vertices is copied back to 
    # local view (because it's  "status = True"). _update_vertices is called, 
    # and because self.interactive is false, then the operation is updated.  the
    # operation's vertices is sent back to the remote operation (because 
    # "apply = True"), where the remote operation is updated.    
    
    def _onselect(self, vertices):
        self._vertices = vertices
        
    @observe('_vertices')
    def _update_vertices(self, _):
        if not self.interactive:
            self.op.vertices = self._vertices
        
    @observe('xchannel,ychannel,xscale,yscale', post_init = True)
    def _reset_polygon(self, _):
        self._vertices = []
        self.op.vertices = []
        
    def clear_estimate(self):
        # no-op
        return
        
    def get_notebook_code(self, idx):
        view = ScatterplotPolygonSelectionView()
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
class PolygonWorkflowOp(WorkflowOperation, PolygonOp):
    name = Str(apply = True)
    xchannel = Str(apply = True)
    ychannel = Str(apply = True)
    
    vertices = List((Float, Float), apply = True)
    
    # there's a bit of a subtlety here: if the vertices were 
    # selected on a plot with scaled axes, we need to apply that 
    # scale function to both the vertices and the data before 
    # looking for path membership

    xscale = util.ScaleEnum(apply = True)
    yscale = util.ScaleEnum(apply = True)
    
    def default_view(self, **kwargs):
        return PolygonSelectionView(op = self, **kwargs)
    
    def get_notebook_code(self, idx):
        op = PolygonOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        
        
### Serialization
@camel_registry.dumper(PolygonWorkflowOp, 'polygon', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                ychannel = op.ychannel,
                vertices = op.vertices,
                xscale = op.xscale,
                yscale = op.yscale)
    
@camel_registry.loader('polygon', version = 1)
def _load(data, version):
    data['vertices'] = [(v[0], v[1]) for v in data['vertices']]
    return PolygonWorkflowOp(**data)

@camel_registry.dumper(PolygonSelectionView, 'polygon-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                huefacet = view.huefacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(PolygonSelectionView, 'polygon-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op,
                huefacet = view.huefacet,
                subset_list = view.subset_list)

@camel_registry.loader('polygon-view', version = any)
def _load_view(data, version):
    return PolygonSelectionView(**data)
