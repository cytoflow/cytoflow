#!/usr/bin/env python3.4
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

import warnings, os
from pathlib import Path
from traits.api import (HasTraits, provides, Str, observe, Instance, Int, Bool,
                        List, File, Float, Property, Constant, DelegatesTo,
                        Event, Directory)

from cytoflow import (Experiment, AutofluorescenceOp, BleedthroughLinearOp, 
                      BeadCalibrationOp, ColorTranslationOp, PolygonOp,
                      ImportOp, Tube, ExportFCS)
from cytoflow.operations.polygon import PolygonSelection
import cytoflow.utility as util

from .. import Changed
from ..views import IWorkflowView, WorkflowView
from ..views.view_base import IterWrapper
from ..serialization import camel_registry, traits_repr, dedent
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

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
class TasbeCalibrationOp(WorkflowOperation):   
    id = Constant('edu.mit.synbio.cytoflowgui.op_plugins.bleedthrough_piecewise')
    friendly_id = Constant("Quantitative Pipeline")
    name = Constant("TASBE")
    
    fsc_channel = DelegatesTo('_polygon_op', 'xchannel', estimate = True)
    ssc_channel = DelegatesTo('_polygon_op', 'ychannel', estimate = True)
    vertices = DelegatesTo('_polygon_op', 'vertices', estimate = True)
    channels = List(Str, estimate = True)
    
    blank_file = File(filter = ["*.fcs"], estimate = True)
    
    bleedthrough_list = List(BleedthroughControl, estimate = True)

    beads_name = Str(estimate = True)
    beads_file = File(filter = ["*.fcs"], estimate = True)
    units_list = List(BeadUnit, estimate = True)
    
    bead_peak_quantile = Int(80, estimate = True)
    bead_brightness_threshold = Float(100, estimate = True)
    bead_brightness_cutoff = util.FloatOrNone("", estimate = True)
    
    do_color_translation = Bool(estimate = True)
    to_channel = Str(estimate = True)
    translation_list = List(TranslationControl, estimate = True)
    mixture_model = Bool(False, estimate = True)
    
    do_estimate = Event
    do_exit = Event
    input_files = List(File)
    output_directory = Directory
        
    _experiment = Instance(Experiment, transient = True)

    _polygon_op = Instance(PolygonOp, 
                           kw = {'name' : 'polygon',
                                 'xscale' : 'log', 
                                 'yscale' : 'log'}, 
                           transient = True)
    _af_op = Instance(AutofluorescenceOp, (), transient = True)
    _bleedthrough_op = Instance(BleedthroughLinearOp, (), transient = True)
    _bead_calibration_op = Instance(BeadCalibrationOp, (), transient = True)
    _color_translation_op = Instance(ColorTranslationOp, (), transient = True)
    
    status = Str(Progress.NO_MODEL, estimate_result = True, status = True)
    
    @observe('channels.items,to_channel,do_color_translation', post_init = True)
    def _channels_changed(self, _):
        for channel in self.channels:
            if channel not in [control.channel for control in self.bleedthrough_list]:
                self.bleedthrough_list.append(BleedthroughControl(channel = channel))
                
            if channel not in [unit.channel for unit in self.units_list]:
                self.units_list.append(BeadUnit(channel = channel))

            
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
                self.translation_list.append(TranslationControl(from_channel = c,
                                                                 to_channel = self.to_channel))


    @observe('vertices', post_init = True)
    def _on_polygon_changed(self, _):
        self.changed = '_polygon_op'

    @observe("bleedthrough_list:items:file", post_init = True)
    def _bleedthrough_controls_changed(self, _):
        self.changed = 'bleedthrough_list'
     
    @observe("translation_list:items:file", post_init = True)
    def _on_translation_controls_changed(self, _):
        self.changed = 'translation_list'
        
    @observe('units_list:items:file', post_init = True)
    def _on_units_changed(self, _):
        self.changed = 'units_list'
        
    @observe('blank_file,bleedthrough_list:items:file,translation_list:items:file')
    def _update_experiment(self, _):
        control_files = set(self.blank_file)
        control_files = control_files.union({x.file for x in self.bleedthrough_list})
        control_files = control_files.union({x.file for x in self.translation_list})
        self._experiment = ImportOp(conditions = {'name' : 'category'},
                                    tubes = [Tube(file = x, 
                                                  conditions = {'name' : x})
                                             for x in control_files] ).apply()
        


    def estimate(self, experiment, subset = None):
        if not self._experiment:
            raise util.CytoflowOpError(None, "Please set at least one control before "
                                             "trying to estimate!")
            
        if not self.fsc_channel:
            raise util.CytoflowOpError('fsc_channel',
                                       "Must set FSC channel")
            
        if not self.ssc_channel:
            raise util.CytoflowOpError('ssc_channel',
                                       "Must set SSC channel")
        
        if not self.vertices:
            raise util.CytoflowOpError(None, "Please draw a polygon around the "
                                             "single-cell population in the "
                                             "Morphology tab")            

        experiment = self._experiment.clone()
        experiment = self._polygon_op.apply(experiment)
        
        self.status = Progress.AUTOFLUORESCENCE
        
        self._af_op.channels = self.channels
        self._af_op.blank_file = self.blank_file
        
        self._af_op.estimate(experiment, subset = "polygon == True")
        self.changed = (Changed.ESTIMATE_RESULT, "Autofluorescence")
        experiment = self._af_op.apply(experiment)

        self.status = Progress.BLEEDTHROUGH
        
        self._bleedthrough_op.controls.clear()
        for control in self.bleedthrough_list:
            self._bleedthrough_op.controls[control.channel] = control.file

        self._bleedthrough_op.estimate(experiment, subset = "polygon == True") 
        self.changed = (Changed.ESTIMATE_RESULT, "Bleedthrough")
        experiment = self._bleedthrough_op.apply(experiment)
        
        self.status = Progress.BEAD_CALIBRATION
        
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
            self.status = Progress.COLOR_TRANSLATION

            experiment = self._bead_calibration_op.apply(experiment)
            
            self._color_translation_op.mixture_model = self.mixture_model
            
            self._color_translation_op.controls.clear()
            for control in self.translation_list:
                self._color_translation_op.controls[(control.from_channel,
                                                     control.to_channel)] = control.file
                                                     
            self._color_translation_op.estimate(experiment, subset = 'polygon == True')                                         
            
            self.changed = (Changed.ESTIMATE_RESULT, "Color Translation")
            
        self.status = Progress.VALID      
        
