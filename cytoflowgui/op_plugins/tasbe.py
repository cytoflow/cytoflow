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

from traits.api import provides, Property
from traitsui.api import View, Item, VGroup, ButtonEditor, FileEditor, HGroup, EnumEditor, Controller, CheckListEditor, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.operations.bead_calibration import BeadCalibrationOp

from ..view_plugins import ViewHandler
from ..editors import ColorTextEditor, InstanceHandlerEditor, VerticalListEditor, SubsetListEditor
from ..subset_controllers import subset_handler_factory
from ..workflow.operations import TasbeWorkflowOp, TasbeWorkflowView

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin

class BleedthroughControlHandler(Controller):
    control_view = View(HGroup(Item('channel', style = 'readonly'),
                               Item('file', 
                                    editor = FileEditor(dialog_style = 'open'),
                                    show_label = False),
                               show_labels = False))
    
class TranslationControlHandler(Controller):
    control_view = View(HGroup(Item('from_channel', style = 'readonly', show_label = False),
                               Item('', label = '->'),
                               Item('to_channel', style = 'readonly', show_label = False),
                               Item('file', 
                                    editor = FileEditor(dialog_style = 'open'),
                                    show_label = False),
                               show_labels = False))
    

class TasbeHandler(OpHandler):
                
    beads_name_choices = Property(transient = True)
    beads_units = Property(observe = 'model.beads_name')
    
    def _get_beads_name_choices(self):
        return list(BeadCalibrationOp.BEADS.keys())
    
    def _get_beads_units(self):
        if self.model.beads_name:
            return list(BeadCalibrationOp.BEADS[self.model.beads_name].keys())
        else:
            return []
    
    operation_traits_view = \
        View(Item("channels",
                  editor = CheckListEditor(cols = 2,
                                           name = 'context_handler.previous_channels'),
                  style = 'custom'),
             VGroup(
                 Item('blank_file',
                      editor = FileEditor(dialog_style = 'open')),
                 label = "Autofluorescence"),
             VGroup(
                 Item('bleedthrough_list',
                      editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'control_view',
                                                                                 handler_factory = BleedthroughControlHandler),
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
                 Item('beads_file',
                      editor = FileEditor(dialog_style = 'open')),
                 Item('beads_unit', 
                      editor = EnumEditor(name = 'handler.beads_units')),
                 Item('bead_peak_quantile',
                      editor = TextEditor(auto_set = False,
                                         evaluate = int,
                                         format_func = lambda x: "" if x is None else str(x),
                                         placeholder = "None"),
                      label = "Peak\nQuantile"),
                 Item('bead_brightness_threshold',
                      editor = TextEditor(auto_set = False,
                                          evaluate = float,
                                          format_func = lambda x: "" if x is None else str(x),
                                          placeholder = "None"),
                      label = "Peak\nThreshold "),
                 Item('bead_brightness_cutoff',
                      editor = TextEditor(auto_set = False,
                                          evaluate = float,
                                          format_func = lambda x: "" if x is None else str(x),
                                          placeholder = "None"),
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
                         editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'control_view',
                                                                                    handler_factory = TranslationControlHandler),
                                                     style = 'custom',
                                                     mutable = False),
                         style = 'custom'),

                 show_labels = False),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "context_handler.previous_conditions",
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory))),
                    label = "Subset",
                    show_border = False,
                    show_labels = False),
             Item('estimate_progress', style = 'readonly'),
             Item('do_estimate',
                  editor = ButtonEditor(value = True,
                                        label = "Estimate!"),
                  show_label = False),
             shared_op_traits_view)


class TasbeViewHandler(ViewHandler):
    view_traits_view = \
        View(Item('context.view_warning',
                  resizable = True,
                  visible_when = 'context.view_warning',
                  editor = ColorTextEditor(foreground_color = "#000000",
                                          background_color = "#ffff99")),
             Item('context.view_error',
                  resizable = True,
                  visible_when = 'context.view_error',
                  editor = ColorTextEditor(foreground_color = "#000000",
                                           background_color = "#ff9191")))
        
    view_params_view = View()


@provides(IOperationPlugin)
class TasbePlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.op_plugins.tasbe'
    operation_id = 'edu.mit.synbio.cytoflowgui.workflow.operations.tasbe'
    view_id = 'edu.mit.synbio.cytoflowgui.workflow.operations.tasbeview'

    short_name = "TASBE Calibration"
    menu_group = "Gates"
    
    def get_operation(self):
        return TasbeWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, TasbeWorkflowOp):
            return TasbeHandler(model = model, context = context)
        elif isinstance(model, TasbeWorkflowView):
            return TasbeViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('tasbe')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
