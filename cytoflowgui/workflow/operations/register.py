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
cytoflowgui.workflow.operations.register
----------------------------------------

"""

from traits.api import (HasTraits, provides, Str, observe, Instance,
                        List, Dict, Float, Int, Callable, Property,
                        Union, Enum)

from cytoflow.operations.register import RegistrationOp, RegistrationDiagnosticView
import cytoflow.utility as util

from .. import Changed
from ..views import IWorkflowView, WorkflowView
from ..subset import ISubset
from ..serialization import camel_registry, traits_str, traits_repr, cytoflow_class_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

RegistrationOp.__repr__ = cytoflow_class_repr

class Channel(HasTraits):
    channel = Str
    scale = util.ScaleEnum
    
    def __repr__(self):
        return traits_repr(self)


@provides(IWorkflowOperation)    
class RegistrationWorkflowOp(WorkflowOperation, RegistrationOp):
    # use a list of _Channel instead of separate lists/dicts of channels/scales
    channels_list = List(Channel, estimate = True)
    channels = Property(List(Str), 
                        observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    scale = Property(Dict(Str, util.ScaleEnum),
                     observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    
    # add the 'estimate' metadata
    by = List(Str)
    
    # Smoothing
    
    kernel = Enum('gaussian','tophat','epanechnikov','exponential','linear','cosine', estimate = True)
    bw = Union(Enum('scott', 'silverman'), Float, estimate = True)
    gridsize = Int(200, estimate = True)
    
    # add 'estimate_result' metadata
    _warping = Dict(Str, Callable, transient = True, estimate_result = True)

    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, estimate = True)
    
    # bits for channels
    @observe('[channels_list:items,channels_list:items.channel,channels_list:items.scale]')
    def _channels_updated(self, event):
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
    
    def default_view(self, **kwargs):
        return RegistrationDiagnosticWorkflowView(op = self, **kwargs)
    
    def estimate(self, experiment):
        for i, channel_i in enumerate(self.channels_list):
            for j, channel_j in enumerate(self.channels_list):
                if channel_i.channel == channel_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(channel_i.channel))
                    
        super().estimate(experiment, subset = self.subset)
    
    def should_clear_estimate(self, changed, payload):
        if changed == Changed.ESTIMATE:
            return True
        
        return False
        
    def clear_estimate(self):
        self._scale = {}
        self._groups = []
        self._support = {}
        self._kde = {}
        self._peaks = {}
        self._clusters = {}
        self._means = {}
        self._warping = {}
        
    def get_notebook_code(self, idx):
        op = RegistrationOp()
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
        
        
@provides(IWorkflowView)
class RegistrationDiagnosticWorkflowView(WorkflowView, RegistrationDiagnosticView):
    plot_params = Instance(HasTraits, ())
    
    def should_plot(self, changed, payload):
        if changed == Changed.ESTIMATE_RESULT:
            return True
        
        return False
    
    def get_notebook_code(self, idx):
        view = RegistrationDiagnosticView()
        view.copy_traits(self, view.copyable_trait_names())
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx})
        """
        .format(traits = traits_str(view),
                idx = idx,
                prev_idx = idx - 1))
    

### Serialization
@camel_registry.dumper(RegistrationWorkflowOp, 'registration', version = 1)
def _dump(op):
    return dict(channels_list = op.channels_list,
                by = op.by,
                kernel = op.kernel,
                bw = op.bw,
                gridsize = op.gridsize)

    
@camel_registry.loader('registration', version = 1)
def _load(data, version):
    return RegistrationWorkflowOp(**data)
    
    
@camel_registry.dumper(Channel, 'registration-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                scale = channel.scale)
    
@camel_registry.loader('registration-channel', version = 1)
def _load_channel(data, version):
    return Channel(**data)