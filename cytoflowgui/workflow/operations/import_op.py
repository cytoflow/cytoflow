#!/usr/bin/env python3.4

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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

"""
Import Files
------------

Import FCS files and associate them with experimental conditions (metadata.)

.. object:: Channels

    Here, you can rename channels to use names that are more informative,
    or remove channels you don't need.  Names must be valid Python identifiers
    (must contain only letters, numbers and underscores and must start with
    a letter or underscore.)
    
.. object:: Reset channel names

    Reset the channels and channel names.

.. object:: Events per sample

    For very large data sets, *Cytoflow*'s interactive operation may be too slow.
    By setting **Events per sample**, you can tell *Cytoflow* to import a
    smaller number of events from each FCS file, which will make interactive
    data exploration much faster.  When you're done setting up your workflow,
    set **Events per sample** to empty or 0 and *Cytoflow* will re-run your
    workflow with the entire data set.
    
.. object:: Set up experiment....

    Open the sample editor dialog box.

..  object:: The sample editor dialog

    .. image:: _images/import.png

    Allows you to specify FCS files in the experiment, and
    the experimental conditions that each tube (or well) was subject to.
    
    .. note::
    
        You can select sort the table by clicking on a row header.
        
    .. note::
    
        You can select multiple entries in a column by clicking one, holding
        down *Shift*, and clicking another (to select a range); or, by holding
        down *Ctrl* and clicking multiple additional cells in the table.  If 
        multiple cells are selected, typing a value will update all of them.
        
    .. note:: 
    
        **Each tube must have a unique set of experimental conditions.**  If a
        tube's conditions are not unique, the row is red and you will not be
        able to click "OK".
    
    .. object:: Add tubes
    
        Opens a file selector to add tubes.
        
    .. object: Remove tubes
    
        Removes the currently selected tubes (rows) in the table.
        
    .. object: Add variable
    
        Adds a new experimental condition.  You can change the condition's
        type by changing the drop-down box.  You can remove a variable by 
        clicking the "X" next to its row.
        
    .. object: Import from CSV....
    
        Lets you import a set of tubes and experimental conditions from a CSV
        file.  The first row of the CSV must have variable names.  The first
        column of the CSV must be paths to FCS files (relative to the location
        of the CSV.)
        
        The variables are read in as "Categories", but you can change them 
        to other types and Cytoflow will attempt to convert them.

"""
from textwrap import dedent 

from traits.api import (HasTraits, String, List, Dict, Str, Enum, Instance, 
                        provides, BaseCStr)

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
class ImportWorkflowOp(ImportOp, WorkflowOperation):   
    original_channels = List(Str, estimate = True)
    channels_list = List(Channel, estimate = True)
    events = util.CIntOrNone(None, estimate = True)
    tubes = List(Tube, estimate = True)
    channels = Dict(Str, Str, transient = True)
    name_metadata =  Enum(None, "$PnN", "$PnS", estimate = True)
    
    # how many events did we load?
    ret_events = util.PositiveInt(0, allow_zero = True, status = True)
    
    # since we're actually calling super().apply() from self.estimate(), we need
    # to keep around the actual experiment that's returned
    ret_experiment = Instance('Experiment', transient = True)
    
#     do_import = Bool(False)
    
    def reset_channels(self):
        self.channels_list = [Channel(channel = x, name = util.sanitize_identifier(x)) for x in self.original_channels]
     
# 
#     @on_trait_change('channels_list_items, channels_list.+')
#     def _channels_changed(self, obj, name, old, new):
#         self.changed = (Changed.ESTIMATE, ('channels_list', self.channels_list))
# 
# 
#     @on_trait_change('tubes_items, tubes:+')
#     def _tubes_changed(self, obj, name, old, new):
#         self.changed = (Changed.ESTIMATE, ('tubes', self.tubes))        


#     def estimate(self, _):
#         self.do_import = False
#         self.do_import = True
#         

    def estimate(self, _):
        self.channels = {c.channel : c.name for c in self.channels_list}
        self.ret_experiment = super().apply()
        self.ret_events = len(self.ret_experiment
                              )
        
    def apply(self, _):
        if self.ret_experiment:
            return self.ret_experiment
        elif not self.tubes:
            raise util.CytoflowOpError(None, 'Click "Set up experiment, then "Import!"')
        else:
            raise util.CytoflowOpError(None, 'Click "Import!"')
            
        
        
#     def apply(self, experiment = None, metadata_only = False, force = False):
#         if self.do_import or force:
#             self.channels = {c.channel : c.name for c in self.channels_list}
#             ret = super().apply(experiment = experiment, metadata_only = metadata_only)
#             
#             self.ret_events = len(ret.data)
#             return ret
#         else:
#             if not self.tubes:
#                 raise util.CytoflowOpError(None, 'Click "Set up experiment", '
#                                                  'then "Import!"')
#             raise util.CytoflowOpError(None, "Press 'Import!'")
        
#         
#     def clear_estimate(self):
#         self.do_import = False

    
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

