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

    .. image:: images/import.png

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

from traits.api import (Button, Property, cached_property, 
                        Instance, provides, observe, Event)
from traitsui.api import (View, Item, Controller, TextEditor, ButtonEditor, 
                          HGroup, VGroup, Label)

from envisage.api import Plugin, contributes_to
                       
from cytoflowgui.editors import VerticalListEditor, InstanceHandlerEditor
from cytoflowgui.import_dialog import ExperimentDialogModel, ExperimentDialogHandler

from ..workflow.operations import ImportWorkflowOp

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT 
from .op_plugin_base import OpHandler, PluginHelpMixin, shared_op_traits_view


class ChannelHandler(Controller):
    default_view = View(HGroup(Item('channel', style = 'readonly', show_label = False),
                               Item(label = '-->'),
                               Item('name',
                                    editor = TextEditor(auto_set = False), 
                                    show_label = False)))
    

class ImportHandler(OpHandler):
    setup_event = Button(label="Set up experiment...")
    reset_channels_event = Event()
    samples = Property(depends_on = 'model.tubes', status = True)
    dialog_model = Instance(ExperimentDialogModel)
        
    operation_traits_view = \
        View(VGroup(Label(label = "Channels",
                          visible_when = 'model.tubes' ),
                    Item('object.channels_list',
                         editor = VerticalListEditor(editor = InstanceHandlerEditor(handler_factory = ChannelHandler,
                                                                                    view = "default_view"),
                                                     style = 'custom',
                                                     mutable = False,
                                                     deletable = True),
                         show_label = False),
                    Item('handler.reset_channels_event',
                         editor = ButtonEditor(value = True,
                                               label = "Reset channel names"),
                    show_label = False),
             visible_when = 'object.channels_list'),
             Item('object.events',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None",
                                      format_func = lambda x: "" if x is None else str(x)),
                  label="Events per\nsample"),
             Item('handler.samples', label='Samples', style='readonly'),
             Item('ret_events', label='Events', style='readonly'),
             Item('handler.setup_event',
                  editor = ButtonEditor(value = True, label = "Set up experiment..."),
                  show_label=False),
             Item('object.do_estimate',
                  editor = ButtonEditor(value = True, label = "Import!"),
                  show_label = False),
             shared_op_traits_view)
     
    @observe('setup_event')   
    def _on_setup(self, event):
        """
        Import data; save as self.result
        """

        handler = ExperimentDialogHandler(model = ExperimentDialogModel(),
                                          import_op = self.model)
        
        handler.edit_traits(kind = 'livemodal') 
    
    @observe('reset_channels_event')    
    def _on_reset_channels(self, _):
        self.model.reset_channels()
        
    @cached_property
    def _get_samples(self):
        return len(self.model.tubes)
    
    @observe('model.events', post_init = True)
    def _events_changed(self, _):
        if not self.dialog_model:
            return
        
        ret_events = 0
        for tube in self.dialog_model.tubes:
            if self.model.events:
                ret_events += min(tube.metadata['$TOT'], self.model.events)
            else:
                ret_events += tube.metadata['$TOT']
        
        self.model.ret_events = ret_events
        

@provides(IOperationPlugin)
class ImportPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.import'
    operation_id = 'edu.mit.synbio.cytoflow.operations.import'
    view_id = None

    short_name = "Import data"
    menu_group = "TOP"
    
    def get_operation(self):
        return ImportWorkflowOp()
    
    def get_handler(self, model, context):
        return ImportHandler(model = model, context = context)
    
    def get_icon(self):
        return None
        
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

