#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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

'''
TASBE Calibrated Flow Cytometry
-------------------------------

This module combines all of the other calibrated flow cytometry modules
(autofluorescence, bleedthrough compensation, bead calibration, and channel
translation) into one easy-use-interface.

.. object:: Channels

    Which channels are you calibrating?
    
.. object:: Autofluorescence

    .. object:: Blank File

        The FCS file with the blank (unstained or untransformed) cells, for 
        autofluorescence correction.
        
    .. plot:: 
       :context: close-figs 
    
        import cytoflow as flow
        import_op = flow.ImportOp()
        import_op.tubes = [flow.Tube(file = "tasbe/rby.fcs")]
        ex = import_op.apply()
    
        af_op = flow.AutofluorescenceOp()
        af_op.channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"]
        af_op.blank_file = "tasbe/blank.fcs"
    
        af_op.estimate(ex)
        af_op.default_view().plot(ex) 
        ex2 = af_op.apply(ex)

    
.. object:: Bleedthrough Correction

    A list of single-color controls to use in bleedthrough compensation.  
    There's one entry per channel to compensate.
    
    .. object:: Channel
    
    The channel that this file is the single-color control for.
    
    .. object:: File
    
    The FCS file containing the single-color control data.
    
    .. plot::
       :context: close-figs 
    
        bl_op = flow.BleedthroughLinearOp()
        bl_op.controls = {'Pacific Blue-A' : 'tasbe/ebfp.fcs',
                          'FITC-A' : 'tasbe/eyfp.fcs',
                          'PE-Tx-Red-YG-A' : 'tasbe/mkate.fcs'}    
    
        bl_op.estimate(ex2)
        bl_op.default_view().plot(ex2)  
    
        ex3 = bl_op.apply(ex2)  
    
.. object:: Bead Calibration

    .. object: Beads
    
    The beads that you used for calibration.  Make sure to check the lot
    number as well!
    
    .. object: Beads File
    
    The FCS file containing the bead data.
    
    .. object: Beads Unit
    
    The unit (such as *MEFL*) to calibrate to.
    
    .. object:: Peak Quantile
    
    The minimum quantile required to call a peak in the bead data.  Check
    the diagnostic plot: if you have peaks that aren't getting called, decrease
    this.  If you have "noise" peaks that are getting called incorrectly, 
    increase this.
    
    .. object:: Peak Threshold
    
    The minumum brightness where the module will call a peak.
    
    .. object:: Peak Cutoff
    
    The maximum brightness where the module will call a peak.  Use this to 
    remove peaks that are saturating the detector.
    
    .. plot::
       :context: close-figs 
    
        bead_op = flow.BeadCalibrationOp()
        beads = "Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R"
        bead_op.beads = flow.BeadCalibrationOp.BEADS[beads]
        bead_op.units = {"Pacific Blue-A" : "MEBFP",
                         "FITC-A" : "MEFL",
                         "PE-Tx-Red-YG-A" : "MEPTR"}
        bead_op.beads_file = "tasbe/beads.fcs"
    
        bead_op.estimate(ex2)
        bead_op.default_view().plot(ex2)  
        ex3 = bead_op.apply(ex2) 
    
.. object:: Color Translation

    .. object:: To Channel
    
    Which channel should we rescale all the other channels to?
    
    .. object:: Use mixture model?
    
    If this is set, the module will try to separate the data using a 
    mixture-of-Gaussians, then only compute the translation using the higher
    population.  This is the kind of behavior that you see in a transient
    transfection in mammalian cells, for example.
    
    .. object:: Translation list
    
    Each pair of channels must have a multi-color control from which to
    compute the scaling factor.

    .. plot::
       :context: close-figs 
    
        color_op = flow.ColorTranslationOp()
        color_op.controls = {("Pacific Blue-A", "FITC-A") : "tasbe/rby.fcs",
                             ("PE-Tx-Red-YG-A", "FITC-A") : "tasbe/rby.fcs"}
        color_op.mixture_model = True
    
        color_op.estimate(ex3)
        color_op.default_view().plot(ex3)  
        ex4 = color_op.apply(ex3)  
'''

import warnings

from traitsui.api import (View, Item, EnumEditor, Controller, VGroup, 
                          CheckListEditor, ButtonEditor, 
                          HGroup, InstanceEditor)
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, Bool, List, Str, HasTraits,
                        on_trait_change, File, Constant,
                        Property, Instance, CInt, CFloat)
from pyface.api import ImageResource

import pandas as pd

import cytoflow.utility as util

