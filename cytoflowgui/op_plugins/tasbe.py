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
Created on Oct 9, 2015

@author: brian
'''

import warnings

from traitsui.api import (View, Item, EnumEditor, Controller, VGroup, 
                          CheckListEditor, ButtonEditor, Heading, 
                          HGroup, InstanceEditor)
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, Bool, List, Str, HasTraits,
                        on_trait_change, File, Constant,
                        Property, Instance, Int, Float, Undefined)
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
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.vertical_list_editor import VerticalListEditor
from cytoflowgui.workflow import Changed

class _BleedthroughControl(HasTraits):
    channel = Str
    file = File
    
class _TranslationControl(HasTraits):
    from_channel = Str
    to_channel = Str
    file = File

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
    
    bead_peak_quantile = Int(80, estimate = True)
    bead_brightness_threshold = Float(100, estimate = True)
    bead_brightness_cutoff = Float(Undefined, estimate = True)
    
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
    
    @on_trait_change("subset_list.str", post_init = True)
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('subset_list', self.subset_list))
    
    @on_trait_change('channels[]', post_init = True)
    def _channels_changed(self, obj, name, old, new):
        self.bleedthrough_list = []
        for c in self.channels:
            self.bleedthrough_list.append(_BleedthroughControl(channel = c))
            
        self.changed = (Changed.ESTIMATE, ('bleedthrough_list', self.bleedthrough_list))
            
        self.translation_list = []
        if self.to_channel:
            for c in self.channels:
                if c == self.to_channel:
                    continue
                self.translation_list.append(_TranslationControl(from_channel = c,
                                                                 to_channel = self.to_channel))
        self.changed = (Changed.ESTIMATE, ('translation_list', self.translation_list))


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
        
        experiment = experiment.clone()
        
        self._af_op.channels = self.channels
        self._af_op.blank_file = self.blank_file
        
        self._af_op.estimate(experiment, subset = self.subset)
        self.changed = (Changed.ESTIMATE_RESULT, self)
        experiment = self._af_op.apply(experiment)
        
        self._bleedthrough_op.controls.clear()
        for control in self.bleedthrough_list:
            self._bleedthrough_op.controls[control.channel] = control.file

        self._bleedthrough_op.estimate(experiment, subset = self.subset) 
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
            
        self._bead_calibration_op.estimate(experiment)
        self.changed = (Changed.ESTIMATE_RESULT, self)
        experiment = self._bead_calibration_op.apply(experiment)
        
        self._color_translation_op.mixture_model = self.mixture_model
        
        self._color_translation_op.controls.clear()
        for control in self.translation_list:
            self._color_translation_op.controls[(control.from_channel,
                                                 control.to_channel)] = control.file
                                                 
        self._color_translation_op.estimate(experiment, subset = self.subset)                                         
        
        self.changed = (Changed.ESTIMATE_RESULT, self)
        
        
    def should_clear_estimate(self, changed):
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
    
    _id = "edu.mit.synbio.cytoflowgui.op_plugins.tasbe"
    _friendly_id = "TASBE Calibration" 
    
    name = Constant("TASBE Calibration")
    
    def plot_wi(self, wi):
        self.plot(wi.previous_wi.result, plot_name = wi.current_plot)
        
    def enum_plots(self, experiment):
        return iter(["Autofluorescence",
                     "Bleedthrough",
                     "Bead Calibration",
                     "Color Translation"])
        
    def enum_plots_wi(self, wi):
        return iter(["Autofluorescence",
                     "Bleedthrough",
                     "Bead Calibration",
                     "Color Translation"])
        
    def should_plot(self, changed):
        if changed == Changed.RESULT or changed == Changed.PREV_RESULT:
            return False
        
        return True
        
    def plot(self, experiment, plot_name = None, **kwargs):
        
        if plot_name not in ["Autofluorescence", "Bleedthrough", "Bead Calibration", "Color Translation"]:
            raise util.CytoflowViewError("Which plot do you want?  Must be one "
                                         "of \"Autofluorescence\", "
                                         "\"Bleedthrough\", \"Bead Calibration\", "
                                         "or \"Color Translation\"")
                    
        if experiment is None:
            raise util.CytoflowViewError("No experiment to plot")
        
        new_ex = experiment.clone()
        
        # we don't need to actually apply any ops to data
        new_ex.data = pd.DataFrame(data = {x : pd.Series() for x in new_ex.data})
                    
        if plot_name == "Autofluorescence":
            self.op._af_op.default_view().plot(new_ex, **kwargs)
        else:
            new_ex = self.op._af_op.apply(new_ex)

        if plot_name == "Bleedthrough":
            self.op._bleedthrough_op.default_view().plot(new_ex, **kwargs)
        else:
            new_ex = self.op._bleedthrough_op.apply(new_ex)
            
        if plot_name == "Bead Calibration":
            self.op._bead_calibration_op.default_view().plot(new_ex, **kwargs)
        else:
            new_ex = self.op._bead_calibration_op.apply(new_ex)
            
        if plot_name == "Color Translation":
            self.op._color_translation_op.default_view().plot(new_ex, **kwargs)


@provides(IOperationPlugin)
class TasbePlugin(Plugin):
    """
    class docs
    """
    
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
    