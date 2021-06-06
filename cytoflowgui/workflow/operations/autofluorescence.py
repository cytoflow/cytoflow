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

import warnings 

from traits.api import (HasTraits, provides, Str, Property, observe, Instance,
                        List, Dict, DelegatesTo, File, Float)

from cytoflow.operations.autofluorescence import AutofluorescenceOp, AutofluorescenceDiagnosticView
import cytoflow.utility as util

from .. import Changed
from ..views import IWorkflowView, WorkflowView
from ..serialization import camel_registry, traits_str, traits_repr, dedent
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

AutofluorescenceOp.__repr__ = traits_repr


@provides(IWorkflowOperation)    
class AutofluorescenceWorkflowOp(WorkflowOperation, AutofluorescenceOp):   
    channels = List(Str, estimate = True)
    blank_file = File(filter = ["*.fcs"], estimate = True)
    
    # add the 'estimate_result' metadata
    _af_median = Dict(Str, Float, transient = True, estimate_result = True)

    @observe('channels:items', post_init = True)
    def _on_channels_changed(self):
        self.changed = 'channels'
    
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
        return AutofluorescenceWorkflowView(op = self, **kwargs)
    
    def estimate(self, experiment):
        if not self.subset:
            warnings.warn("Are you sure you don't want to specify a subset "
                          "used to estimate the model?",
                          util.CytoflowOpWarning)
            
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
        
        super().estimate(experiment, subset = self.subset)

    def apply(self, experiment):
        if not self._af_median:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        return super().apply(experiment)

    def clear_estimate(self):
        self._af_median = {}
        self._af_stdev = {}
        self._af_histogram = {}
    
    def should_apply(self, changed, payload):
        if changed == Changed.PREV_RESULT or changed == Changed.ESTIMATE_RESULT:
            return True
        else:
            return False

    def should_clear_estimate(self, changed, payload):
        if changed == Changed.ESTIMATE:
            return True
        else:
            return False
    
    def get_notebook_code(self, idx):
        op = AutofluorescenceOp()
        op.copy_traits(self, op.copyable_trait_names())

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
class AutofluorescenceWorkflowView(WorkflowView, AutofluorescenceDiagnosticView):
    subset = DelegatesTo('op')
    plot_params = Instance(HasTraits, ())

    def should_plot(self, changed, payload):
        if changed == Changed.ESTIMATE_RESULT:
            return True
        else:
            return False
    
    def get_notebook_code(self, idx):
        view = AutofluorescenceDiagnosticView()
        view.copy_traits(self, view.copyable_trait_names())
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx})
        """
        .format(traits = traits_str(view),
                idx = idx,
                prev_idx = idx - 1))
    
        
### Serialization
@camel_registry.dumper(AutofluorescenceWorkflowOp, 'autofluorescence', version = 1)
def _dump(op):
    return dict(blank_file = op.blank_file,
                channels = op.channels,
                subset_list = op.subset_list)
    
@camel_registry.loader('autofluorescence', version = 1)
def _load(data, version):
    return AutofluorescenceWorkflowOp(**data)

@camel_registry.dumper(AutofluorescenceWorkflowView, 'autofluorescence-view', version = 1)
def _dump_view(view):
    return dict(op = view.op)

@camel_registry.loader('autofluorescence-view', version = 1)
def _load_view(data, version):
    return AutofluorescenceWorkflowView(**data)

