#!/usr/bin/env python3.4

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

from traitsui.api import (View, Item, Controller, TextEditor, ButtonEditor, 
                          InstanceEditor, HGroup, VGroup, Label)
from traits.api import (Button, Property, cached_property, provides, Callable, 
                        HasTraits, String, List, on_trait_change, Instance,
                        Bool, Dict, Str, Enum)

from envisage.api import Plugin, contributes_to

import cytoflow.utility as util
from cytoflow import Tube, ImportOp
from cytoflow.operations.i_operation import IOperation
                       
from cytoflowgui.vertical_list_editor import VerticalListEditor
from cytoflowgui.serialization import camel_registry, traits_repr
from cytoflowgui.import_dialog import ExperimentDialogModel, ExperimentDialogHandler, ValidPythonIdentifier
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.workflow import Changed

ImportOp.__repr__ = Tube.__repr__ = traits_repr

class Channel(HasTraits):
    channel = String
    name = ValidPythonIdentifier
    
    default_view = View(HGroup(Item('channel', style = 'readonly', show_label = False),
                               Item(label = '-->'),
                               Item('name',
                                    editor = TextEditor(auto_set = False), 
                                    show_label = False)))


class ImportHandler(OpHandlerMixin, Controller):
    
    setup_event = Button(label="Set up experiment...")
    reset_channels = Button(label = "Reset channel names")
    samples = Property(depends_on = 'model.tubes', status = True)
    dialog_model = Instance(ExperimentDialogModel)
        
    def default_traits_view(self):
        return View(VGroup(Label(label = "Channels",
                                   visible_when = 'model.tubes' ),
                           Item('object.channels_list',
                                editor = VerticalListEditor(editor = InstanceEditor(),
                                                            style = 'custom',
                                                            mutable = False,
                                                            deletable = True),
                                show_label = False),
                           Item('handler.reset_channels',
                           show_label = False),
                    visible_when = 'object.channels_list'),
                    Item('object.events',
                         editor = TextEditor(auto_set = False,
                                             format_func = lambda x: "" if x == None else str(x)),
                         label="Events per\nsample"),
                    Item('handler.samples', label='Samples', style='readonly'),
                    Item('ret_events', label='Events', style='readonly'),
                    Item('handler.setup_event', show_label=False),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Import!"),
                         show_label = False),
                    shared_op_traits)
        
    def _setup_event_fired(self):
        """
        Import data; save as self.result
        """

        handler = ExperimentDialogHandler(model = ExperimentDialogModel(),
                                          import_op = self.model)
        
        handler.edit_traits(kind = 'livemodal') 
                
    def _reset_channels_fired(self):
        self.model.reset_channels()
        
        
    @cached_property
    def _get_samples(self):
        return len(self.model.tubes)
    
    
    @on_trait_change('model.events', post_init = True)
    def _events_changed(self):
        if not self.dialog_model:
            return
        
        ret_events = 0
        for tube in self.dialog_model.tubes:
            if self.model.events:
                ret_events += min(tube.metadata['$TOT'], self.model.events)
            else:
                ret_events += tube.metadata['$TOT']
        
        self.model.ret_events = ret_events
        

@provides(IOperation)
class ImportPluginOp(PluginOpMixin, ImportOp):
    handler_factory = Callable(ImportHandler, transient = True)
    
    original_channels = List(Str, estimate = True)
    channels_list = List(Channel, estimate = True)
    events = util.CIntOrNone(None, estimate = True)
    tubes = List(Tube, estimate = True)
    channels = Dict(Str, Str, transient = True)
    name_metadata =  Enum(None, "$PnN", "$PnS", estimate = True)
    
    ret_events = util.PositiveInt(0, allow_zero = True, status = True)
    do_import = Bool(False)
    
    def reset_channels(self):
        self.channels_list = [Channel(channel = x, name = util.sanitize_identifier(x)) for x in self.original_channels]
    

    @on_trait_change('channels_list_items, channels_list.+')
    def _channels_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('channels_list', self.channels_list))


    @on_trait_change('tubes_items, tubes:+')
    def _tubes_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('tubes', self.tubes))        


    def estimate(self, _):
        self.do_import = False
        self.do_import = True
        
        
    def apply(self, experiment = None, metadata_only = False, force = False):
        if self.do_import or force:
            self.channels = {c.channel : c.name for c in self.channels_list}
            ret = super().apply(experiment = experiment, metadata_only = metadata_only)
            
            self.ret_events = len(ret.data)
            return ret
        else:
            if not self.tubes:
                raise util.CytoflowOpError(None, 'Click "Set up experiment", '
                                                 'then "Import!"')
            raise util.CytoflowOpError(None, "Press 'Import!'")
        
        
    def clear_estimate(self):
        self.do_import = False

    
    def get_notebook_code(self, idx):
        op = ImportOp()
        op.copy_traits(self, op.copyable_trait_names())
        op.channels = {c.channel : c.name for c in self.channels_list}
        
        return dedent("""
            op_{idx} = {repr}
            
            ex_{idx} = op_{idx}.apply()"""
            .format(repr = repr(op),
                    idx = idx))
        

@provides(IOperationPlugin)
class ImportPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.import'
    operation_id = 'edu.mit.synbio.cytoflow.operations.import'

    short_name = "Import data"
    menu_group = "TOP"
    
    def get_operation(self):
        return ImportPluginOp()
    
    def get_icon(self):
        return None
        
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
### Serialization
    
@camel_registry.dumper(ImportPluginOp, 'import', version = 3)
def _dump_op(op):
    return dict(tubes = op.tubes,
                conditions = op.conditions,
                channels_list = op.channels_list,
                events = op.events,
                name_metadata = op.name_metadata)
    


@camel_registry.dumper(ImportPluginOp, 'import', version = 2)
def _dump_op_v2(op):
    return dict(tubes = op.tubes,
                conditions = op.conditions,
                channels = op.channels,
                events = op.events,
                name_metadata = op.name_metadata)

@camel_registry.dumper(ImportPluginOp, 'import', version = 1)
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
    return ImportPluginOp(**data)


@camel_registry.loader('import', version = 3)
def _load_op_v3(data, version):
    return ImportPluginOp(**data)


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

