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
cytoflowgui.workflow.operations.pca
-----------------------------------

"""

import pandas as pd
import numpy as np
from traits.api import (HasTraits, provides, Str, Property, observe, 
                        List, Dict, Any, Bool, Float, Int, Instance,
                        Event)

from cytoflow.operations.flowclean import FlowCleanOp, FlowCleanDiagnostic
from cytoflow.operations.import_op import Tube
import cytoflow.utility as util

from .. import Changed
from ..views import IWorkflowView, WorkflowView
from ..serialization import camel_registry, traits_repr, traits_str, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

FlowCleanOp.__repr__ = traits_repr


class Channel(HasTraits):
    channel = Str
    scale = util.ScaleEnum
    
    def __repr__(self):
        return traits_repr(self)
    
    
@provides(IWorkflowOperation)    
class FlowCleanWorkflowOp(WorkflowOperation, FlowCleanOp):
    # use a list of _Channel instead of separate lists/dicts of channels/scales
    channels_list = List(Channel, estimate = True)
    channels = Property(List(Str), 
                        observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    scale = Property(Dict(Str, util.ScaleEnum),
                     observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    
    # add 'estimate', 'apply' metadata
    name = Str(apply = True)
    time_channel = Str(estimate = True)
    segment_size = Int(500, estimate = True)
    density_cutoff = Float(0.05, estimate = True)
    max_drift = Float(0.15, estimate = True)
    max_mean_drift = Float(0.13, estimate = True)
    max_discontinuity = Float(0.1, estimate = True)
    
    segment_cutoff = Float(0.05, estimate = True)
    
    detect_worst_channels_range = Int(0, estimate = True)
    detect_worst_channels_sd = Int(0, estimate = True)
    measures = List(Str, 
                    value = ["5th percentile", "20th percentile", 
                             "50th percentile", "80th percentile", 
                             "95th percentile", "mean", 
                             "variance", "skewness"],
                    estimate = True)
    force_clean = Bool(False, estimate = True)
    dont_clean = Bool(False, estimate = True)
        
    tube_status = Dict(Tube, Str, estimate_result = True)
    
    # bits for channels
    @observe('[channels_list:items,channels_list:items.channel,channels_list:items.scale]')
    def _channels_updated(self, _):
        self.changed = 'channels_list'
        
    def _get_channels(self):
        return [c.channel for c in self.channels_list]
    
    def _get_scale(self):
        return {c.channel : c.scale for c in self.channels_list}
    
    def estimate(self, experiment):
        for i, channel_i in enumerate(self.channels_list):
            for j, channel_j in enumerate(self.channels_list):
                if channel_i.channel == channel_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(channel_i.channel))
                    
        for channel in self.channels_list:
            if channel.channel == self.time_channel:
                raise util.CytoflowOpError("Channel {} selected as both the time channel "
                                           "and a fluorescence channel"
                                           .format(self.time_channel))
            
        super().estimate(experiment)
        
    def default_view(self, **kwargs):
        return FlowCleanWorkflowView(op = self, **kwargs)
        
    def apply(self, experiment):
        if not self._tube_bins:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        return super().apply(experiment)
        
    def clear_estimate(self):
        self._tube_bins = {}
        self._bin_means = {}
        self._bin_kept = {}
        self._bin_measures = {}
        self._tube_channels = {}
        self._bin_means = {}
        self._density_kde = {}
        self._density_peaks = {}
        self._density_pdf = {}
        self._measures_kde = {}
        self._measures_pdf = {}
        self._measures_peaks = {}    
        self.tube_status = {}
        
    def get_notebook_code(self, idx):
        op = FlowCleanOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
        
        op_{idx}.estimate(ex_{prev_idx})
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        
@provides(IWorkflowView)
class FlowCleanWorkflowView(WorkflowView, FlowCleanDiagnostic):
    plot_params = Instance(HasTraits, ())
    
    # def should_plot(self, changed, payload):
    #     if changed == Changed.ESTIMATE_RESULT:
    #         return True
    #
    #     return False
    
    def plot(self, experiment, **kwargs):
        super().plot(experiment, plot_name = self.current_plot, **kwargs)
    
    def get_notebook_code(self, idx):
        view = FlowCleanDiagnostic()
        view.copy_traits(self, view.copyable_trait_names())
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx}{plot})
        """
        .format(traits = traits_str(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.current_plot else "",
                prev_idx = idx - 1))
        

### Serialization
@camel_registry.dumper(FlowCleanWorkflowOp, 'flowclean', version = 1)
def _dump(op):
    return dict(name = op.name,
                channels_list = op.channels_list,
                time_channel = op.time_channel,
                segment_size = op.segment_size,
                density_cutoff = op.density_cutoff,
                max_drift = op.max_drift,
                max_mean_drift = op.max_mean_drift,
                max_discontinuity = op.max_discontinuity,
                segment_cutoff = op.segment_cutoff,
                detect_worst_channels_range = op.detect_worst_channels_range,
                detect_worst_channels_sd = op.detect_worst_channels_sd,
                measures = op.measures,
                force_clean = op.force_clean,
                dont_clean = op.dont_clean)
    
@camel_registry.loader('pca', version = 1)
def _load(data, version):
    return FlowCleanWorkflowOp(**data)

@camel_registry.dumper(Channel, 'flowclean-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                scale = channel.scale)
    
@camel_registry.loader('flowclean-channel', version = 1)
def _load_channel(data, version):
    return Channel(**data)