from cytoflow.operations import IOperation
from cytoflow.operations.autofluorescence import AutofluorescenceOp
from cytoflow.operations.bleedthrough_linear import BleedthroughLinearOp
from cytoflow.operations.bead_calibration import BeadCalibrationOp
from cytoflow.operations.color_translation import ColorTranslationOp
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.vertical_list_editor import VerticalListEditor
from cytoflowgui.workflow import Changed
from cytoflowgui.serialization import camel_registry, traits_repr, dedent

AutofluorescenceOp.__repr__ = traits_repr
BleedthroughLinearOp.__repr__ = traits_repr
BeadCalibrationOp.__repr__ = traits_repr
ColorTranslationOp.__repr__ = traits_repr

class _BleedthroughControl(HasTraits):
    channel = Str
    file = File
    
    def __repr__(self):
        return traits_repr(self)

    
    
class _TranslationControl(HasTraits):
    from_channel = Str
    to_channel = Str
    file = File
    
    def __repr__(self):
        return traits_repr(self)


class TasbeHandler(OpHandlerMixin, Controller):
                
    beads_name_choices = Property(transient = True)
    beads_units = Property(depends_on = 'model.beads_name',
                           transient = True)
    
    def _get_beads_name_choices(self):
        return list(BeadCalibrationOp.BEADS.keys())
    
    def _get_beads_units(self):
        if self.model.beads_name:
            return list(BeadCalibrationOp.BEADS[self.model.beads_name].keys())
        else:
            return []
        
    def bleedthrough_traits_view(self):
        return View(HGroup(Item('channel', style = 'readonly'),
                           Item('file', show_label = False),
                           show_labels = False),
                    handler = self)
        
    def translation_traits_view(self):
        return View(HGroup(Item('from_channel', style = 'readonly', show_label = False),
                           Item('', label = '->'),
                           Item('to_channel', style = 'readonly', show_label = False),
                           Item('file', show_label = False)),
                    handler = self)
    
    def default_traits_view(self):
        return View(Item("channels",
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context.previous_wi.channels'),
                         style = 'custom'),
                    VGroup(
                        Item('blank_file'),
                        label = "Autofluorescence"),
                    VGroup(
                        Item('bleedthrough_list',
                                editor = VerticalListEditor(editor = InstanceEditor(view = self.bleedthrough_traits_view()),
                                                            style = 'custom',
                                                            mutable = False),
                                style = 'custom'),
                        label = "Bleedthrough Correction",
                        show_border = False,
                        show_labels = False),
                    VGroup(
                        Item('beads_name',
                             editor = EnumEditor(name = 'handler.beads_name_choices'),
                             label = "Beads",
                             width = -125),
                        Item('beads_file'),
                        Item('beads_unit', 
                             editor = EnumEditor(name = 'handler.beads_units')),
                        Item('bead_peak_quantile',
                             label = "Peak\nQuantile"),
                        Item('bead_brightness_threshold',
                             label = "Peak\nThreshold "),
                        Item('bead_brightness_cutoff',
                             label = "Peak\nCutoff"),
                        label = "Bead Calibration",
                        show_border = False),
                    VGroup(
                        Item('to_channel',
                             editor = EnumEditor(name = 'channels')),
                        Item('mixture_model',
                             label = "Use mixture\nmodel?"),
                           label = "Color Translation"),
                    VGroup(
                        Item('translation_list',
                                editor = VerticalListEditor(editor = InstanceEditor(view = self.translation_traits_view()),
                                                            style = 'custom',
                                                            mutable = False),
                                style = 'custom'),

                        show_labels = False),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous_wi.conditions",
                                                      metadata = "context.previous_wi.metadata",
                                                      when = "'experiment' not in vars() or not experiment")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    shared_op_traits)

