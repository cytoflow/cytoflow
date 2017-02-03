#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

import matplotlib.pyplot as plt

from traitsui.api import (View, Item, EnumEditor, Controller, VGroup, 
                          CheckListEditor, ButtonEditor, Heading, 
                          HGroup, ListEditor, InstanceEditor)
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, Bool, List, Str, HasTraits,
                        on_trait_change, File, Constant,
                        Property, Instance, Int, Float, Undefined)
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations import IOperation
from cytoflow.operations.autofluorescence import AutofluorescenceOp
from cytoflow.operations.bleedthrough_piecewise import BleedthroughPiecewiseOp
from cytoflow.operations.bead_calibration import BeadCalibrationOp
from cytoflow.operations.color_translation import ColorTranslationOp
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.workflow_item import WorkflowItem

class _BleedthroughControl(HasTraits):
    channel = Str
    file = File
    
class _TranslationControl(HasTraits):
    from_channel = Str
    to_channel = Str
    file = File

class TasbeHandler(Controller, OpHandlerMixin):
                
    beads_name_choices = Property(transient = True)
    beads_units = Property(depends_on = 'model.beads_name',
                           transient = True)
    
    wi = Instance(WorkflowItem)
    
    def init_info(self, info):
        # this is ugly, but it works.
        if not self.wi:
            self.wi = info.ui.context['context']
    
    def _get_beads_name_choices(self):
        return BeadCalibrationOp.BEADS.keys()
    
    def _get_beads_units(self):
        if self.model.beads_name:
            return BeadCalibrationOp.BEADS[self.model.beads_name].keys()
        else:
            return []
        
    def bleedthrough_traits_view(self):
        return View(HGroup(Item('channel', style = 'readonly'),
                           Item('file', show_label = False)),
                    handler = self)
        
    def translation_traits_view(self):
        return View(HGroup(Item('from_channel', style = 'readonly'),
                           Item('to_channel', style = 'readonly'),
                           Item('file', show_label = False)),
                    handler = self)
    
    def default_traits_view(self):
        return View(Item("channels",
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context.previous.channels'),
                         style = 'custom'),
                    VGroup(
                        Item('blank_file'),
                        label = "Autofluorescence"),
                    VGroup(
                        Item('bleedthrough_list',
                                editor = ListEditor(editor = InstanceEditor(view = self.bleedthrough_traits_view()),
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
                             editor = EnumEditor(name = 'object.channels')),
                        Item('mixture_model',
                             label = "Use mixture\nmodel?"),
                           label = "Color Translation"),
                    VGroup(
                        Item('translation_list',
                                editor = ListEditor(editor = InstanceEditor(view = self.translation_traits_view()),
                                                    style = 'custom',
                                                    mutable = False),
                                style = 'custom'),

                        show_labels = False),
                    VGroup(Item('subset_dict',
                                show_label = False,
                                editor = SubsetEditor(conditions = "context.previous.conditions",
                                                      metadata = "context.previous.metadata",
                                                      when = "'experiment' not in vars() or not experiment")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Heading("WARNING: Very slow!"),
                    Heading("Give it a few minutes..."),
                    Item('context.do_estimate',
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
    _bleedthrough_op = Instance(BleedthroughPiecewiseOp, (), transient = True)
    _bead_calibration_op = Instance(BeadCalibrationOp, (), transient = True)
    _color_translation_op = Instance(ColorTranslationOp, (), transient = True)
    
    @on_trait_change('channels[]', post_init = True)
    def _channels_changed(self, obj, name, old, new):
        self.bleedthrough_list = []
        for c in self.channels:
            self.bleedthrough_list.append(_BleedthroughControl(channel = c))
            
        self.translation_list = []
        if self.to_channel:
            for c in self.channels:
                if c == self.to_channel:
                    continue
                self.translation_list.append(_TranslationControl(from_channel = c,
                                                                 to_channel = self.to_channel))
        self.changed = "estimate"


    @on_trait_change('to_channel', post_init = True)
    def _to_channel_changed(self, obj, name, old, new):
        self.translation_list = []
        if self.to_channel:
            for c in self.channels:
                if c == self.to_channel:
                    continue
                self.translation_list.append(_TranslationControl(from_channel = c,
                                                                 to_channel = self.to_channel))


    
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
        self.changed = "estimate_result"
        experiment = self._af_op.apply(experiment)
        
        self._bleedthrough_op.controls.clear()
        for control in self.bleedthrough_list:
            self._bleedthrough_op.controls[control.channel] = control.file

        self._bleedthrough_op.estimate(experiment, subset = self.subset) 
        self.changed = "estimate_result"
        experiment = self._bleedthrough_op.apply(experiment)
        
        self._bead_calibration_op.beads = BeadCalibrationOp.BEADS[self.beads_name]
        self._bead_calibration_op.beads_file = self.beads_file
        self._bead_calibration_op.bead_peak_quantile = self.bead_peak_quantile
        self._bead_calibration_op.bead_brightness_threshold = self.bead_brightness_threshold
        self._bead_calibration_op.bead_brightness_cutoff = self.bead_brightness_cutoff        
        
        self._bead_calibration_op.units.clear()
        for channel in self.channels:
            self._bead_calibration_op.units[channel] = self.beads_unit
            
        self._bead_calibration_op.estimate(experiment)
        self.changed = "estimate_result"
        experiment = self._bead_calibration_op.apply(experiment)
        
        self._color_translation_op.mixture_model = self.mixture_model
        
        self._color_translation_op.controls.clear()
        for control in self.translation_list:
            self._color_translation_op.controls[(control.from_channel,
                                                 control.to_channel)] = control.file
                                                 
        self._color_translation_op.estimate(experiment, subset = self.subset)                                         
        
        self.changed = "estimate_result"
        
        
    def should_clear_estimate(self, changed):
        """
        Should the owning WorkflowItem clear the estimated model by calling
        op.clear_estimate()?  `changed` can be:
         - "estimate" -- the parameters required to call 'estimate()' (ie
            traits with estimate = True metadata) have changed
         - "prev_result" -- the previous WorkflowItem's result changed
        """
        if changed == "prev_result":
            return False
        
        return True
        
        
    def clear_estimate(self):
        self._af_op = AutofluorescenceOp()
        self._bleedthrough_op = BleedthroughPiecewiseOp()
        self._bead_calibration_op = BeadCalibrationOp()
        self._color_translation_op = ColorTranslationOp()
        
        self.changed = "estimate_result"
        
        
    def apply(self, experiment):
        
        experiment = self._af_op.apply(experiment)
        experiment = self._bleedthrough_op.apply(experiment)
        experiment = self._bead_calibration_op.apply(experiment)
        experiment = self._color_translation_op.apply(experiment)
        
        return experiment
    
    
    def default_view(self, **kwargs):
        return TasbePluginView(op = self, **kwargs)

class TasbeViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         style = 'readonly'),
                    Item('context.view_warning',
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
        self.plot(wi.previous.result, plot_name = wi.current_plot)
        
    def enum_plots(self, experiment):
        return iter(["Autofluorescence",
                     "Bleedthrough",
                     "Bead Calibration",
                     "Color Translation"])
        
    def enum_plots_wi(self, wi):
        if wi.previous and wi.previous.result:
            return self.enum_plots(wi.previous.result)
        else:
            return []
        
        
    def should_plot(self, changed):
        """
        Should the owning WorkflowItem refresh the plot when certain things
        change?  `changed` can be:
         - "view" -- the view's parameters changed
         - "result" -- this WorkflowItem's result changed
         - "prev_result" -- the previous WorkflowItem's result changed
         - "estimate_result" -- the results of calling "estimate" changed
        """
        if changed == "result" or changed == "prev_result":
            return False
        
        return True
        
    def plot(self, experiment, plot_name = None, **kwargs):
        
        if not plot_name:
            for plot in self.enum_plots(experiment):
                self.plot(experiment, plot_name = plot, **kwargs)
                plt.title(plot)
        elif plot_name == "Autofluorescence":
            self.op._af_op.default_view().plot(experiment, **kwargs)
        elif plot_name == "Bleedthrough":
            self.op._bleedthrough_op.default_view().plot(experiment, **kwargs)
        elif plot_name == "Bead Calibration":
            self.op._bead_calibration_op.default_view().plot(experiment, **kwargs)
        elif plot_name == "Color Translation":
            self.op._color_translation_op.default_view().plot(experiment, **kwargs)
        else:
            raise util.CytoflowViewError("Couldn't find plot \"{}\""
                                         .format(plot_name))


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
    