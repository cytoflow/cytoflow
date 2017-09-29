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
Bead Calibration
----------------

Calibrate arbitrary channels to molecules-of-fluorophore using fluorescent
beads (eg, the **Spherotech RCP-30-5A** rainbow beads.)

Computes a log-linear calibration function that maps arbitrary fluorescence
units to physical units (ie molecules equivalent fluorophore, or *MEF*).

To use, set **Beads** to the beads you calibrated with (check the lot!) and
**Beads File** to an FCS file containing events collected *using
the same cytometer settings as the data you're calibrating*.  Then, click 
**Add a channel** to add the channels to calibrate, and set both the channel 
name and the units you want calibrate to.  Click **Estimate**, and *make sure
you check the diagnostic plot to see that the correct peaks were found.*

If it didn't find all the peaks (or found too many), try tweaking 
**Peak Quantile**, **Peak Threshold** and **Peak Cutoff**.  If you can't make 
the peak finding work by tweaking , please submit a bug report!

.. object:: Beads

    The beads you're calibrating with.  Make sure to check the lot number!

.. object:: Beads file

    A file containing the FCS events from the beads.
    
.. object:: Channels
    
    A list of the channels you want calibrated and the units you want them 
    calibrated in.       
    
.. object:: Peak Quantile

    Peaks must be at least this quantile high to be considered.  Default = 80.
    
.. object:: Peak Threshold

    Don't search for peaks below this brightness.  Default = 100.
    
.. object: Peak Cutoff

    Don't search for peaks above this brightness.  Default: 70% of detector range.

    
.. plot::
    
    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "tasbe/rby.fcs")]
    ex = import_op.apply()

    bead_op = flow.BeadCalibrationOp()
    beads = "Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R"
    bead_op.beads = flow.BeadCalibrationOp.BEADS[beads]
    bead_op.units = {"Pacific Blue-A" : "MEBFP",
                     "FITC-A" : "MEFL",
                     "PE-Tx-Red-YG-A" : "MEPTR"}
    
    bead_op.beads_file = "tasbe/beads.fcs"

    bead_op.estimate(ex)

    bead_op.default_view().plot(ex)  

    ex = bead_op.apply(ex)  
