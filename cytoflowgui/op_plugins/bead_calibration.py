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

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor, \
                         CheckListEditor, ButtonEditor, Heading, TableEditor, \
                         TableColumn, ObjectColumn
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Bool, CFloat, List, Str, HasTraits, \
                       File, Event, on_trait_change, Property, Instance, \
                       Dict, Int, Float
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations.bead_calibration import BeadCalibrationOp, BeadCalibrationDiagnostic
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

class _Unit(HasTraits):
    channel = Str
    unit = Str

class BeadCalibrationHandler(Controller, OpHandlerMixin):
    
    beads_name_choices = Property(transient = True)
    beads_units = Property(transient = True)
    
    def _get_beads_name_choices(self):
        return self.model.BEADS.keys()
    
    def _get_beads_units(self):
        if self.model.beads_name:
            return self.model.BEADS[self.model.beads_name].keys()
        else:
            return []
        
    
    def default_traits_view(self):
        return View(Item('beads_name',
                         editor = EnumEditor(name = 'handler.beads_name_choices'),
                         label = "Beads"),
                    Item('beads_file'),
                    Item('units_list',
                         editor=TableEditor(
                            columns = 
                                [ObjectColumn(name = 'channel',
                                              editor = EnumEditor(name = 'context.previous.channels'),
                                              resize_mode = 'fixed',
                                              width = 80),
                                 ObjectColumn(name = 'unit',
                                              editor = EnumEditor(name = 'handler.beads_units'),
                                              # 'fixed' with no width stretches to fill table
                                              resize_mode = 'fixed')],
                            row_factory = _Unit,
                            sortable = False),
                         show_label = False),
                    Item('add_channel',
                         editor = ButtonEditor(value = True,
                                               label = "Add a channel"),
                         show_label = False),
                    Item('bead_peak_quantile',
                         label = "Bead Peak\nQuantile"),
                    Item('bead_brightness_threshold',
                         label = "Bead\nThreshold "),
                    Item('context.do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    shared_op_traits)

class BeadCalibrationPluginOp(BeadCalibrationOp, PluginOpMixin):
    handler_factory = Callable(BeadCalibrationHandler)
    add_channel = Event

    beads_name = Str(estimate = True)    
    beads_file = File(estimate = True)
    units_list = List(_Unit, estimate = True)

    bead_peak_quantile = Int(80, estimate = True)
    bead_brightness_threshold = Float(100, estimate = True)

    @on_trait_change('units_list_items,units_list.+')
    def _controls_changed(self, obj, name, old, new):
        self.changed = "estimate"
        
    # MAGIC: called when add_control is set
    def _add_channel_fired(self):
        self.units_list.append(_Unit(op = self))
    
    def default_view(self, **kwargs):
        return BeadCalibrationPluginView(op = self, **kwargs)
    
    def estimate(self, experiment):
        for i, unit_i in enumerate(self.units_list):
            for j, unit_j in enumerate(self.units_list):
                if unit_i.channel == unit_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(unit_i.channel))
                                               
        units = {}
        for unit in self.units_list:
            units[unit.channel] = unit.unit
            
        self.units = units
        
        self.beads = self.BEADS[self.beads_name]
        BeadCalibrationOp.estimate(self, experiment)

class BeadCalibrationViewHandler(Controller, ViewHandlerMixin):
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
class BeadCalibrationPluginView(BeadCalibrationDiagnostic, PluginViewMixin):
    handler_factory = Callable(BeadCalibrationViewHandler)
    
    def plot_wi(self, wi):
        self.plot(wi.previous.result)

@provides(IOperationPlugin)
class BeadCalibrationPlugin(Plugin):
    """
    class docs
    """
    
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
    