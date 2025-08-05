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

from traits.api import provides, Instance, Str, observe, List, Float, Bool, Enum, Constant

from cytoflow.operations.polygon import PolygonOp, ScatterplotPolygonSelectionView, DensityPolygonSelectionView, Op2DView, _PolygonSelection
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowView
from ..views.view_base import Data2DPlotParams
from ..views.scatterplot import SCATTERPLOT_MARKERS
from ..serialization import camel_registry, traits_str, cytoflow_class_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

PolygonOp.__repr__ = cytoflow_class_repr

class PolygonPlotParams(Data2DPlotParams):
    density = Bool(False)
    
    # density-specific
    gridsize = util.PositiveCInt(50, allow_zero = False)
    smoothed = Bool(False)
    smoothed_sigma = util.PositiveCFloat(1.0, allow_zero = False)

    # scatterplot-specific
    alpha = util.PositiveCFloat(0.25)
    s = util.PositiveCFloat(2)
    marker = Enum(SCATTERPLOT_MARKERS)

class _PolygonSelectionWorkflowView(_PolygonSelection):
    parent = Instance(IWorkflowView)

    _vertices = List((Float, Float), status = True)
    
    # data flow: user choose polygon. upon double click, the remote 
    # canvas calls _onselect, sets _vertices. _vertices is copied back to 
    # local view (because it's  "status = True"). _update_vertices is called, 
    # and because self.interactive is false, then the operation is updated.  the
    # operation's vertices is sent back to the remote operation (because 
    # "apply = True"), where the remote operation is updated.    
    
    def _onselect(self, vertices):
        self.parent._vertices = vertices
        
@provides(IWorkflowView)
class ScatterplotPolygonSelectionWorkflowView(_PolygonSelectionWorkflowView, ScatterplotPolygonSelectionView):
    pass

@provides(IWorkflowView)
class DensityPolygonSelectionWorkflowView(_PolygonSelectionWorkflowView, DensityPolygonSelectionView):
    pass

@provides(IWorkflowView)
class PolygonSelectionView(WorkflowView, Op2DView):
    id = Constant('cytoflowgui.workflow.operations.polygonview')

    op = Instance(IWorkflowOperation, fixed = True)
    plot_params = Instance(PolygonPlotParams, ()) 
    
    _view = Instance(IWorkflowView)
    _vertices = List((Float, Float), status = True)
    
    interactive = Bool(False, transient = True)
        
    @observe('_vertices')
    def _update_vertices(self, _):
        self.op.vertices = self._vertices
        
    @observe('xchannel,ychannel,xscale,yscale', post_init = True)
    def _reset_polygon(self, _):
        self._vertices = []
        self.op.vertices = []
        
    def clear_estimate(self):
        # no-op
        return
    
    def plot(self, experiment, **kwargs):
        density = kwargs.pop('density')
        if density:
            kwargs.pop('alpha')
            kwargs.pop('s')
            kwargs.pop('marker')
            if not self._view or not isinstance(self._view, DensityPolygonSelectionWorkflowView):
                self._view = DensityPolygonSelectionWorkflowView(op = self.op,
                                                                 parent = self, 
                                                                 interactive = self.interactive,
                                                                 huescale = self.huescale)
            kwargs['patch_props'] = {'edgecolor' : 'white', 'linewidth' : 3, 'fill' : False}
        else:
            kwargs.pop('gridsize')
            kwargs.pop('smoothed')
            kwargs.pop('smoothed_sigma')
            if not self._view or not isinstance(self._view, ScatterplotPolygonSelectionWorkflowView):
                self._view = ScatterplotPolygonSelectionWorkflowView(op = self.op,
                                                                     parent = self,
                                                                     interactive = self.interactive,
                                                                     huefacet = self.huefacet)
            kwargs['patch_props'] = {'edgecolor' : 'black', 'linewidth' : 3, 'fill' : False}

        self._view.plot(experiment, **kwargs)
        
    def get_notebook_code(self, idx):
        if self.plot_params.density:
            view = DensityPolygonSelectionWorkflowView()
            plot_params = self.plot_params.clone_traits(copy = "deep")
            plot_params.reset_traits(traits = ['density', 'alpha', 's', 'marker'])
        else:
            view = ScatterplotPolygonSelectionWorkflowView()
            plot_params = self.plot_params.clone_traits(copy = "deep")
            plot_params.reset_traits(traits = ['density', 'gridsize', 'smoothed', 'smoothed_sigma'])
            
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(plot_params)
        
        return dedent("""
        op_{idx}.default_view({traits}{comma}{density}).plot(ex_{prev_idx}{plot_params})
        """
        .format(idx = idx,
                traits = traits_str(view), 
                comma = ", " if traits_str(view) and self.plot_params.density else "",
                density = "density = True" if self.plot_params.density else "",
                prev_idx = idx - 1,
                plot_params = ", " + plot_params_str if plot_params_str else ""))
        
    @observe('interactive', post_init = True)
    def _interactive(self, _):
        if self._view:
            self._view.interactive = self.interactive
            
    @observe('_vertices', post_init = True)
    def _update_range(self, _):
        self.op.vertices = self._vertices
        
    @observe('huefacet', post_init = True)
    def _update_huefacet(self, _):
        if self._view:
            self._view.huefacet = self.huefacet
        
    @observe('huescale', post_init = True)
    def _update_huescale(self, _):
        if self._view:
            self._view.huescale = self.huescale
        
    
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

@camel_registry.dumper(PolygonSelectionView, 'polygon-view', version = 3)
def _dump_view(view):
    return dict(op = view.op,
                huefacet = view.huefacet,
                huescale = view.huescale,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)

@camel_registry.dumper(PolygonSelectionView, 'polygon-view', version = 2)
def _dump_view_v2(view):
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

@camel_registry.dumper(PolygonPlotParams, 'polygon-params', version = 1)
def _dump_view_params(params):
    return dict(density = params.density,
                
                # BasePlotParams
                title = params.title,
                xlabel = params.xlabel,
                ylabel = params.ylabel,
                huelabel = params.huelabel,
                col_wrap = params.col_wrap,
                sns_style = params.sns_style,
                sns_context = params.sns_context,
                legend = params.legend,
                sharex = params.sharex,
                sharey = params.sharey,
                despine = params.despine,

                # DataplotParams
                min_quantile = params.min_quantile,
                max_quantile = params.max_quantile,
                
                # Data2DPlotParams
                xlim = params.xlim,
                ylim = params.ylim,
                
                # Scatterplot params
                alpha = params.alpha,
                s = params.s,
                marker = params.marker,
                
                 # Density plot params
                gridsize = params.gridsize,
                smoothed = params.smoothed,
                smoothed_sigma = params.smoothed_sigma )
    
@camel_registry.loader('polygon-params', version = any)
def _load_params(data, version):
    return PolygonPlotParams(**data)