@provides(IOperation)
class TasbePluginOp(PluginOpMixin):
    handler_factory = Callable(TasbeHandler)
    
    id = Constant('edu.mit.synbio.cytoflowgui.op_plugins.bleedthrough_piecewise')
    friendly_id = Constant("Quantitative Pipeline")
    name = Constant("TASBE")
    
    channels = List(Str, estimate = True)
    
    blank_file = File(filter = ["*.fcs"], estimate = True)
    
    bleedthrough_list = List(_BleedthroughControl, estimate = True)

    beads_name = Str(estimate = True)
    beads_file = File(filter = ["*.fcs"], estimate = True)
    beads_unit = Str(estimate = True)
    
    bead_peak_quantile = CInt(80, estimate = True)
    bead_brightness_threshold = CFloat(100.0, estimate = True)
    bead_brightness_cutoff = util.CFloatOrNone(None, estimate = True)
    
    to_channel = Str(estimate = True)
    translation_list = List(_TranslationControl, estimate = True)
    mixture_model = Bool(False, estimate = True)
        
    _af_op = Instance(AutofluorescenceOp, (), transient = True)
    _bleedthrough_op = Instance(BleedthroughLinearOp, (), transient = True)
    _bead_calibration_op = Instance(BeadCalibrationOp, (), transient = True)
    _color_translation_op = Instance(ColorTranslationOp, (), transient = True)
    
    subset_list = List(ISubset, estimate = True)    
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change("subset_list.str")
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('subset_list', self.subset_list))
    
    @on_trait_change('channels[]', post_init = True)
    def _channels_changed(self, obj, name, old, new):
        for channel in self.channels:
            if channel not in [control.channel for control in self.bleedthrough_list]:
                self.bleedthrough_list.append(_BleedthroughControl(channel = channel))

        to_remove = []    
        for control in self.bleedthrough_list:
            if control.channel not in self.channels:
                to_remove.append(control)
                
        for control in to_remove:
            self.bleedthrough_list.remove(control)
             
        for c in self.channels:
            if c == self.to_channel:
                continue
            if channel not in [control.from_channel for control in self.translation_list]:
                self.translation_list.append(_TranslationControl(from_channel = c,
                                                                 to_channel = self.to_channel))
            
        to_remove = []
        for control in self.translation_list:
            if control.from_channel not in self.channels:
                to_remove.append(control)
                
        for control in to_remove:
            self.translation_list.remove(control)
            
        self.changed = (Changed.ESTIMATE, ('translation_list', self.translation_list))
        self.changed = (Changed.ESTIMATE, ('bleedthrough_list', self.bleedthrough_list))            


    @on_trait_change('to_channel', post_init = True)
    def _to_channel_changed(self, obj, name, old, new):
        self.translation_list = []
        if self.to_channel:
            for c in self.channels:
                if c == self.to_channel:
                    continue
                self.translation_list.append(_TranslationControl(from_channel = c,
                                                                 to_channel = self.to_channel))
        self.changed = (Changed.ESTIMATE, ('translation_list', self.translation_list))
         
    @on_trait_change("bleedthrough_list_items, bleedthrough_list.+", post_init = True)
    def _bleedthrough_controls_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('bleedthrough_list', self.bleedthrough_list))
     
    @on_trait_change("translation_list_items, translation_list.+", post_init = True)
    def _translation_controls_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('translation_list', self.translation_list))
    
    def estimate(self, experiment, subset = None):
        if not self.subset:
            warnings.warn("Are you sure you don't want to specify a subset "
                          "used to estimate the model?",
                          util.CytoflowOpWarning)
            
        if experiment is None:
            raise util.CytoflowOpError("No valid result to estimate with")
        
        # TODO - don't actually need to apply these operations to data in estimate
        experiment = experiment.clone()
        
        self._af_op.channels = self.channels
        self._af_op.blank_file = self.blank_file
        
        try:
            self._af_op.estimate(experiment, subset = self.subset)
        except:
            raise
        finally:
            self.changed = (Changed.ESTIMATE_RESULT, self)
            
        experiment = self._af_op.apply(experiment)
        
        self._bleedthrough_op.controls.clear()
        for control in self.bleedthrough_list:
            self._bleedthrough_op.controls[control.channel] = control.file

        try:
            self._bleedthrough_op.estimate(experiment, subset = self.subset)
        except:
            raise
        finally:
            self.changed = (Changed.ESTIMATE_RESULT, self)
            
        experiment = self._bleedthrough_op.apply(experiment)
        
        self._bead_calibration_op.beads = BeadCalibrationOp.BEADS[self.beads_name]
        self._bead_calibration_op.beads_file = self.beads_file
        self._bead_calibration_op.bead_peak_quantile = self.bead_peak_quantile
        self._bead_calibration_op.bead_brightness_threshold = self.bead_brightness_threshold
        self._bead_calibration_op.bead_brightness_cutoff = self.bead_brightness_cutoff        
        
        self._bead_calibration_op.units.clear()
        
        # this is the old way
