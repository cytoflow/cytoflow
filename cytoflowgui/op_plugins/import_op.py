#!/usr/bin/env python2.7
from traits.has_traits import on_trait_change

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

"""
Created on Mar 15, 2015

@author: brian
"""
# 
# if __name__ == '__main__':
#     from traits.etsconfig.api import ETSConfig
#     ETSConfig.toolkit = 'qt4'
# 
#     import os
#     os.environ['TRAITS_DEBUG'] = "1"

from traitsui.api import View, Item, Controller, TextEditor
from traits.api import Button, Property, cached_property, provides, Callable, \
                       Bool
from pyface.api import OK as PyfaceOK
from envisage.api import Plugin, contributes_to

import cytoflow.utility as util
from cytoflow import ImportOp
from cytoflow.operations.i_operation import IOperation
                       
from cytoflowgui.import_dialog import ExperimentDialog
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.toggle_button import ToggleButtonEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin


class ImportHandler(Controller, OpHandlerMixin):
    """
    A WorkflowItem that handles importing data and making a new Experiment
    """
    
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
class ImportPluginOp(ImportOp, PluginOpMixin):
    handler_factory = Callable(ImportHandler, transient = True)
    ret_events = util.PositiveInt(0, allow_zero = True, status = True)
    
    def apply(self, experiment = None):
        ret = super(ImportPluginOp, self).apply(experiment = experiment)
        self.ret_events = len(ret.data)

        return ret
    
            
@provides(IOperationPlugin)
class ImportPlugin(Plugin):
    """
    class docs
    """
    
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