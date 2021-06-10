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

from natsort import natsorted

from traits.api import provides, Event, Property, List, Str
from traitsui.api import View, Item, VGroup, TextEditor, ButtonEditor, FileEditor, HGroup, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from ..view_plugins import ViewHandler
from ..editors import ColorTextEditor, InstanceHandlerEditor, VerticalListEditor
from ..workflow.operations import BeadCalibrationWorkflowOp, BeadCalibrationWorkflowView, BeadCalibrationUnit

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class UnitHandler(Controller):
    unit_view = View(HGroup(Item('channel',
                                 editor = EnumEditor(name = 'context_handler.channels')),
                            Item('unit',
                                 editor = EnumEditor(name = 'context_handler.beads_units'),
                                 show_label = False)))
    

class BeadCalibrationHandler(OpHandler):
    
    add_channel = Event
    remove_channel = Event
    channels = Property(List(Str), observe = 'context.channels')
    
    beads_name_choices = Property
    beads_units = Property(depends_on = 'model.beads_name')
    
    operation_traits_view = \
        View(VGroup(
             Item('beads_name',
                  editor = EnumEditor(name = 'handler.beads_name_choices'),
                  label = "Beads"),
             Item('beads_file',
                  editor = FileEditor(dialog_style = 'open'))),
             VGroup(Item('units_list',
                         editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'unit_view',
                                                                                    handler_factory = UnitHandler),
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
             Item('do_estimate',
                  editor = ButtonEditor(value = True,
                                        label = "Estimate!"),
                  show_label = False),
             shared_op_traits_view)
        
    # MAGIC: called when add_control is set
    def _add_channel_fired(self):
        self.model.units_list.append(BeadCalibrationUnit())
        
    def _remove_channel_fired(self):
        if self.model.units_list:
            self.model.units_list.pop()   
            
    def _get_channels(self):
        if self.context and self.context.channels:
            return natsorted(self.context.channels)
        else:
            return [] 
    
    def _get_beads_name_choices(self):
        return list(self.model.BEADS.keys())
    
    def _get_beads_units(self):
        if self.model.beads_name:
            return list(self.model.BEADS[self.model.beads_name].keys())
        else:
            return []



class BeadCalibrationViewHandler(ViewHandler):
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
class BeadCalibrationPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.beads_calibrate'
    operation_id = 'edu.mit.synbio.cytoflow.operations.beads_calibrate'
    view_id = 'edu.mit.synbio.cytoflow.view.beadcalibrationdiagnosticview'

    short_name = "Bead Calibration"
    menu_group = "Calibration"
    
    def get_operation(self):
        return BeadCalibrationWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, BeadCalibrationWorkflowOp):
            return BeadCalibrationHandler(model = model, context = context)
        elif isinstance(model, BeadCalibrationWorkflowView):
            return BeadCalibrationViewHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('bead_calibration')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
    
