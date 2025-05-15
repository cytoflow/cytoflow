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
cytoflowgui.workflow.operations.tasbe
-------------------------------------

"""

import warnings
from traits.api import (HasTraits, provides, Str, observe, Instance, Int, Bool,
                        List, File, Float, Property, Constant)

from cytoflow.operations.autofluorescence import AutofluorescenceOp
from cytoflow.operations.bleedthrough_linear import BleedthroughLinearOp
from cytoflow.operations.bead_calibration import BeadCalibrationOp
from cytoflow.operations.color_translation import ColorTranslationOp
import cytoflow.utility as util

from .. import Changed
from ..views import IWorkflowView, WorkflowView
from ..views.view_base import IterWrapper
from ..serialization import camel_registry, cytoflow_class_repr, traits_repr, dedent
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

AutofluorescenceOp.__repr__ = cytoflow_class_repr
BleedthroughLinearOp.__repr__ = cytoflow_class_repr
BeadCalibrationOp.__repr__ = cytoflow_class_repr
ColorTranslationOp.__repr__ = cytoflow_class_repr


class BleedthroughControl(HasTraits):
    channel = Str
    file = File
    
    def __repr__(self):
        return traits_repr(self)
    
    
class TranslationControl(HasTraits):
    from_channel = Str
    to_channel = Str
    file = File
    
    def __repr__(self):
        return traits_repr(self)
    
    
class BeadUnit(HasTraits):
    channel = Str
    unit = Str
    
    def __repr__(self):
        return traits_repr(self)
    
class Progress(object):
    NO_MODEL = "No model estimated"
    
    AUTOFLUORESCENCE = "Estimating autofluorescence"
    
    BLEEDTHROUGH = "Estimating bleedthrough"
    
    BEAD_CALIBRATION = "Estimating bead calibration"
    
    COLOR_TRANSLATION = "Estimating color translation"
    
    VALID = "Valid model estimated!"
    
    
@provides(IWorkflowOperation)
class TasbeWorkflowOp(WorkflowOperation):   
    id = Constant('cytoflowgui.workflow.operations.tasbe')
    friendly_id = Constant("Quantitative Pipeline")
    name = Constant("TASBE")
    
    channels = List(Str, estimate = True)
    
    blank_file = File(filter = ["*.fcs"], estimate = True)
    
    bleedthrough_list = List(BleedthroughControl, estimate = True)

    beads_name = Str(estimate = True)
    beads_file = File(filter = ["*.fcs"], estimate = True)
    beads_unit = Str(estimate = True) # used if do_color_translation is True
    units_list = List(BeadUnit, estimate = True)  # used if do_color_translation is False
    
    bead_peak_quantile = Int(80, estimate = True)
    bead_brightness_threshold = Float(100.0, estimate = True)
    bead_brightness_cutoff = util.FloatOrNone(None, estimate = True)
    
    do_color_translation = Bool(False, estimate = True)
    to_channel = Str(estimate = True)
    translation_list = List(TranslationControl, estimate = True)
    mixture_model = Bool(False, estimate = True)
        
    _af_op = Instance(AutofluorescenceOp, (), transient = True)
    _bleedthrough_op = Instance(BleedthroughLinearOp, (), transient = True)
    _bead_calibration_op = Instance(BeadCalibrationOp, (), transient = True)
    _color_translation_op = Instance(ColorTranslationOp, (), transient = True)
    
    estimate_progress = Str(Progress.NO_MODEL, transient = True, estimate_result = True, status = True)
        
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
    
    @observe('channels.items,to_channel,do_color_translation', post_init = True)
    def _on_channels_changed(self, _):
        
        # bleedthrough
        for channel in self.channels:
            if channel not in [control.channel for control in self.bleedthrough_list]:
                self.bleedthrough_list.append(BleedthroughControl(channel = channel))

        to_remove = []    
        for control in self.bleedthrough_list:
            if control.channel not in self.channels:
                to_remove.append(control)
                
        for control in to_remove:
            self.bleedthrough_list.remove(control)
            
            
        # bead calibration
        for channel in self.channels:                
            if channel not in [unit.channel for unit in self.units_list]:
                self.units_list.append(BeadUnit(channel = channel))

        to_remove = []    
        for unit in self.units_list:
            if unit.channel not in self.channels:
                to_remove.append(unit)
        
        for unit in to_remove:        
            self.units_list.remove(unit)
            
        # color translation
        if self.to_channel not in self.channels:
            self.translation_list = []
            self.to_channel = ''
            return 
        
        for channel in self.channels:
            if channel != self.to_channel:
                if channel not in [control.from_channel for control in self.translation_list]:
                    self.translation_list.append(TranslationControl(from_channel = channel,
                                                                    to_channel = self.to_channel))
                 
        to_remove = []
        for control in self.translation_list:
            if control.from_channel not in self.channels or \
               control.to_channel not in self.channels:
                to_remove.append(control)
                
        for control in to_remove:
            self.translation_list.remove(control)


    @observe('to_channel', post_init = True)
    def _on_to_channel_changed(self, _):
        self.translation_list = []
        if self.to_channel:
            for c in self.channels:
                if c == self.to_channel:
                    continue
                self.translation_list.append(TranslationControl(from_channel = c,
                                                                 to_channel = self.to_channel))
         
    @observe("bleedthrough_list:items:file", post_init = True)
    def _bleedthrough_controls_changed(self, _):
        self.changed = 'bleedthrough_list'
      
    @observe("translation_list:items:file", post_init = True)
    def _translation_controls_changed(self, _):
        self.changed = 'translation_list'
        
    @observe('units_list:items:unit', post_init = True)
    def _on_units_changed(self, _):
        self.changed = 'units_list'
    
    def estimate(self, experiment, subset = None):
        if not self.subset:
            warnings.warn("Are you sure you don't want to specify a subset "
                          "used to estimate the model?",
                          util.CytoflowOpWarning)
            
        if experiment is None:
            raise util.CytoflowOpError("No valid result to estimate with")
        
        # TODO - don't actually need to apply these operations to data in estimate
        experiment = experiment.clone(deep = True)
        
        self.estimate_progress = Progress.AUTOFLUORESCENCE            
        self._af_op.channels = self.channels
        self._af_op.blank_file = self.blank_file
        
        self._af_op.estimate(experiment, subset = self.subset)       
        experiment = self._af_op.apply(experiment)
        
        self.estimate_progress = Progress.BLEEDTHROUGH                   
        self._bleedthrough_op.controls.clear()
        for control in self.bleedthrough_list:
            self._bleedthrough_op.controls[control.channel] = control.file

        self._bleedthrough_op.estimate(experiment, subset = self.subset)
        experiment = self._bleedthrough_op.apply(experiment)

        self.estimate_progress = Progress.BEAD_CALIBRATION                   
        self._bead_calibration_op.beads = BeadCalibrationOp.BEADS[self.beads_name]
        self._bead_calibration_op.beads_file = self.beads_file
        self._bead_calibration_op.bead_peak_quantile = self.bead_peak_quantile
        self._bead_calibration_op.bead_brightness_threshold = self.bead_brightness_threshold
        self._bead_calibration_op.bead_brightness_cutoff = self.bead_brightness_cutoff        
        
        
        if self.do_color_translation:
            # this way matches TASBE better
            self._bead_calibration_op.units.clear()
            self._bead_calibration_op.units[self.to_channel] = self.beads_unit
            self._bead_calibration_op.estimate(experiment)
            experiment = self._bead_calibration_op.apply(experiment)            

            self.estimate_progress = Progress.COLOR_TRANSLATION                    
            self._color_translation_op.mixture_model = self.mixture_model
            
            self._color_translation_op.controls.clear()
            for control in self.translation_list:
                self._color_translation_op.controls[(control.from_channel,
                                                     control.to_channel)] = control.file
                
            self._color_translation_op.estimate(experiment, subset = self.subset)
        
        else:
            self._bead_calibration_op.units.clear()

            for unit in self.units_list:
                self._bead_calibration_op.units[unit.channel] = unit.unit
                
            self._bead_calibration_op.estimate(experiment)
            experiment = self._bead_calibration_op.apply(experiment)      
            
            
        self.estimate_progress = Progress.VALID                                       
        
        
    def should_clear_estimate(self, changed, payload):
        if changed == Changed.ESTIMATE:
            return True
        
        return False
        
        
    def clear_estimate(self):
        self._af_op = AutofluorescenceOp()
        self._bleedthrough_op = BleedthroughLinearOp()
        self._bead_calibration_op = BeadCalibrationOp()
        self._color_translation_op = ColorTranslationOp()  
        self.estimate_progress = Progress.NO_MODEL  
        
    def apply(self, experiment): 
        if self.estimate_progress == Progress.NO_MODEL:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        elif self.estimate_progress != Progress.VALID:
            raise util.CytoflowOpError(None, 'No valid model')
         
        experiment = self._af_op.apply(experiment)
        experiment = self._bleedthrough_op.apply(experiment)
        experiment = self._bead_calibration_op.apply(experiment)
        if self.do_color_translation:
            experiment = self._color_translation_op.apply(experiment)
        
        return experiment
    
    
    def default_view(self, **kwargs):
        return TasbeWorkflowView(op = self, **kwargs)
    
    def get_notebook_code(self, idx):
        self._af_op.channels = self.channels
        self._af_op.blank_file = self.blank_file
        
        self._bleedthrough_op.controls.clear()
        for control in self.bleedthrough_list:
            self._bleedthrough_op.controls[control.channel] = control.file
        
        self._bead_calibration_op.beads = BeadCalibrationOp.BEADS[self.beads_name]
        self._bead_calibration_op.beads_file = self.beads_file
        self._bead_calibration_op.bead_peak_quantile = self.bead_peak_quantile
        self._bead_calibration_op.bead_brightness_threshold = self.bead_brightness_threshold
        self._bead_calibration_op.bead_brightness_cutoff = self.bead_brightness_cutoff        
        
        self._bead_calibration_op.units.clear()
        self._bead_calibration_op.units[self.to_channel] = self.beads_unit
       
        self._color_translation_op.mixture_model = self.mixture_model
        
        self._color_translation_op.controls.clear()
        for control in self.translation_list:
            self._color_translation_op.controls[(control.from_channel,
                                                 control.to_channel)] = control.file      

        return dedent("""
        # the TASBE-style calibration is not a single Cytoflow module.  Instead, it
        # is a specific sequence of four calibrations: autofluorescence correction,
        # bleedthrough, bead calibration and color translation.
        
        # autofluorescence
        op_{idx}_af = {af_repr}
        
        op_{idx}_af.estimate(ex_{prev_idx}{subset})
        ex_{idx}_af = op_{idx}_af.apply(ex_{prev_idx})
        
        # bleedthrough
        op_{idx}_bleedthrough = {bleedthrough_repr}
        
        op_{idx}_bleedthrough.estimate(ex_{idx}_af{subset})
        ex_{idx}_bleedthrough = op_{idx}_bleedthrough.apply(ex_{idx}_af)
        
        # bead calibration
        # beads: {beads}
        op_{idx}_beads = {beads_repr}
        
        op_{idx}_beads.estimate(ex_{idx}_bleedthrough)
        ex_{idx}_beads = op_{idx}_beads.apply(ex_{idx}_bleedthrough)
        
        # color translation
        op_{idx}_color = {color_repr}
        
        op_{idx}_color.estimate(ex_{idx}_beads{subset})
        ex_{idx} = op_{idx}_color.apply(ex_{idx}_beads)
        """
        .format(idx = idx,
                prev_idx = idx - 1,
                af_repr = repr(self._af_op),
                bleedthrough_repr = repr(self._bleedthrough_op),
                color_repr = repr(self._color_translation_op),
                beads = self.beads_name,
                beads_repr = repr(self._bead_calibration_op),
                subset = ", subset = " + repr(self.subset) if self.subset else ""))


@provides(IWorkflowView)
class TasbeWorkflowView(WorkflowView):
    op = Instance(TasbeWorkflowOp)
    plot_params = Instance(HasTraits, ())
    
    id = "cytoflowgui.workflow.operations.tasbeview"
    friendly_id = "TASBE Calibration" 
    
    name = Constant("TASBE Calibration")

    def enum_plots(self, experiment):
        return IterWrapper(iter(["Autofluorescence",
                                 "Bleedthrough",
                                 "Bead Calibration",
                                 "Color Translation"]),
                           [])
        
    def should_plot(self, changed, payload):
        if changed == Changed.RESULT or changed == Changed.PREV_RESULT:
            return False
        
        return True
        
    def plot(self, experiment, **kwargs):
        if experiment is None:
            raise util.CytoflowViewError("No experiment to plot")
                    
        if self.current_plot == "Autofluorescence":
            self.op._af_op.default_view().plot(experiment, **kwargs)
        elif self.current_plot == "Bleedthrough":
            self.op._bleedthrough_op.default_view().plot(experiment, **kwargs)
        elif self.current_plot == "Bead Calibration":
            self.op._bead_calibration_op.default_view().plot(experiment, **kwargs)
        elif self.current_plot == "Color Translation":
            self.op._color_translation_op.default_view().plot(experiment, **kwargs)
            
    def get_notebook_code(self, idx):
        
        return dedent("""
        # Autofluorescence
        op_{idx}_af.default_view().plot(ex_{prev_idx})
        
        # Bleedthrough
        op_{idx}_bleedthrough.default_view().plot(ex_{idx}_af)
        
        # Bead calibration
        op_{idx}_beads.default_view().plot(ex_{idx}_bleedthrough)
        
        # Color translation
        op_{idx}_color.default_view().plot(ex_{idx}_beads)
        """
        .format(idx = idx,
                prev_idx = idx - 1))


### Serialization
@camel_registry.dumper(TasbeWorkflowOp, 'tasbe', version = 1)
def _dump_v1(op):
    return dict(channels = op.channels,
                blank_file = op.blank_file,
                bleedthrough_list = op.bleedthrough_list,
                beads_name = op.beads_name,
                beads_file = op.beads_file,
                beads_unit = op.beads_unit,
                bead_peak_quantile = op.bead_peak_quantile,
                bead_brightness_threshold = op.bead_brightness_threshold,
                bead_brightness_cutoff = op.bead_brightness_cutoff,
                to_channel = op.to_channel,
                mixture_model = op.mixture_model,
                translation_list = op.translation_list,
                subset_list = op.subset_list)

@camel_registry.dumper(TasbeWorkflowOp, 'tasbe', version = 2)
def _dump_v2(op):
    return dict(channels = op.channels,
                blank_file = op.blank_file,
                bleedthrough_list = op.bleedthrough_list,
                beads_name = op.beads_name,
                beads_file = op.beads_file,
                beads_unit = op.beads_unit,
                units_list = op.units_list,
                bead_peak_quantile = op.bead_peak_quantile,
                bead_brightness_threshold = op.bead_brightness_threshold,
                bead_brightness_cutoff = op.bead_brightness_cutoff,
                do_color_translation = op.do_color_translation,
                to_channel = op.to_channel,
                mixture_model = op.mixture_model,
                translation_list = op.translation_list,
                subset_list = op.subset_list)

@camel_registry.loader('tasbe', version = 1)
def _load_v1(data, version):
    # should be fine -- the only change to v2 was the addition of units_list
    # and do_color_translation, both of which have okay defaults
    return TasbeWorkflowOp(**data)
    
@camel_registry.loader('tasbe', version = 2)
def _load_v2(data, version):
    return TasbeWorkflowOp(**data)

@camel_registry.dumper(BleedthroughControl, 'tasbe-bleedthrough-control', version = 1)
def _dump_bleedthrough_control(bl):
    return dict(channel = bl.channel,
                file = bl.file)
    
@camel_registry.loader('tasbe-bleedthrough-control', version = 1)
def _load_bleedthrough_control(data, version):
    return BleedthroughControl(**data)

@camel_registry.dumper(TranslationControl, 'tasbe-translation-control', version = 1)
def _dump_translation_control(tl):
    return dict(from_channel = tl.from_channel,
                to_channel = tl.to_channel,
                file = tl.file)
    
@camel_registry.loader('tasbe-translation-control', version = 1)
def _load_translation_control(data, version):
    return TranslationControl(**data)

@camel_registry.dumper(BeadUnit, 'tasbe-bead-unit', version = 1)
def _dump_bead_unit(bu):
    return dict(channel = bu.channel,
                unit = bu.unit)
    
@camel_registry.loader('tasbe-bead-unit', version = 1)
def _load_bead_unit(data, version):
    return BeadUnit(**data)

@camel_registry.dumper(TasbeWorkflowView, 'tasbe-view', version = 1)
def _dump_view(view):
    return dict(op = view.op)

@camel_registry.loader('tasbe-view', version = 1)
def _load_view(data, version):
    return TasbeWorkflowView(**data)
