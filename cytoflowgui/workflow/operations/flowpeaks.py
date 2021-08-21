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
cytoflowgui.workflow.operations.flowpeaks
-----------------------------------------

"""

from traits.api import (provides, Instance, Str, Property, observe, Constant,
                        List, Dict, Any, DelegatesTo, Bool)

from cytoflow.operations.flowpeaks import FlowPeaksOp, FlowPeaks2DView, FlowPeaks2DDensityView, By2DView
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowByView, ScatterplotPlotParams, DensityPlotParams
from ..serialization import camel_registry, traits_str, traits_repr, dedent
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

FlowPeaksOp.__repr__ = traits_repr


@provides(IWorkflowOperation)
class FlowPeaksWorkflowOp(WorkflowOperation, FlowPeaksOp):
    # add "apply" and "estimate" metadata
    name = Str(apply = True)
    xchannel = Str(estimate = True)
    ychannel = Str(estimate = True)
    xscale = util.ScaleEnum(estimate = True)
    yscale = util.ScaleEnum(estimate = True)
    h = util.PositiveCFloat(1.5, allow_zero = False, estimate = True)
    h0 = util.PositiveCFloat(1, allow_zero = False, estimate = True)
    tol = util.PositiveCFloat(0.5, allow_zero = False, estimate = True)
    merge_dist = util.PositiveCFloat(5, allow_zero = False, estimate = True)
    
    by = List(Str, estimate = True)
    
    # add the 'estimate_result' metadata
    _cluster_peak = Dict(Any, List, transient = True, estimate_result = True)

    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, estimate = True)
        
    # bits to support the subset editor
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    # @on_trait_change('xchannel, ychannel')
    # def _channel_changed(self):
    #     self.channels = []
    #     self.scale = {}
    #     if self.xchannel:
    #         self.channels.append(self.xchannel)
    #
    #         if self.xchannel in self.scale:
    #             del self.scale[self.xchannel]
    #
    #         self.scale[self.xchannel] = self.xscale
    #
    #     if self.ychannel:
    #         self.channels.append(self.ychannel)
    #
    #         if self.ychannel in self.scale:
    #             del self.scale[self.ychannel]
    #
    #         self.scale[self.ychannel] = self.yscale
    #
    #
    # @on_trait_change('xscale, yscale')
    # def _scale_changed(self):
    #     self.scale = {}
    #
    #     if self.xchannel:
    #         self.scale[self.xchannel] = self.xscale
    #
    #     if self.ychannel:
    #         self.scale[self.ychannel] = self.yscale
            

    def default_view(self, **kwargs):
        return FlowPeaksWorkflowView(op = self, **kwargs)
    
    def estimate(self, experiment):
        if not self.xchannel:
            raise util.CytoflowOpError('xchannel',
                                       "Must set X channel")
            
        if not self.ychannel:
            raise util.CytoflowOpError('ychannel',
                                       "Must set Y channel")
            
            
        self.channels = [self.xchannel, self.ychannel]
        self.scale = {self.xchannel : self.xscale,
                      self.ychannel : self.yscale}
            
        super().estimate(experiment, subset = self.subset)
        
    def apply(self, experiment):
        if not self._cluster_group:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        return super().apply(experiment)
    
    def clear_estimate(self):
        self._kmeans = {}
        self._means = {}
        self._normals = {}
        self._density = {}
        self._peaks = {}
        self._peak_clusters = {}
        self._cluster_peak = {}
        self._cluster_group = {}
        self._scale = {}
            
    def get_notebook_code(self, idx):
        op = FlowPeaksOp()
        op.copy_traits(self, op.copyable_trait_names())    
        op.channels = [self.xchannel, self.ychannel]  
        op.scale = {self.xchannel : self.xscale,
                    self.ychannel : self.yscale}

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
class FlowPeaksWorkflowView(WorkflowByView, By2DView):
    op = Instance(IWorkflowOperation, fixed = True)
    subset = DelegatesTo('op')
    by = DelegatesTo('op')
    xchannel = DelegatesTo('op')
    xscale = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    yscale = DelegatesTo('op')
    plot_params = Property()
    scatterplot_plot_params = Instance(ScatterplotPlotParams, ())
    density_plot_params = Instance(DensityPlotParams, ())
    
    show_density = Bool(False)
    
    id = "edu.mit.synbio.cytoflowgui.op_plugins.flowpeaks"
    friendly_id = "FlowPeaks" 
    
    name = Constant("FlowPeaks")
    
    def _get_plot_params(self):
        if self.show_density:
            return self.density_plot_params
        else:
            return self.scatterplot_plot_params
    
    @observe('scatterplot_plot_params:+type')
    def _on_scatterplot_plot_params_changed(self, event):
        self.changed = 'scatterplot_plot_params'
    
    @observe('density_plot_params:+type')
    def _on_density_plot_params_changed(self, event):
        self.changed = 'density_plot_params'
    
    def plot(self, experiment, **kwargs):
        if self.show_density:
            FlowPeaks2DDensityView(op = self.op,
                                   xchannel = self.xchannel,
                                   ychannel = self.ychannel,
                                   xscale = self.xscale,
                                   yscale = self.yscale).plot(experiment, **kwargs)
        else:
            FlowPeaks2DView(op = self.op,
                            xchannel = self.xchannel,
                            ychannel = self.ychannel,
                            xscale = self.xscale,
                            yscale = self.yscale).plot(experiment, **kwargs)
            
    def get_notebook_code(self, idx):
        view = FlowPeaks2DView()
        trait_names = view.copyable_trait_names()
        trait_names.remove('xchannel')
        trait_names.remove('xscale')
        trait_names.remove('ychannel')
        trait_names.remove('yscale')
        view.copy_traits(self, trait_names)
        view.subset = self.subset

        if self.show_density:        
            plot_params_str = traits_str(self.density_plot_params)
        else:
            plot_params_str = traits_str(self.scatterplot_plot_params)


        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{idx}{plot}{plot_params})
        """
        .format(traits = traits_str(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.current_plot else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))
        
        
### serialization
@camel_registry.dumper(FlowPeaksWorkflowOp, 'flowpeaks', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                ychannel = op.ychannel,
                xscale = op.xscale,
                yscale = op.yscale,
                h = op.h,
                h0 = op.h0,
                tol = op.tol,
                merge_dist = op.merge_dist,
                subset_list = op.subset_list)
    
@camel_registry.loader('flowpeaks', version = 1)
def _load(data, version):
    return FlowPeaksWorkflowOp(**data)

@camel_registry.dumper(FlowPeaksWorkflowView, 'flowpeaks-view', version = 3)
def _dump_view(view):
    return dict(op = view.op,
                show_density = view.show_density,
                scatterplot_plot_params = view.scatterplot_plot_params,
                density_plot_params = view.density_plot_params)

@camel_registry.dumper(FlowPeaksWorkflowView, 'flowpeaks-view', version = 2)
def _dump_view_v2(view):
    return dict(op = view.op,
                show_density = view.show_density,
                plot_params = view.plot_params,
                scatterplot_plot_params = view.scatterplot_plot_params,
                density_plot_params = view.density_plot_params)

@camel_registry.dumper(FlowPeaksWorkflowView, 'flowpeaks-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op,
                show_density = view.show_density)

@camel_registry.loader('flowpeaks-view', version = any)
def _load_view(data, ver):
    if 'plot_params' in data:
        del data['plot_params']
        
    return FlowPeaksWorkflowView(**data)
    