'''

from traitsui.api import (View, Item, EnumEditor, Controller, VGroup, 
                          ButtonEditor, HGroup, InstanceEditor)
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, List, Str, HasTraits, File, Event, 
                        on_trait_change, Property, Dict, Int, Float, Undefined)
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations.bead_calibration import BeadCalibrationOp, BeadCalibrationDiagnostic
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.vertical_list_editor import VerticalListEditor
from cytoflowgui.workflow import Changed

class _Unit(HasTraits):
    channel = Str
    unit = Str

class BeadCalibrationHandler(OpHandlerMixin, Controller):
    
    add_channel = Event
    remove_channel = Event
    
    beads_name_choices = Property()
    beads_units = Property(depends_on = 'model.beads_name')
    
    # MAGIC: called when add_control is set
    def _add_channel_fired(self):
        self.model.units_list.append(_Unit())
        
    def _remove_channel_fired(self):
        if self.model.units_list:
            self.model.units_list.pop()    
    
    def _get_beads_name_choices(self):
        return list(self.model.BEADS.keys())
    
    def _get_beads_units(self):
        if self.model.beads_name:
            return list(self.model.BEADS[self.model.beads_name].keys())
        else:
            return []
    
    def unit_traits_view(self):
        return View(HGroup(Item('channel',
                                editor = EnumEditor(name = 'handler.context.previous_wi.channels')),
                           Item('unit',
                                editor = EnumEditor(name = 'handler.beads_units'),
                                show_label = False)),
                    handler = self)
    
    def default_traits_view(self):
        return View(VGroup(
                    Item('beads_name',
                         editor = EnumEditor(name = 'handler.beads_name_choices'),
                         label = "Beads",
                         width = -125),
                    Item('beads_file',
                         width = -125)),
                    VGroup(Item('units_list',
                                editor = VerticalListEditor(editor = InstanceEditor(view = self.unit_traits_view()),
                                                            style = 'custom',
                                                            mutable = False),
                                style = 'custom'),
                    Item('handler.add_channel',
                         editor = ButtonEditor(value = True,
                                               label = "Add a channel")),
                    Item('handler.remove_channel',
                         editor = ButtonEditor(value = True,
                                               label = "Remove a channel")),
                    label = "Controls",
                    show_labels = False),
                    Item('bead_peak_quantile',
                         label = "Peak\nQuantile"),
                    Item('bead_brightness_threshold',
                         label = "Peak\nThreshold "),
                    Item('bead_brightness_cutoff',
                         label = "Peak\nCutoff"),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    shared_op_traits)

class BeadCalibrationPluginOp(PluginOpMixin, BeadCalibrationOp):
    handler_factory = Callable(BeadCalibrationHandler)

    beads_name = Str(estimate = True)   
    beads = Dict(Str, List(Float), transient = True)
 
    beads_file = File(filter = ["*.fcs"], estimate = True)
    units_list = List(_Unit, estimate = True)
    units = Dict(Str, Str, transient = True)

    bead_peak_quantile = Int(80, estimate = True)
    bead_brightness_threshold = Float(100, estimate = True)
    bead_brightness_cutoff = Float(Undefined, estimate = True)

    @on_trait_change('units_list_items,units_list.+', post_init = True)
    def _controls_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('units_list', self.units_list))
    
    def default_view(self, **kwargs):
        return BeadCalibrationPluginView(op = self, **kwargs)
    
    def apply(self, experiment):

        if not self.beads_name:
            raise util.CytoflowOpError("Specify which beads to calibrate with.")
                
        for i, unit_i in enumerate(self.units_list):
            for j, unit_j in enumerate(self.units_list):
                if unit_i.channel == unit_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(unit_i.channel))
                                               
        self.units = {}
        for unit in self.units_list:
            self.units[unit.channel] = unit.unit
                    
        self.beads = self.BEADS[self.beads_name]
        return BeadCalibrationOp.apply(self, experiment)
    
    def estimate(self, experiment):
        if not self.beads_name:
            raise util.CytoflowOpError("Specify which beads to calibrate with.")
                
        for i, unit_i in enumerate(self.units_list):
            for j, unit_j in enumerate(self.units_list):
                if unit_i.channel == unit_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(unit_i.channel))
                                               
        self.units = {}
        for unit in self.units_list:
            self.units[unit.channel] = unit.unit
                    
        self.beads = self.BEADS[self.beads_name]
        BeadCalibrationOp.estimate(self, experiment)
        self.changed = (Changed.ESTIMATE_RESULT, self)

    
    def should_clear_estimate(self, changed):
        if changed == Changed.ESTIMATE:
            return True
        
        return False
        
    def clear_estimate(self):
        self._calibration_functions.clear()
        self._peaks.clear()
        self._mefs.clear()
        self.changed = (Changed.ESTIMATE_RESULT, self)

class BeadCalibrationViewHandler(ViewHandlerMixin, Controller):
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
class BeadCalibrationPluginView(PluginViewMixin, BeadCalibrationDiagnostic):
    handler_factory = Callable(BeadCalibrationViewHandler)
    
    def plot_wi(self, wi):
        self.plot(wi.previous_wi.result)
        
    def should_plot(self, changed):
        if changed == Changed.ESTIMATE_RESULT:
            return True
        
        return False
    

@provides(IOperationPlugin)
class BeadCalibrationPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.bead_calibrate'
    operation_id = 'edu.mit.synbio.cytoflow.operations.bead_calibrate'

    short_name = "Bead Calibration"
    menu_group = "Calibration"
    
    def get_operation(self):
        return BeadCalibrationPluginOp()
    
    def get_icon(self):
        return ImageResource('bead_calibration')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    