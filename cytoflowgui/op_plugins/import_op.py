#!/usr/bin/env python3.4

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

"""
Import Files
------------

Import FCS files and associate them with experimental conditions (metadata.)

.. object:: Edit samples

    Open the sample editor dialog box.

.. object:: Random subsample

    For very large data sets, *Cytoflow*'s interactive operation may be too slow.
    By clicking **Random subsample**, you can tell *Cytoflow* to import a
    smaller number of events from each FCS file, which will make interactive
    data exploration much faster.  When you're done setting up your workflow,
    toggle **Random subsample** off to automatically re-run the workflow with
    the full data set.
    

..  object:: The import dialog

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
        
    .. object: Add condition
    
        Opens a dialog (see below) to add a new experimental condition.
        
    .. object: Remove condition
    
        Removes the currently selected condition (column) in the table.

    .. object:: The new condition dialog box

    
        .. image:: _images/condition.png
        
            
        .. object:: Condition name
        
            The name of the new condition.  The name must be a valid Python identifier:
            it must start with a letter or _, and contain only letters, numbers and _.
            
        .. object: Condition type
        
            The type of the new condition.  Allowed types are **Category**, **Number**
            and **True/False**.

"""
from textwrap import dedent

from traitsui.api import View, Item, Controller, TextEditor
from traits.api import Button, Property, cached_property, provides, Callable, \
                       Bool, on_trait_change
from pyface.api import OK as PyfaceOK
from envisage.api import Plugin, contributes_to

import cytoflow.utility as util
from cytoflow import Tube, ImportOp
from cytoflow.operations.i_operation import IOperation
                       
from cytoflowgui.serialization import camel_registry, traits_repr
from cytoflowgui.import_dialog import ExperimentDialog
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.toggle_button import ToggleButtonEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin

ImportOp.__repr__ = Tube.__repr__ = traits_repr

class ImportHandler(OpHandlerMixin, Controller):
    
    import_event = Button(label="Edit samples...")
    samples = Property(depends_on = 'model.tubes', status = True)

    coarse = Bool
    coarse_events = util.PositiveInt(0, allow_zero = True)
    
    def default_traits_view(self):
        return View(Item('handler.import_event',
                         show_label=False),
                    Item('handler.samples',
                         label='Samples',
                         style='readonly'),
                    Item('ret_events',
                         label='Events',
                         style='readonly'),
                    Item('handler.coarse',
                         label="Random subsample?",
                         show_label = False,
                         editor = ToggleButtonEditor()),
                    Item('object.events',
                         editor = TextEditor(auto_set = False),
                         label="Events per\nsample",
                         visible_when='handler.coarse == True'),
                    shared_op_traits)
        
    def _import_event_fired(self):
        """
        Import data; save as self.result
        """

        d = ExperimentDialog()

        # self.model is an instance of ImportPluginOp
        d.model.init_model(self.model)
            
        d.size = (550, 500)
        d.open()
        
        if d.return_code is not PyfaceOK:
            return
        
        d.model.update_import_op(self.model)
        
        d = None
        
    @cached_property
    def _get_samples(self):
        return len(self.model.tubes)
        
    @on_trait_change('coarse')    
    def _on_coarse_changed(self):
        if self.coarse:
            self.model.events = self.coarse_events
        else:
            self.coarse_events = self.model.events
            self.model.events = 0
        

@provides(IOperation)
class ImportPluginOp(PluginOpMixin, ImportOp):
    handler_factory = Callable(ImportHandler, transient = True)
    ret_events = util.PositiveInt(0, allow_zero = True, status = True)
    
    def apply(self, experiment = None):
        ret = super().apply(experiment = experiment)
        self.ret_events = len(ret.data)

        return ret
    
    
    def get_notebook_code(self, idx):
        op = ImportOp()
        op.copy_traits(self, op.copyable_trait_names())
        
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
    
@camel_registry.dumper(ImportPluginOp, 'import', version = 1)
def _dump_op(op):
    return dict(tubes = op.tubes,
                conditions = op.conditions,
                channels = op.channels,
                events = op.events,
                name_metadata = op.name_metadata)

@camel_registry.loader('import', version = 1)
def _load_op(data, version):
    return ImportPluginOp(**data)

@camel_registry.dumper(Tube, 'tube', version = 1)
def _dump_tube(tube):
    return dict(file = tube.file,
                conditions = tube.conditions)

@camel_registry.loader('tube', version = 1)
def _load_tube(data, version):
    return Tube(**data)
            