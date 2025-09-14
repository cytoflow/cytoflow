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
cytoflowgui.workflow.operations.som
-----------------------------------

"""

from traits.api import (HasTraits, provides, Str, Property, observe, 
                        List, Dict, Any, Enum, Int, Float, Bool, Instance,
                        Constant)

from cytoflow.operations.som import SOMOp, SOMDiagnosticView
import cytoflow.utility as util

from .. import Changed
from ..views import IWorkflowView, WorkflowByView

from ..serialization import camel_registry, cytoflow_class_repr, traits_repr, dedent, traits_str
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

SOMOp.__repr__ = cytoflow_class_repr

class Channel(HasTraits):
    channel = Str
    scale = util.ScaleEnum
    
    def __repr__(self):
        return traits_repr(self)
    
@provides(IWorkflowView)
class SOMWorkflowView(WorkflowByView, SOMDiagnosticView):
    id = Constant('cytoflowgui.workflow.operations.somworkflowview')

    op = Instance(IWorkflowOperation, fixed = True)
    plot_params = Instance(HasTraits, ())
     
    def should_plot(self, changed, _):
        if changed == Changed.ESTIMATE_RESULT:
            return True
        else:
            return False
            
    def get_notebook_code(self, idx):
        view = SOMDiagnosticView()
        view.copy_traits(self, view.copyable_trait_names())
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx})
        """
        .format(traits = traits_str(view),
                idx = idx,
                prev_idx = idx - 1))
    
@provides(IWorkflowOperation)    
class SOMWorkflowOp(WorkflowOperation, SOMOp):
    # use a list of _Channel instead of separate lists/dicts of channels/scales
    channels_list = List(Channel, estimate = True)
    channels = Property(List(Str), 
                        observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    scale = Property(Dict(Str, util.ScaleEnum),
                     observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    
    # add 'estimate', 'apply' metadata
    name = Str(apply = True)
    by = List(Str, estimate = True)
    # SOM parameters
    width = Int(7, estimate = True)
    height = Int(7, estimate = True)
    distance = Enum("euclidean", "cosine", "chebyshev", "manhattan", estimate = True)
    learning_rate = Float(0.5, estimate = True)
    learning_decay_function = Enum('asymptotic_decay', 'inverse_decay_to_zero', 'linear_decay_to_zero', estimate = True)
    sigma = Float(1.0, estimate = True)
    sigma_decay_function = Enum('asymptotic_decay', 'inverse_decay_to_zero', 'linear_decay_to_zero', estimate = True)
    neighborhood_function = Enum('gaussian', 'mexican_hat', 'bubble', 'triangle', estimate = True)
    num_iterations = Int(50, estimate = True)
    sample = util.UnitFloat(0.05, estimate = True)
    
    # consensus clustering parameters
    consensus_cluster = Bool(True, estimate = True)
    min_clusters = Int(2, estimate = True)
    max_clusters = Int(10, estimate = True)
    n_resamples = Int(100, estimate = True)
    resample_frac = Float(0.8, estimate = True)
    
    # add the 'estimate_result' metadata
    _som = Dict(Any, Instance("cytoflow.utility.minisom.MiniSom"), transient = True, estimate_result = True)
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, estimate = True)
    
    # bits for channels
    @observe('[channels_list:items,channels_list:items.channel,channels_list:items.scale]')
    def _channels_updated(self, _):
        self.changed = 'channels_list'
        
    def _get_channels(self):
        return [c.channel for c in self.channels_list]
    
    def _get_scale(self):
        return {c.channel : c.scale for c in self.channels_list}
    
    # bits to support the subset editor
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    def estimate(self, experiment):
        for i, channel_i in enumerate(self.channels_list):
            for j, channel_j in enumerate(self.channels_list):
                if channel_i.channel == channel_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(channel_i.channel))
        
        super().estimate(experiment, subset = self.subset)
        
    def apply(self, experiment):
        if not self._som:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        
        return super().apply(experiment)
            
    def clear_estimate(self):
        self._som = {}
        self._cc = {}
        self._centers = {}
        
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the k-means clustering.
         
        Returns
        -------
            IView : an IView, call ``SOMWorkflowView.plot`` to see the diagnostic plot.
        """
            
        return SOMWorkflowView(op = self, **kwargs)

    
    def get_notebook_code(self, idx):
        op = SOMOp()
        op.copy_traits(self, op.copyable_trait_names())
        
        op.channels = [c.channel for c in self.channels_list]
        op.scale = {c.channel : c.scale for c in self.channels_list}

        return dedent("""
        op_{idx} = {repr}
        
        op_{idx}.estimate(ex_{prev_idx}{subset})
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1,
                subset = ", subset = " + repr(self.subset) if self.subset else ""))
        

### Serialization
@camel_registry.dumper(SOMWorkflowOp, 'som', version = 1)
def _dump(op):
    return dict(name = op.name,
                channels_list = op.channels_list,
                width = op.width,
                height = op.height,
                distance = op.distance,
                learning_rate = op.learning_rate,
                learning_decay_function = op.learning_decay_function,
                sigma = op.sigma,
                sigma_decay_function = op.sigma_decay_function,
                neighborhood_function = op.neighborhood_function,
                num_iterations = op.num_iterations,
                sample = op.sample,
                consensus_cluster = op.consensus_cluster,
                min_clusters = op.min_clusters,
                max_clusters = op.max_clusters,
                n_resamples = op.n_resamples,
                resample_frac = op.resample_frac,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('som', version = 1)
def _load(data, _):
    return SOMWorkflowOp(**data)

@camel_registry.dumper(SOMWorkflowView, 'som-view', version = 1)
def _dump_view(view):
    return dict(op = view.op,
                current_plot = view.current_plot)

@camel_registry.loader('som-view', version = any)
def _load_view(data, _):
    return SOMWorkflowView(**data)

@camel_registry.dumper(Channel, 'som-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                scale = channel.scale)
    
@camel_registry.loader('som-channel', version = 1)
def _load_channel(data, _):
    return Channel(**data)

