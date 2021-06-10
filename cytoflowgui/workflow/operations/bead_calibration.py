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

from traits.api import (HasTraits, provides, Str, observe, Instance,
                        List, Dict, File, Float, Int, Callable)

from cytoflow.operations.bead_calibration import BeadCalibrationOp, BeadCalibrationDiagnostic
import cytoflow.utility as util

from .. import Changed
from ..views import IWorkflowView, WorkflowView
from ..serialization import camel_registry, traits_str, traits_repr, dedent

from .operation_base import IWorkflowOperation, WorkflowOperation

BeadCalibrationOp.__repr__ = traits_repr


class Unit(HasTraits):
    channel = Str
    unit = Str
    
    def __repr__(self):
        return traits_repr(self)


@provides(IWorkflowOperation)    
class BeadCalibrationWorkflowOp(WorkflowOperation, BeadCalibrationOp):
    # add the 'estimate' metadata

    beads_name = Str(estimate = True)   
    beads_file = File(filter = ["*.fcs"], estimate = True)
    units_list = List(Unit, estimate = True)

    bead_peak_quantile = Int(80, estimate = True)
    bead_brightness_threshold = Float(100.0, estimate = True)
    bead_brightness_cutoff = util.FloatOrNone(None, estimate = True)
    
    # add 'estimate_result' metadata
    _calibration_functions = Dict(Str, Callable, transient = True, estimate_result = True)

    @observe('units_list:items,units_list:items.+type', post_init = True)
    def _on_units_changed(self, event):
        self.changed = 'units_list'
    
    def default_view(self, **kwargs):
        return BeadCalibrationWorkflowView(op = self, **kwargs)
    
    def apply(self, experiment):

        if not self.beads_name:
            raise util.CytoflowOpError("Specify which beads to calibrate with.")

        self.beads = self.BEADS[self.beads_name]
                
        for i, unit_i in enumerate(self.units_list):
            for j, unit_j in enumerate(self.units_list):
                if unit_i.channel == unit_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(unit_i.channel))
                                               
        self.units = {u.channel : u.unit for u in self.units_list}
                    
        return super().apply(experiment)
    
    def estimate(self, experiment):
        if not self.beads_name:
            raise util.CytoflowOpError("Specify which beads to calibrate with.")
                
        self.beads = self.BEADS[self.beads_name]
                
        for i, unit_i in enumerate(self.units_list):
            for j, unit_j in enumerate(self.units_list):
                if unit_i.channel == unit_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(unit_i.channel))
                                               
        self.units = {u.channel : u.unit for u in self.units_list}

        super().estimate(experiment)
    
    def should_clear_estimate(self, changed, payload):
        if changed == Changed.ESTIMATE:
            return True
        
        return False
        
    def clear_estimate(self):
        self._peaks = {}
        self._mefs = {}
        self._histograms = {}
        self._calibration_functions = {}
        
    def get_notebook_code(self, idx):
        op = BeadCalibrationOp()
        op.copy_traits(self, op.copyable_trait_names())

        for unit in self.units_list:
            op.units[unit.channel] = unit.unit
                    
        op.beads = self.BEADS[self.beads_name]
        

        return dedent("""
        # Beads: {beads}
        op_{idx} = {repr}
        
        op_{idx}.estimate(ex_{prev_idx})
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(beads = self.beads_name,
                repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))
        
        
@provides(IWorkflowView)
class BeadCalibrationWorkflowView(WorkflowView, BeadCalibrationDiagnostic):
    plot_params = Instance(HasTraits, ())
    
    def should_plot(self, changed, payload):
        if changed == Changed.ESTIMATE_RESULT:
            return True
        
        return False
    
    def get_notebook_code(self, idx):
        view = BeadCalibrationDiagnostic()
        view.copy_traits(self, view.copyable_trait_names())
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx})
        """
        .format(traits = traits_str(view),
                idx = idx,
                prev_idx = idx - 1))
    

### Serialization
@camel_registry.dumper(BeadCalibrationWorkflowOp, 'bead-calibration', version = 1)
def _dump(bead_op):
    return dict(beads_name = bead_op.beads_name,
                beads_file = bead_op.beads_file,
                units_list = bead_op.units_list,
                bead_peak_quantile = bead_op.bead_peak_quantile,
                bead_brightness_threshold = bead_op.bead_brightness_threshold,
                bead_brightness_cutoff = bead_op.bead_brightness_cutoff)
    
@camel_registry.loader('bead-calibration', version = 1)
def _load(data, version):
    return BeadCalibrationWorkflowOp(**data)

@camel_registry.dumper(Unit, 'bead-unit', version = 1)
def _dump_unit(unit):
    return dict(channel = unit.channel,
                unit = unit.unit)
    
@camel_registry.loader('bead-unit', version = 1)
def _load_unit(data, version):
    return Unit(**data)

@camel_registry.dumper(BeadCalibrationWorkflowView, 'bead-calibration-view', version = 1)
def _dump_view(view):
    return dict(op = view.op)

@camel_registry.loader('bead-calibration-view', version = 1)
def _load_view(data, version):
    return BeadCalibrationWorkflowView(**data)