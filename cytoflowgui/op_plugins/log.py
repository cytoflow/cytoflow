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

"""
Created on Feb 24, 2015

@author: brian
"""

from traits.api import provides, Callable
from traitsui.api import Controller, View, Item, CheckListEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import LogTransformOp

from cytoflowgui.op_plugins.i_op_plugin \
    import OpHandlerMixin, IOperationPlugin, OP_PLUGIN_EXT, PluginOpMixin, shared_op_traits

class LogHandler(Controller, OpHandlerMixin):
    """
    classdocs
    """
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channels',
                         editor = CheckListEditor(name='handler.previous_channels',
                                                  cols = 2),
                         style = 'custom'),
                    shared_op_traits)
        
class LogTransformPluginOp(LogTransformOp, PluginOpMixin):
    handler_factory = Callable(LogHandler)
    
@provides(IOperationPlugin)
class LogPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.log'
    operation_id = 'edu.mit.synbio.cytoflow.operations.log'
    
    short_name = "Log"
    menu_group = "Transformations"
     
    def get_operation(self):
        return LogTransformPluginOp()
    
    def get_default_view(self):
        return None
    
    def get_icon(self):
        return ImageResource('log')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

    
        