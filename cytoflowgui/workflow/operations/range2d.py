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
cytoflowgui.workflow.operations.range2d
---------------------------------------

"""

from traits.api import (provides, Instance, Str, Property, Tuple, Constant, 
                        Bool, Enum, observe)

from cytoflow.operations.range2d import Range2DOp, Op2DView, ScatterplotRangeSelection2DView, DensityRangeSelection2DView, _RangeSelection2D
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowView
from ..views.scatterplot import SCATTERPLOT_MARKERS
from ..views.view_base import Data2DPlotParams
from ..serialization import camel_registry, traits_str, cytoflow_class_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

Range2DOp.__repr__ = cytoflow_class_repr

class Range2DPlotParams(Data2DPlotParams):
    density = Bool(False)
    
    # density-specific
    gridsize = util.PositiveCInt(50, allow_zero = False)
    smoothed = Bool(False)
    smoothed_sigma = util.PositiveCFloat(1.0, allow_zero = False)

    # scatterplot-specific
    alpha = util.PositiveCFloat(0.25)
    s = util.PositiveCFloat(2)
    marker = Enum(SCATTERPLOT_MARKERS)
    
class _RangeSelection2DWorkflowView(_RangeSelection2D):
    parent = Instance(IWorkflowView)
    
    # data flow: user drags cursor. remote canvas calls _onselect, sets 
    # _range. _range is copied back to local view (because it's 
    # "status = True"). _update_range is called, and because 
    # self.interactive is false, then the operation is updated.  the
    # operation's range is sent back to the remote operation (because 
    # "apply = True"), where the remote operation is updated.
    
    # low ahd high are properties (both in the view and in the operation) 
    # so that the update can happen atomically. otherwise, they happen 
    # one after the other, which is noticably slow!
            
    def _onselect(self, pos1, pos2): 
        """Update selection traits"""
        self.parent._range = (min(pos1.xdata, pos2.xdata),
                       max(pos1.xdata, pos2.xdata),
                       min(pos1.ydata, pos2.ydata),
                       max(pos1.ydata, pos2.ydata))
    
@provides(IWorkflowView)
class ScatterPlotRangeSelection2DWorkflowView(_RangeSelection2DWorkflowView, ScatterplotRangeSelection2DView):
    pass

@provides(IWorkflowView)

class DensityRangeSelection2DWorkflowView(_RangeSelection2DWorkflowView, DensityRangeSelection2DView):
    pass

@provides(IWorkflowView)
class Range2DSelectionView(WorkflowView, Op2DView):
    id = Constant('cytoflowgui.workflow.operations.range2dview')

    op = Instance(IWorkflowOperation, fixed = True)
    plot_params = Instance(Range2DPlotParams, ())
    
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    
    _view = Instance(IWorkflowView)
    _range = Tuple(util.FloatOrNone(None), util.FloatOrNone(None),
                   util.FloatOrNone(None), util.FloatOrNone(None), status = True)
    
    interactive = Bool(False, transient = True)

    def clear_estimate(self):
        # no-op
        return
    
    def plot(self, experiment, **kwargs):
        density = kwargs.pop('density')
        if density:
            kwargs.pop('alpha')
            kwargs.pop('s')
            kwargs.pop('marker')
            if not self._view or not isinstance(self._view, DensityRangeSelection2DWorkflowView):
                self._view = DensityRangeSelection2DWorkflowView(op = self.op,
                                                                 parent = self, 
                                                                 interactive = self.interactive,
                                                                 huescale = self.huescale)
            kwargs['patch_props'] = {'edgecolor' : 'white', 'linewidth' : 3, 'fill' : False}
        else:
            kwargs.pop('gridsize')
            kwargs.pop('smoothed')
            kwargs.pop('smoothed_sigma')
            if not self._view or not isinstance(self._view, ScatterPlotRangeSelection2DWorkflowView):
                self._view = ScatterPlotRangeSelection2DWorkflowView(op = self.op,
                                                                     parent = self,
                                                                     interactive = self.interactive,
                                                                     huefacet = self.huefacet)
            kwargs['patch_props'] = {'edgecolor' : 'black', 'linewidth' : 3, 'fill' : False}

        self._view.plot(experiment, **kwargs)
        
    def get_notebook_code(self, idx):
        if self.plot_params.density:
            view = DensityRangeSelection2DWorkflowView()
            plot_params = self.plot_params.clone_traits(copy = "deep")
            plot_params.reset_traits(traits = ['density', 'alpha', 's', 'marker'])
        else:
            view = ScatterPlotRangeSelection2DWorkflowView()
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
            
    @observe('_range', post_init = True)
    def _update_range(self, _):
        self.op._range = self._range
        
    @observe('huefacet', post_init = True)
    def _update_huefacet(self, _):
        if self._view:
            self._view.huefacet = self.huefacet
        
    @observe('huescale', post_init = True)
    def _update_huescale(self, _):
        if self._view:
            self._view.huescale = self.huescale

    
@provides(IWorkflowOperation)
class Range2DWorkflowOp(WorkflowOperation, Range2DOp):
    name = Str(apply = True)
    xchannel = Str(apply = True)
    ychannel = Str(apply = True)
    
    _range = Tuple(util.FloatOrNone(None), util.FloatOrNone(None), 
                   util.FloatOrNone(None), util.FloatOrNone(None), apply = True)
    xlow = Property(util.FloatOrNone(None), observe = '_range')
    xhigh = Property(util.FloatOrNone(None), observe = '_range')
    ylow = Property(util.FloatOrNone(None), observe = '_range')
    yhigh = Property(util.FloatOrNone(None), observe = '_range')
    
    def _get_xlow(self):
        return self._range[0]
    
    def _set_xlow(self, val):
        self._range = (val, self._range[1], self._range[2], self._range[3])

    def _get_xhigh(self):
        return self._range[1]
    
    def _set_xhigh(self, val):
        self._range = (self._range[0], val, self._range[2], self._range[3])
        
    def _get_ylow(self):
        return self._range[2]
    
    def _set_ylow(self, val):
        self._range = (self._range[0], self._range[1], val, self._range[3])

    def _get_yhigh(self):
        return self._range[3]
    
    def _set_yhigh(self, val):
        self._range = (self._range[0], self._range[1], self._range[2], val)
    
    def default_view(self, **kwargs):
        return Range2DSelectionView(op = self, **kwargs)
    
    def get_notebook_code(self, idx):
        op = Range2DOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        
        
### Serialization
@camel_registry.dumper(Range2DWorkflowOp, 'range2d', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                xlow = op.xlow,
                xhigh = op.xhigh,
                ychannel = op.ychannel,
                ylow = op.ylow,
                yhigh = op.yhigh)
    
@camel_registry.loader('range2d', version = 1)
def _load(data, version):
    return Range2DWorkflowOp(**data)

@camel_registry.dumper(Range2DSelectionView, 'range2d-view', version = 3)
def _dump_view(view):
    return dict(op = view.op,
                xscale = view.xscale,
                yscale = view.yscale,
                huefacet = view.huefacet,
                huescale = view.huescale,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)

@camel_registry.dumper(Range2DSelectionView, 'range2d-view', version = 2)
def _dump_view_v2(view):
    return dict(op = view.op,
                xscale = view.xscale,
                yscale = view.yscale,
                huefacet = view.huefacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(Range2DSelectionView, 'range2d-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op,
                xscale = view.xscale,
                yscale = view.yscale,
                huefacet = view.huefacet,
                subset_list = view.subset_list)
    
@camel_registry.loader('range2d-view', version = any)
def _load_view(data, version):
    return Range2DSelectionView(**data)

@camel_registry.dumper(Range2DPlotParams, 'range2d-params', version = 1)
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
    
@camel_registry.loader('range2d-params', version = any)
def _load_params(data, version):
    return Range2DPlotParams(**data)

