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
cytoflowgui.workflow.operations.color_translation
-------------------------------------------------

"""

import warnings
from traits.api import (HasTraits, provides, Str, observe, Event, Bool, Instance,
                        List, Dict, File, Property, Tuple, Constant, Any)

from cytoflow.operations.color_translation import ColorTranslationOp, ColorTranslationDiagnostic
import cytoflow.utility as util

from .. import Changed
from ..views import IWorkflowView, WorkflowView
from ..serialization import camel_registry, traits_str, traits_repr, dedent
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

ColorTranslationOp.__repr__ = traits_repr


class Control(HasTraits):
    from_channel = Str
    to_channel = Str
    file = File
        
    def __repr__(self):
        return traits_repr(self)


@provides(IWorkflowOperation)
class ColorTranslationWorkflowOp(WorkflowOperation, ColorTranslationOp):
    add_control = Event
    remove_control = Event

    # add some metadata
    controls = Dict(Tuple(Str, Str), File, transient = True)
    controls_list = List(Control, estimate = True)
    mixture_model = Bool(False, estimate = True)
    translation = Constant(None)
    
    _coefficients = Dict(Tuple(Str, Str), Any, transient = True, estimate_result = True)
        
    @observe('controls_list:items,controls_list:items.+type', post_init = True)
    def _on_controls_changed(self, _):
        self.changed = 'controls_list'

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
        return ColorTranslationWorkflowView(op = self, **kwargs)
    
    def estimate(self, experiment):
        for i, control_i in enumerate(self.controls_list):
            for j, control_j in enumerate(self.controls_list):
                if control_i.from_channel == control_j.from_channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(control_i.from_channel))
                    
        # check for experiment metadata used to estimate operations in the
        # history, and bail if we find any
        for op in experiment.history[1:]:
            if hasattr(op, 'by'):
                for by in op.by:
                    if 'experiment' in experiment.metadata[by]:
                        raise util.CytoflowOpError('experiment',
                                                   "Prior to applying this operation, "
                                                   "you must not apply any operation with 'by' "
                                                   "set to an experimental condition.")
                                               
        self.controls = {}
        for control in self.controls_list:
            self.controls[(control.from_channel, control.to_channel)] = control.file
            
        if not self.subset:
            warnings.warn("Are you sure you don't want to specify a subset "
                          "used to estimate the model?",
                          util.CytoflowOpWarning)
                   
        super().estimate(experiment, subset = self.subset)
    
    def apply(self, experiment):
        if not self._coefficients:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        return super().apply(experiment)
        
    def should_clear_estimate(self, changed, payload):
        if changed == Changed.ESTIMATE:
            return True
        
        return False
        
    def clear_estimate(self):
        self._coefficients = {}      
        self._trans_fn.clear()
        self._sample.clear()       
        self._means.clear()
        
    def get_notebook_code(self, idx):
        op = ColorTranslationOp()
        op.copy_traits(self, op.copyable_trait_names())

        for control in self.controls_list:
            op.controls[(control.from_channel, control.to_channel)] = control.file        

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
class ColorTranslationWorkflowView(WorkflowView, ColorTranslationDiagnostic):
    plot_params = Instance(HasTraits, ())

    def should_plot(self, changed, payload):
        if changed == Changed.ESTIMATE_RESULT:
            return True
        
        return False
    
    def get_notebook_code(self, idx):
        view = ColorTranslationDiagnostic()
        view.copy_traits(self, view.copyable_trait_names())
        view.subset = self.subset
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx})
        """
        .format(traits = traits_str(view),
                idx = idx,
                prev_idx = idx - 1))
        
        
### Serialization
@camel_registry.dumper(ColorTranslationWorkflowOp, 'color-translation', version = 1)
def _dump(op):
    return dict(controls_list = op.controls_list,
                mixture_model = op.mixture_model,
                subset_list = op.subset_list)
    
@camel_registry.loader('color-translation', version = 1)
def _load(data, version):
    return ColorTranslationWorkflowOp(**data)

@camel_registry.dumper(Control, 'color-translation-control', version = 1)
def _dump_control(c):
    return dict(from_channel = c.from_channel,
                to_channel = c.to_channel,
                file = c.file)
    
@camel_registry.loader('color-translation-control', version = 1)
def _load_control(data, version):
    return Control(**data)

@camel_registry.dumper(ColorTranslationWorkflowView, 'color-translation-view', version = 1)
def _dump_view(view):
    return dict(op = view.op)

@camel_registry.loader('color-translation-view', version = 1)
def _load_view(data, ver):
    return ColorTranslationWorkflowView(**data)


