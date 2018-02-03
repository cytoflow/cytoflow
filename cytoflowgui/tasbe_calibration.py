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

.. object:: Files

    Choose the files to calibrate
    
.. object:: X Morpho Channel

    The X channel to select morphology
    
.. object:: X Morpho Scale

    How to scale the X morpho channel?
    
.. object:: Y Morpho Channel

    The Y channel to select morphology
    
.. object:: Y Morpho Scale

    How to scale the Y morpho channel?

.. object:: Fluorescence channels

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

.. object:: Export
    
    Choose a directory to export to
    
.. object:: Quit

    Return to the main Cytoflow interface
'''

import warnings
from pathlib import Path

import fcsparser

from traitsui.api import (View, Item, EnumEditor, Controller, VGroup, 
                          CheckListEditor, ButtonEditor, 
                          HGroup, InstanceEditor)
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, Bool, List, Str, HasTraits,
                        on_trait_change, File, Constant, Directory,
                        Property, Instance, Int, Float, Undefined, Event,
                        DelegatesTo)
from pyface.api import ImageResource

import pandas as pd

from pyface.api import FileDialog, ImageResource, AboutDialog, information, error, confirm, OK, YES

import cytoflow.utility as util

from cytoflow.operations import IOperation
from cytoflow import (Experiment, ImportOp, Tube, AutofluorescenceOp, 
                      BleedthroughLinearOp, BeadCalibrationOp, 
                      ColorTranslationOp, PolygonOp, ExportFCS)
from cytoflow.operations.polygon import PolygonSelection

from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.vertical_list_editor import VerticalListEditor
from cytoflowgui.toggle_button import ToggleButtonEditor
from cytoflowgui.workflow import Changed

class _BleedthroughControl(HasTraits):
    channel = Str
    file = File
    
class _TranslationControl(HasTraits):
    from_channel = Str
    to_channel = Str
    file = File
    
class _Unit(HasTraits):
    channel = Str
    unit = Str

class TasbeHandler(OpHandlerMixin, Controller):
                
    beads_name_choices = Property(transient = True)
    beads_units = Property(depends_on = 'model.beads_name',
                           transient = True)
    do_convert = Event
    
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
        
        
    def unit_traits_view(self):
        return View(HGroup(Item('channel', style = 'readonly', show_label = False),
                           Item('unit',
                                editor = EnumEditor(name = 'handler.beads_units'),
                                show_label = False)),
                    handler = self)
    
        
    def translation_traits_view(self):
        return View(HGroup(Item('from_channel', style = 'readonly', show_label = False),
                           Item('', label = '->'),
                           Item('to_channel', style = 'readonly', show_label = False),
                           Item('file', show_label = False)),
                    handler = self)
    
    def default_traits_view(self):
        return View(
                    VGroup(
                        Item('blank_file'),
                        label = "Autofluorescence"),
                    VGroup(
                        Item('fsc_channel',
                             editor = EnumEditor(name = '_blank_exp_channels'),
                             label = "Forward Scatter Channel"),
                        Item('ssc_channel',
                             editor = EnumEditor(name = '_blank_exp_channels'),
                             label = "Side Scatter Channel"),
                        label = "Morphology"),
                    VGroup(
                        Item("channels",
                             editor = CheckListEditor(cols = 2,
                                                      name = '_blank_exp_channels'),
                             style = 'custom'),
                        label = "Channels To Calibrate",
                        show_labels = False),
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
                        Item('units_list',
                                editor = VerticalListEditor(editor = InstanceEditor(view = self.unit_traits_view()),
                                                            style = 'custom',
                                                            mutable = False),
                                style = 'custom',
                                label = "Bead\nunits"),
                        Item('bead_peak_quantile',
                             label = "Peak\nQuantile"),
                        Item('bead_brightness_threshold',
                             label = "Peak\nThreshold "),
                        Item('bead_brightness_cutoff',
                             label = "Peak\nCutoff"),
                        label = "Bead Calibration",
                        show_border = False),
                    VGroup(
                        Item('do_color_translation',
                             label = "Do color translation?",
                             editor = ToggleButtonEditor(),
                             show_label = False),
                        Item('to_channel',
                             editor = EnumEditor(name = 'channels'),
                             visible_when = 'do_color_translation == True'),
                        Item('mixture_model',
                             label = "Use mixture\nmodel?",
                             visible_when = 'do_color_translation == True'),
                        VGroup(
                            Item('translation_list',
                                 editor = VerticalListEditor(editor = InstanceEditor(view = self.translation_traits_view()),
                                                             style = 'custom',
                                                             mutable = False),
                               style = 'custom'),
                               show_labels = False,
                               visible_when = 'do_color_translation == True'),
                        label = "Color Translation",
                        show_border = False),
                    VGroup(
                        Item('status',
                             style = 'readonly'),
                        Item('output_directory'),
                        Item('do_estimate',
                             editor = ButtonEditor(value = True,
                                                   label = "Estimate parameters"),
                             show_label = False),
                        Item('handler.do_convert',
                             editor = ButtonEditor(value = True,
                                                   label = "Convert files..."),
                             enabled_when = "valid_model == True",
                             show_label = False),
                        label = "Output",
                        show_border = False),
                    Item('do_exit',
                         editor = ButtonEditor(value = True,
                                               label = "Return to Cytoflow"),
                         show_label = False),
                    shared_op_traits)
        
    
    def _do_convert_fired(self):
        
        dialog = FileDialog(action = 'open files',
                            wildcard = (FileDialog.create_wildcard("FCS files", "*.fcs"))) #@UndefinedVariable  
        if dialog.open() == OK:            
            self.model.input_files = dialog.paths


@provides(IOperation)
class TasbeCalibrationOp(PluginOpMixin):
    handler_factory = Callable(TasbeHandler)
    
    id = Constant('edu.mit.synbio.cytoflowgui.op_plugins.bleedthrough_piecewise')
    friendly_id = Constant("Quantitative Pipeline")
    name = Constant("TASBE")
    
    fsc_channel = DelegatesTo('_polygon_op', 'xchannel', estimate = True)
    ssc_channel = DelegatesTo('_polygon_op', 'ychannel', estimate = True)
    vertices = DelegatesTo('_polygon_op', 'vertices', estimate = True)
    channels = List(Str, estimate = True)
    
    blank_file = File(filter = ["*.fcs"], estimate = True)
    
    bleedthrough_list = List(_BleedthroughControl, estimate = True)

    beads_name = Str(estimate = True)
    beads_file = File(filter = ["*.fcs"], estimate = True)
    units_list = List(_Unit, estimate = True)
    
    bead_peak_quantile = Int(80, estimate = True)
    bead_brightness_threshold = Float(100, estimate = True)
    bead_brightness_cutoff = Float(Undefined, estimate = True)
    
    do_color_translation = Bool(estimate = True)
    to_channel = Str(estimate = True)
    translation_list = List(_TranslationControl, estimate = True)
    mixture_model = Bool(False, estimate = True)
    
    do_estimate = Event
    valid_model = Bool(False, status = True)
    do_exit = Event
    input_files = List(File)
    output_directory = Directory
        
    _blank_exp_file = File(transient = True)
    _blank_exp = Instance(Experiment, transient = True)
    _blank_exp_file = File(transient = True)
    _blank_exp_channels = List(Str, status = True)
    _polygon_op = Instance(PolygonOp, 
                           kw = {'name' : 'polygon',
                                 'xscale' : 'log', 
                                 'yscale' : 'log'}, 
                           transient = True)
    _af_op = Instance(AutofluorescenceOp, (), transient = True)
    _bleedthrough_op = Instance(BleedthroughLinearOp, (), transient = True)
    _bead_calibration_op = Instance(BeadCalibrationOp, (), transient = True)
    _color_translation_op = Instance(ColorTranslationOp, (), transient = True)
    
    status = Str(status = True)
    
    @on_trait_change('channels[], to_channel, do_color_translation', post_init = True)
    def _channels_changed(self, obj, name, old, new):
        for channel in self.channels:
            if channel not in [control.channel for control in self.bleedthrough_list]:
                self.bleedthrough_list.append(_BleedthroughControl(channel = channel))
                
            if channel not in [unit.channel for unit in self.units_list]:
                self.units_list.append(_Unit(channel = channel))

            
        to_remove = []    
        for control in self.bleedthrough_list:
            if control.channel not in self.channels:
                to_remove.append(control)
                
        for control in to_remove:
            self.bleedthrough_list.remove(control)
            
        to_remove = []    
        for unit in self.units_list:
            if unit.channel not in self.channels:
                to_remove.append(unit)
        
        for unit in to_remove:        
            self.units_list.remove(unit)
                
        if self.do_color_translation:
            to_remove = []
            for unit in self.units_list:
                if unit.channel != self.to_channel:
                    to_remove.append(unit)
            
            for unit in to_remove:
                self.units_list.remove(unit)
                 
            self.translation_list = []
            for c in self.channels:
                if c == self.to_channel:
                    continue
                self.translation_list.append(_TranslationControl(from_channel = c,
                                                                 to_channel = self.to_channel))
                
            self.changed = (Changed.ESTIMATE, ('translation_list', self.translation_list))
            
        self.changed = (Changed.ESTIMATE, ('bleedthrough_list', self.bleedthrough_list))            
        self.changed = (Changed.ESTIMATE, ('units_list', self.units_list))


    @on_trait_change('_polygon_op:vertices', post_init = True)
    def _polygon_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, (None, None))

    @on_trait_change("bleedthrough_list_items, bleedthrough_list.+", post_init = True)
    def _bleedthrough_controls_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('bleedthrough_list', self.bleedthrough_list))
     
    @on_trait_change("translation_list_items, translation_list.+", post_init = True)
    def _translation_controls_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('translation_list', self.translation_list))
        
    @on_trait_change('units_list_items,units_list.+', post_init = True)
    def _units_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('units_list', self.units_list))
#     
    def estimate(self, experiment, subset = None):
#         if not self.subset:
#             warnings.warn("Are you sure you don't want to specify a subset "
#                           "used to estimate the model?",
#                           util.CytoflowOpWarning)
            
#         if experiment is None:
#             raise util.CytoflowOpError("No valid result to estimate with")
        
#         experiment = experiment.clone()

        if not self.fsc_channel:
            raise util.CytoflowOpError('fsc_channel',
                                       "Must set FSC channel")
            
        if not self.ssc_channel:
            raise util.CytoflowOpError('ssc_channel',
                                       "Must set SSC channel")
        
        if not self._polygon_op.vertices:
            raise util.CytoflowOpError(None, "Please draw a polygon around the "
                                             "single-cell population in the "
                                             "Morphology tab")            

        experiment = self._blank_exp.clone()
        experiment = self._polygon_op.apply(experiment)
        
        self._af_op.channels = self.channels
        self._af_op.blank_file = self.blank_file
        
        self._af_op.estimate(experiment, subset = "polygon == True")
        self.changed = (Changed.ESTIMATE_RESULT, "Autofluorescence")
        experiment = self._af_op.apply(experiment)
        
        self.status = "Estimating bleedthrough"
        
        self._bleedthrough_op.controls.clear()
        for control in self.bleedthrough_list:
            self._bleedthrough_op.controls[control.channel] = control.file

        self._bleedthrough_op.estimate(experiment, subset = "polygon == True") 
        self.changed = (Changed.ESTIMATE_RESULT, "Bleedthrough")
        experiment = self._bleedthrough_op.apply(experiment)
        
        self.status = "Estimating bead calibration"
        
        self._bead_calibration_op.beads = BeadCalibrationOp.BEADS[self.beads_name]
        self._bead_calibration_op.beads_file = self.beads_file
        self._bead_calibration_op.bead_peak_quantile = self.bead_peak_quantile
        self._bead_calibration_op.bead_brightness_threshold = self.bead_brightness_threshold
        self._bead_calibration_op.bead_brightness_cutoff = self.bead_brightness_cutoff        
        
        self._bead_calibration_op.units.clear()

        for unit in self.units_list:
            self._bead_calibration_op.units[unit.channel] = unit.unit
            
        self._bead_calibration_op.estimate(experiment)
        self.changed = (Changed.ESTIMATE_RESULT, "Bead Calibration")
        
        if self.do_color_translation:
            self.status = "Estimating color translation"

            experiment = self._bead_calibration_op.apply(experiment)
            
            self._color_translation_op.mixture_model = self.mixture_model
            
            self._color_translation_op.controls.clear()
            for control in self.translation_list:
                self._color_translation_op.controls[(control.from_channel,
                                                     control.to_channel)] = control.file
                                                     
            self._color_translation_op.estimate(experiment, subset = 'polygon == True')                                         
            
            self.changed = (Changed.ESTIMATE_RESULT, "Color Translation")
            
        self.status = "Done estimating"
        self.valid_model = True
        
        
    def should_clear_estimate(self, changed, payload):
        """
        Should the owning WorkflowItem clear the estimated model by calling
        op.clear_estimate()?  `changed` can be:
         - Changed.ESTIMATE -- the parameters required to call 'estimate()' (ie
            traits with estimate = True metadata) have changed
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         """
        if changed == Changed.ESTIMATE:
            name, val = payload
            if name == 'fsc_channel' or name == 'ssc_channel':
                return False
                    
        return True
        
        
    def clear_estimate(self):
        self._af_op = AutofluorescenceOp()
        self._bleedthrough_op = BleedthroughLinearOp()
        self._bead_calibration_op = BeadCalibrationOp()
        self._color_translation_op = ColorTranslationOp()
        self.valid_model = False
        
        self.changed = (Changed.ESTIMATE_RESULT, self)
                        
    def should_apply(self, changed, payload):
        """
        Should the owning WorkflowItem apply this operation when certain things
        change?  `changed` can be:
         - Changed.OPERATION -- the operation's parameters changed
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
        """
        if changed == Changed.ESTIMATE_RESULT and \
            self.blank_file != self._blank_exp_file:
            return True
        
        elif changed == Changed.OPERATION:
            name, _ = payload
            if name == "output_directory":
                return False

            return True
        
        return False

        
        
    def apply(self, experiment):

        if self.blank_file != self._blank_exp_file:
            self._blank_exp = ImportOp(tubes = [Tube(file = self.blank_file)] ).apply()
            self._blank_exp_file = self.blank_file
            self._blank_exp_channels = self._blank_exp.channels
            self.changed = (Changed.PREV_RESULT, None)
            return
        
            
        out_dir = Path(self.output_directory)
        for path in self.input_files:
            in_file_path = Path(path)
            out_file_path = out_dir / in_file_path.name
            if out_file_path.exists():
                raise util.CytoflowOpError(None,
                                           "File {} already exists"
                                           .format(out_file_path))
                
        tubes = [Tube(file = path, conditions = {'filename' : Path(path).stem})
                 for path in self.input_files]
        
        for tube in tubes:
            self.status = "Converting " + Path(tube.file).stem
            experiment = ImportOp(tubes = [tube], conditions = {'filename' : 'category'}).apply()
            
            experiment = self._af_op.apply(experiment)
            experiment = self._bleedthrough_op.apply(experiment)
            experiment = self._bead_calibration_op.apply(experiment)
            
            if self.do_color_translation:
                experiment = self._color_translation_op.apply(experiment)
                
            tube_meta = fcsparser.parse( tube.file, 
                                         channel_naming = experiment.metadata["name_metadata"],
                                         meta_data_only = True,
                                         reformat_meta = False)
            
            del tube_meta['__header__']
            
            tube_meta = {k:v for (k,v) in tube_meta.items() if not k.startswith("flowCore_")}
            tube_meta = {k:v for (k,v) in tube_meta.items() if not (k.startswith("$P") and k[2].isdigit())}
            
            drop_kws = ["$BEGINANALYSIS", "$ENDANALYSIS", 
                        "$BEGINSTEXT", "$ENDSTEXT",
                        "$BEGINDATA", "$ENDDATA",
                        "$BYTEORD", "$DATATYPE",
                        "$MODE", "$NEXTDATA", "$TOT", "$PAR"]
            
            tube_meta = {k:v for (k,v) in tube_meta.items() if not k in drop_kws}                                                     
                    
            ExportFCS(path = self.output_directory,
                      by = ['filename'],
                      _include_by = False,
                      keywords = tube_meta).export(experiment)
                      
        self.input_files = []
        self.status = "Done converting!"
    
    
    def default_view(self, **kwargs):
        return TasbeCalibrationView(op = self, **kwargs)

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
class TasbeCalibrationView(PluginViewMixin):
    handler_factory = Callable(TasbeViewHandler)
    op = Instance(TasbeCalibrationOp)
    
    id = "edu.mit.synbio.cytoflowgui.op_plugins.tasbe"
    friendly_id = "TASBE Calibration" 
    
    name = Constant("TASBE Calibration")

    fsc_channel = DelegatesTo('op')
    ssc_channel = DelegatesTo('op')

    _polygon_view = Instance(PolygonSelection, transient = True)
    interactive = Property(Bool)
    
    def _get_interactive(self):
        if self._polygon_view:
            return self._polygon_view.interactive
        else:
            return False
        
    def _set_interactive(self, val):
        if self._polygon_view:
            self._polygon_view.interactive = val
    
    def plot_wi(self, wi):
        self.plot(None, plot_name = self.current_plot)
        
    def enum_plots(self, experiment):
        return iter(["Morphology",
                     "Autofluorescence",
                     "Bleedthrough",
                     "Bead Calibration",
                     "Color Translation"])
        
    def enum_plots_wi(self, wi):
        return iter(["Morphology",
                     "Autofluorescence",
                     "Bleedthrough",
                     "Bead Calibration",
                     "Color Translation"])

    def should_plot(self, changed, payload):
        """
        Should the owning WorkflowItem refresh the plot when certain things
        change?  `changed` can be:
         - Changed.VIEW -- the view's parameters changed
         - Changed.RESULT -- this WorkflowItem's result changed
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
        """
        if changed == Changed.VIEW:
            _, name, _ = payload
            if self.current_plot == 'Morphology' and (name == 'fsc_channel' or name == 'ssc_channel'):
                return True
            elif name == 'current_plot':
                return True
        elif changed == Changed.PREV_RESULT:
            if self.current_plot == payload:
                return True
        else:
            return False

        
    def plot(self, experiment, plot_name = None, **kwargs):
        
        if plot_name not in ["Morphology", 
                             "Autofluorescence", 
                             "Bleedthrough", 
                             "Bead Calibration", 
                             "Color Translation"]:
            raise util.CytoflowViewError("Which plot do you want?  Must be one "
                                         "of \"Morphology\", \"Autofluorescence\", "
                                         "\"Bleedthrough\", \"Bead Calibration\", "
                                         "or \"Color Translation\"")
                    
        if not self.op._blank_exp:
            raise util.CytoflowViewError("Must set at least the blank control file!")
        
        new_ex = self.op._blank_exp.clone()

        if plot_name == "Morphology":
            if not self._polygon_view:
                self._polygon_view = self.op._polygon_op.default_view()
            
            self._polygon_view.plot(new_ex, **kwargs)
            
            return
        else:
            new_ex = self.op._polygon_op.apply(new_ex)
                    
        if plot_name == "Autofluorescence":
            self.op._af_op.default_view().plot(new_ex, **kwargs)
            return
        else:
            new_ex = self.op._af_op.apply(new_ex)

        if plot_name == "Bleedthrough":
            self.op._bleedthrough_op.default_view().plot(new_ex, **kwargs)
            return
        else:
            new_ex = self.op._bleedthrough_op.apply(new_ex)
            
        if plot_name == "Bead Calibration":
            self.op._bead_calibration_op.default_view().plot(new_ex, **kwargs)
            return
        else:
            new_ex = self.op._bead_calibration_op.apply(new_ex)
            
        if plot_name == "Color Translation":
            self.op._color_translation_op.default_view().plot(new_ex, **kwargs)