#         for channel in self.channels:
#             self._bead_calibration_op.units[channel] = self.beads_unit

        # this way matches TASBE better
        self._bead_calibration_op.units[self.to_channel] = self.beads_unit
            
        try:
            self._bead_calibration_op.estimate(experiment)
        except:
            raise
        finally:
            self.changed = (Changed.ESTIMATE_RESULT, self)
            
        experiment = self._bead_calibration_op.apply(experiment)
        
        self._color_translation_op.mixture_model = self.mixture_model
        
        self._color_translation_op.controls.clear()
        for control in self.translation_list:
            self._color_translation_op.controls[(control.from_channel,
                                                 control.to_channel)] = control.file
            
        try:                                     
            self._color_translation_op.estimate(experiment, subset = self.subset)
        except:
            raise
        finally:                                         
            self.changed = (Changed.ESTIMATE_RESULT, self)
        
        
    def should_clear_estimate(self, changed, payload):
        if changed == Changed.ESTIMATE:
            return True
        
        return False
        
        
    def clear_estimate(self):
        self._af_op = AutofluorescenceOp()
        self._bleedthrough_op = BleedthroughLinearOp()
        self._bead_calibration_op = BeadCalibrationOp()
        self._color_translation_op = ColorTranslationOp()
        
        self.changed = (Changed.ESTIMATE_RESULT, self)
        
        
    def apply(self, experiment):
        
        if experiment is None:
            raise util.CytoflowOpError("No experiment was specified")
        
        experiment = self._af_op.apply(experiment)
        experiment = self._bleedthrough_op.apply(experiment)
        experiment = self._bead_calibration_op.apply(experiment)
        experiment = self._color_translation_op.apply(experiment)
        
        return experiment
    
    
    def default_view(self, **kwargs):
        return TasbePluginView(op = self, **kwargs)
    
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

class TasbeViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(Item('context.view_warning',
                         resizable = True,
                         visible_when = 'context.view_warning',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                 background_color = "#ffff99")),
                    Item('context.view_error',
                         resizable = True,
                         visible_when = 'context.view_error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191")))

@provides(IView)
class TasbePluginView(PluginViewMixin):
    handler_factory = Callable(TasbeViewHandler)
    op = Instance(TasbePluginOp)
    
    id = "edu.mit.synbio.cytoflowgui.op_plugins.tasbe"
    friendly_id = "TASBE Calibration" 
    
    name = Constant("TASBE Calibration")
    
    def plot_wi(self, wi):
        self.plot(wi.previous_wi.result, plot_name = self.current_plot)
        
        
    def enum_plots_wi(self, wi):
        return iter(["Autofluorescence",
                     "Bleedthrough",
                     "Bead Calibration",
                     "Color Translation"])
        
    def should_plot(self, changed, payload):
        if changed == Changed.RESULT or changed == Changed.PREV_RESULT:
            return False
        
        return True
        
    def plot(self, experiment, plot_name = None, **kwargs):

        if experiment is None:
            raise util.CytoflowViewError("No experiment to plot")
                    
        if plot_name == "Autofluorescence":
            self.op._af_op.default_view().plot(experiment, **kwargs)
        elif plot_name == "Bleedthrough":
            self.op._bleedthrough_op.default_view().plot(experiment, **kwargs)
            return
        elif plot_name == "Bead Calibration":
            self.op._bead_calibration_op.default_view().plot(experiment, **kwargs)
        elif plot_name == "Color Translation":
            self.op._color_translation_op.default_view().plot(experiment, **kwargs)
        else:
            raise util.CytoflowViewError("Which plot do you want?  Must be one "
                                         "of \"Autofluorescence\", "
                                         "\"Bleedthrough\", \"Bead Calibration\", "
                                         "or \"Color Translation\"")
            
            
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


@provides(IOperationPlugin)
class TasbePlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.op_plugins.tasbe'
    operation_id = 'edu.mit.synbio.cytoflowgui.op_plugins.tasbe'

    short_name = "TASBE Calibration"
    menu_group = "Gates"
    
    def get_operation(self):
        return TasbePluginOp()
    
    def get_icon(self):
        return ImageResource('tasbe')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
### Serialization
@camel_registry.dumper(TasbePluginOp, 'tasbe', version = 1)
def _dump(op):
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
    
@camel_registry.loader('tasbe', version = 1)
def _load(data, version):
    return TasbePluginOp(**data)

@camel_registry.dumper(_BleedthroughControl, 'tasbe-bleedthrough-control', version = 1)
def _dump_bleedthrough_control(bl):
    return dict(channel = bl.channel,
                file = bl.file)
    
@camel_registry.loader('tasbe-bleedthrough-control', version = 1)
def _load_bleedthrough_control(data, version):
    return _BleedthroughControl(**data)

@camel_registry.dumper(_TranslationControl, 'tasbe-translation-control', version = 1)
def _dump_translation_control(tl):
    return dict(from_channel = tl.from_channel,
                to_channel = tl.to_channel,
                file = tl.file)
    
@camel_registry.loader('tasbe-translation-control', version = 1)
def _load_translation_control(data, version):
    return _TranslationControl(**data)

@camel_registry.dumper(TasbePluginView, 'tasbe-view', version = 1)
def _dump_view(view):
    return dict(op = view.op)

@camel_registry.loader('tasbe-view', version = 1)
def _load_view(data, version):
    return TasbePluginView(**data)