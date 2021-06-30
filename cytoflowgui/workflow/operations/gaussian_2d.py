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

from traits.api import (provides, Instance, Str, Property, observe, Constant,
                        List, Dict, Any, DelegatesTo)

from sklearn import mixture

from cytoflow.operations.gaussian import GaussianMixtureOp, GaussianMixture2DView
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowByView, ScatterplotPlotParams
from ..serialization import camel_registry, traits_str, traits_repr, dedent
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

GaussianMixtureOp.__repr__ = traits_repr

@provides(IWorkflowOperation)    
class GaussianMixture2DWorkflowOp(WorkflowOperation, GaussianMixtureOp):
    # override id so we can differentiate the 1D and 2D ops
    id = Constant('edu.mit.synbio.cytoflowgui.operations.gaussian_2d')

    # add 'estimate' and 'apply' metadata
    name = Str(apply = True)
    xchannel = Str(estimate = True)
    ychannel = Str(estimate = True)
    xscale = util.ScaleEnum(estimate = True)
    yscale = util.ScaleEnum(estimate = True)
    num_components = util.PositiveCInt(1, allow_zero = False, estimate = True)
    sigma = util.PositiveCFloat(None, allow_zero = True, allow_none = True, estimate = True)
    by = List(Str, estimate = True)
    
    # add the 'estimate_result' metadata
    _gmms = Dict(Any, Instance(mixture.GaussianMixture), transient = True,
                 estimate_result = True)
 
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
    
    def default_view(self, **kwargs):
        return GaussianMixture2DWorkflowView(op = self, **kwargs)
    
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
        if not self._gmms:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        return GaussianMixtureOp.apply(self, experiment)

    def clear_estimate(self):
        self._gmms = {}
        self._scale = {}
    
    def get_notebook_code(self, idx):
        op = GaussianMixtureOp()
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
class GaussianMixture2DWorkflowView(WorkflowByView, GaussianMixture2DView):
    op = Instance(IWorkflowOperation, fixed = True)
    subset = DelegatesTo('op')
    by = DelegatesTo('op')
    xchannel = DelegatesTo('op')
    xscale = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    yscale = DelegatesTo('op')

    plot_params = Instance(ScatterplotPlotParams, ())
    
    # AnnotatingView::plot sets 'huefacet' to the newly-created condition. 
    # making 'huefacet' transient prevents this from updating the plot
    # in a loop
    huefacet = Str(transient = True)  
    
    def plot(self, experiment, **kwargs):
        WorkflowByView.plot(self, experiment, **kwargs)
        
        # as noted above, one of the base plot() functions sets huefacet.
        # make sure to reset it after!
        self.huefacet = ""
            
    def get_notebook_code(self, idx):
        view = GaussianMixture2DView()
        view.copy_traits(self, view.copyable_trait_names())
        view.subset = self.subset
        plot_params_str = traits_str(self.plot_params)
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{idx}{plot_params})
        """
        .format(traits = traits_str(view),
                idx = idx,
                plot_params = ", " + plot_params_str if plot_params_str else ""))
        
        
@camel_registry.dumper(GaussianMixture2DWorkflowOp, 'gaussian-2d', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                ychannel = op.ychannel,
                xscale = op.xscale,
                yscale = op.yscale,
                num_components = op.num_components,
                sigma = op.sigma,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('gaussian-2d', version = 1)
def _load(data, version):
    if data['sigma'] == 0:
        data['sigma'] = None
        
    return GaussianMixture2DWorkflowOp(**data)

@camel_registry.dumper(GaussianMixture2DWorkflowView, 'gaussian-2d-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                plot_params = view.plot_params,
                current_plot = view.current_plot)

@camel_registry.dumper(GaussianMixture2DWorkflowView, 'gaussian-2d-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op)

@camel_registry.loader('gaussian-2d-view', version = any)
def _load_view(data, version):
    return GaussianMixture2DWorkflowView(**data)

    