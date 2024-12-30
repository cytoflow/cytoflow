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
cytoflowgui.workflow.operations.bleedthrough_linear
---------------------------------------------------

"""

import warnings
from traits.api import (HasTraits, provides, Str, observe, Instance,
                        List, Dict, File, Float, Property, Tuple)

from cytoflow.operations.bleedthrough_linear import BleedthroughLinearOp, BleedthroughLinearDiagnostic
import cytoflow.utility as util

from .. import Changed
from ..views import IWorkflowView, WorkflowView
from ..serialization import camel_registry, traits_str, traits_repr, dedent
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

BleedthroughLinearOp.__repr__ = traits_repr


class Channel(HasTraits):
    channel = Str
    file = File

    def __repr__(self):
        return traits_repr(self)
    

@provides(IWorkflowOperation)
class BleedthroughLinearWorkflowOp(WorkflowOperation, BleedthroughLinearOp):
    # add some metadata
    channels_list = List(Channel, estimate = True)
    spillover = Dict(Tuple(Str, Str), Float, estimate_result = True)
        
    @observe('channels_list:items,channels_list:items.+type', post_init = True)
    def _on_channels_changed(self, _):
        self.changed = 'channels_list'
        
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
        return BleedthroughLinearWorkflowView(op = self, **kwargs)
    
    def estimate(self, experiment):
        for i, channel_i in enumerate(self.channels_list):
            for j, channel_j in enumerate(self.channels_list):
                if channel_i.channel == channel_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(channel_i.channel))
                    
        # check for experiment metadata used to estimate operations in the
        # history, and bail if we find any
        for op in experiment.history:
            if hasattr(op, 'by'):
                for by in op.by:
                    if 'experiment' in experiment.metadata[by]:
                        raise util.CytoflowOpError('experiment',
                                                   "Prior to applying this operation, "
                                                   "you must not apply any operation with 'by' "
                                                   "set to an experimental condition.")
                                               
        self.controls = {}
        for channel in self.channels_list:
            self.controls[channel.channel] = channel.file
            
        if not self.subset:
            warnings.warn("Are you sure you don't want to specify a subset "
                          "used to estimate the model?",
                          util.CytoflowOpWarning)
                    
        return super().estimate(experiment, subset = self.subset)
    
    def apply(self, experiment):
        if not self.spillover:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        return super().apply(experiment)
        
    def should_clear_estimate(self, changed, payload):
        if changed == Changed.ESTIMATE:
            return True
        
        return False
        
    def clear_estimate(self):
        self.spillover = {}
        self._sample.clear()
        
    def get_notebook_code(self, idx):
        op = BleedthroughLinearOp()
        op.copy_traits(self, op.copyable_trait_names())

        for control in self.controls_list:
            op.controls[control.channel] = control.file        

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
class BleedthroughLinearWorkflowView(WorkflowView, BleedthroughLinearDiagnostic):
    plot_params = Instance(HasTraits, ())
        
    def should_plot(self, changed, payload):
        if changed == Changed.ESTIMATE_RESULT:
            return True
        
        return False
    
    def get_notebook_code(self, idx):
        view = BleedthroughLinearDiagnostic()
        view.copy_traits(self, view.copyable_trait_names())
        view.subset = self.subset
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx})
        """
        .format(traits = traits_str(view),
                idx = idx,
                prev_idx = idx - 1))

### Serialization
@camel_registry.dumper(BleedthroughLinearWorkflowOp, 'bleedthrough-linear', version = 1)
def _dump(op):
    return dict(controls_list = op.controls_list,
                subset_list = op.subset_list)
                
@camel_registry.loader('bleedthrough-linear', version = 1)
def _load(data, version):
    return BleedthroughLinearWorkflowOp(**data)

@camel_registry.dumper(Channel, 'bleedthrough-linear-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                file = channel.file)
    
@camel_registry.loader('bleedthrough-linear-channel', version = 1)
def _load_channel(data, version):
    return Channel(**data)

@camel_registry.loader('bleedthrough-linear-control', version = 1)
def _load_control(data, version):
    return Channel(**data)

@camel_registry.dumper(BleedthroughLinearWorkflowView, 'bleedthrough-linear-view', version = 1)
def _dump_view(view):
    return dict(op = view.op)

@camel_registry.loader('bleedthrough-linear-view', version = 1)
def _load_view(data, version):
    return BleedthroughLinearWorkflowView(**data)
                