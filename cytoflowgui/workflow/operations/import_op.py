#!/usr/bin/env python3.8

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

from textwrap import dedent 

from traits.api import (HasTraits, String, List, Dict, Str, Enum, Instance, 
                        provides, BaseCStr, observe)

import cytoflow.utility as util
from cytoflow import Tube, ImportOp
                       
from cytoflowgui.workflow.serialization import camel_registry, traits_repr
from .operation_base import IWorkflowOperation, WorkflowOperation

ImportOp.__repr__ = Tube.__repr__ = traits_repr


class ValidPythonIdentifier(BaseCStr):

    info_text = 'a valid python identifier'
     
    def validate(self, obj, name, value):
        value = super(ValidPythonIdentifier, self).validate(obj, name, value)
        if util.sanitize_identifier(value) == value:
            return value 
         
        self.error(obj, name, value)
        

class Channel(HasTraits):
    channel = String
    name = ValidPythonIdentifier
  

@provides(IWorkflowOperation)
class ImportWorkflowOp(WorkflowOperation, ImportOp):   
    original_channels = List(Str)
    channels_list = List(Channel, estimate = True)
    events = util.CIntOrNone(None, estimate = True)
    tubes = List(Tube, estimate = True)
    conditions = Dict(Str, Str, estimate = True)
    channels = Dict(Str, Str, transient = True)
    name_metadata =  Enum(None, "$PnN", "$PnS", estimate = True)
    
    # how many events did we load?
    ret_events = util.PositiveInt(0, allow_zero = True, status = True, estimate_result = True, transient = True)
    
    # since we're actually calling super().apply() from self.estimate(), we need
    # to keep around the actual experiment that's returned
    ret_experiment = Instance('cytoflow.experiment.Experiment', transient = True, estimate_result = True)
    
    @observe('channels_list:items,channels_list:items.+type', post_init = True)
    def _on_controls_changed(self, _):
        self.changed = 'channels_list'
        
    def reset_channels(self):
        self.channels_list = [Channel(channel = x, name = util.sanitize_identifier(x)) for x in self.original_channels]

    def estimate(self, _):
        self.channels = {c.channel : c.name for c in self.channels_list}
        self.ret_experiment = super().apply()
        self.ret_events = len(self.ret_experiment)
        
    def apply(self, *args, **kwargs):
        if 'metadata_only' in kwargs:
            return super().apply(*args, **kwargs)
        elif self.ret_experiment:
            return self.ret_experiment
        elif not self.tubes:
            raise util.CytoflowOpError(None, 'Click "Set up experiment, then "Import!"')
        else:
            raise util.CytoflowOpError(None, 'Click "Import!"')
        
    def clear_estimate(self):
        self.ret_experiment = None
        self.ret_events = 0

    def get_notebook_code(self, idx):
        op = ImportOp()
        op.copy_traits(self, op.copyable_trait_names())
        op.channels = {c.channel : c.name for c in self.channels_list}
        
        return dedent("""
            op_{idx} = {repr}
            
            ex_{idx} = op_{idx}.apply()"""
            .format(repr = repr(op),
                    idx = idx))
    
### Serialization
    
@camel_registry.dumper(ImportWorkflowOp, 'import', version = 3)
def _dump_op(op):
    return dict(tubes = op.tubes,
                conditions = op.conditions,
                channels_list = op.channels_list,
                events = op.events,
                name_metadata = op.name_metadata)
    


@camel_registry.dumper(ImportWorkflowOp, 'import', version = 2)
def _dump_op_v2(op):
    return dict(tubes = op.tubes,
                conditions = op.conditions,
                channels = op.channels,
                events = op.events,
                name_metadata = op.name_metadata)

@camel_registry.dumper(ImportWorkflowOp, 'import', version = 1)
def _dump_op_v1(op):
    return dict(tubes = op.tubes,
                conditions = op.conditions,
                channels = op.channels,
                events = op.events,
                name_metadata = op.name_metadata,
                ret_events = op.ret_events)
    

@camel_registry.loader('import', version = 1)
@camel_registry.loader('import', version = 2)
def _load_op(data, version):
    data.pop('ret_events', None)
    channels = data.pop('channels', [])
    data['channels_list'] = [Channel(channel = k, name = v )
                             for k, v in channels.items()]
    return ImportWorkflowOp(**data)


@camel_registry.loader('import', version = 3)
def _load_op_v3(data, version):
    return ImportWorkflowOp(**data)


@camel_registry.dumper(Tube, 'tube', version = 1)
def _dump_tube(tube):
    return dict(file = tube.file,
                conditions = tube.conditions)


@camel_registry.loader('tube', version = 1)
def _load_tube(data, version):
    return Tube(**data)


@camel_registry.dumper(Channel, 'import-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                name = channel.name)
     
     
@camel_registry.loader('import-channel', version = 1)
def _load_channel(data, version):
    return Channel(**data)