#     def should_clear_estimate(self, changed, payload):
#         if changed == Changed.ESTIMATE:
#             return True
#         
#         return False    
        
    def clear_estimate(self):
        self._af_op = AutofluorescenceOp()
        self._bleedthrough_op = BleedthroughLinearOp()
        self._bead_calibration_op = BeadCalibrationOp()
        self._color_translation_op = ColorTranslationOp()
        self.estimate_progress = Progress.NO_MODEL  
        
        
    def should_apply(self, changed, payload):
        # we only want this to return True when the do_convert handler
        # updates the output path
        return False
                                
#     def should_apply(self, changed, payload):
#         """
#         Should the owning WorkflowItem apply this operation when certain things
#         change?  `changed` can be:
#         - Changed.OPERATION -- the operation's parameters changed
#         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
#         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
# 
#         """
#         if changed == Changed.ESTIMATE_RESULT and \
#             self.blank_file != self._blank_exp_file:
#             return True
#         
#         elif changed == Changed.OPERATION:
#             name, _ = payload
#             if name == "output_directory":
#                 return False
# 
#             return True
#         
#         return False
# 
#         
        
    def apply(self, experiment):

        # this "apply" function is a little odd -- it does not return an Experiment because
        # it always the only WI/operation in the workflow.
#         
#         if self.blank_file != self._blank_exp_file:
#             self._blank_exp = ImportOp(tubes = [Tube(file = self.blank_file)] ).apply()
#             self._blank_exp_file = self.blank_file
#             self._blank_exp_channels = self._blank_exp.channels
#             self.changed = (Changed.PREV_RESULT, None)
#             return
#         
#             
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
                    
            ExportFCS(path = self.output_directory,
                      by = ['filename'],
                      _include_by = False).export(experiment)
                      
        self.input_files = []
        self.status = "Done converting!"
    
    
    def default_view(self, **kwargs):
        return TasbeCalibrationView(op = self, **kwargs)
    
    def get_help(self):
        current_dir = os.path.abspath(__file__)
        help_dir = os.path.split(current_dir)[0]
        help_dir = os.path.join(help_dir, "help")
        
        help_file = None
        for klass in self.__class__.__mro__:
            mod = klass.__module__
            mod_html = mod + ".html"
            
            h = os.path.join(help_dir, mod_html)
            if os.path.exists(h):
                help_file = h
                break
                
        with open(help_file, encoding = 'utf-8') as f:
            help_html = f.read()
            
        return help_html
    

@provides(IWorkflowView)
class TasbeCalibrationView(WorkflowView):
    op = Instance(TasbeCalibrationOp)
    
    id = "edu.mit.synbio.cytoflowgui.op_plugins.tasbe"
    friendly_id = "TASBE Calibration" 
    
    name = Constant("TASBE Calibration")

    fsc_channel = DelegatesTo('op')
    ssc_channel = DelegatesTo('op')

    _polygon_view = Instance(PolygonSelection, transient = True)
    interactive = Property(Bool)
    
    plot_params = Instance(HasTraits, ())
    
    def _get_interactive(self):
        if self._polygon_view:
            return self._polygon_view.interactive
        else:
            return False
        
    def _set_interactive(self, val):
        if self._polygon_view:
            self._polygon_view.interactive = val
        
    def enum_plots(self, experiment):
        return IterWrapper(iter(["Morphology",
                                 "Autofluorescence",
                                 "Bleedthrough",
                                 "Bead Calibration",
                                 "Color Translation"]),
                            [])
# 
#     def should_plot(self, changed, payload):
#         """
#         Should the owning WorkflowItem refresh the plot when certain things
#         change?  `changed` can be:
#         - Changed.VIEW -- the view's parameters changed
#         - Changed.RESULT -- this WorkflowItem's result changed
#         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
#         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
# 
#         """
#         if changed == Changed.VIEW:
#             _, name, _ = payload
#             if self.current_plot == 'Morphology' and (name == 'fsc_channel' or name == 'ssc_channel'):
#                 return True
#             elif name == 'current_plot':
#                 return True
#         elif changed == Changed.PREV_RESULT:
#             if self.current_plot == payload:
#                 return True
#         else:
#             return False

        
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
                     
        if not self.op._experiment:
            raise util.CytoflowViewError("Must set at least one control file!")
         
        new_ex = self.op._experiment.clone()
 
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

