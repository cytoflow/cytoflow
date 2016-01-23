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

from traits.api import provides, Callable, on_trait_change
from traitsui.api import Controller, View, Item, CheckListEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import LogicleTransformOp

from cytoflowgui.op_plugins.i_op_plugin \
    import OpHandlerMixin, IOperationPlugin, OP_PLUGIN_EXT, PluginOpMixin
from cytoflowgui.color_text_editor import ColorTextEditor

class LogicleHandler(Controller, OpHandlerMixin):
    """
    classdocs
    """
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.W'),
                    Item('object.M'),
                    Item('object.A'),
                    Item('object.r'),
                    Item('object.channels',
                         editor = CheckListEditor(name='handler.previous_channels',
                                                  cols = 2),
                         style = 'custom'),
                    Item('handler.wi.error',
                         label = 'Error',
                         visible_when = 'handler.wi.error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191",
                                                  word_wrap = True)))
        
    def setattr(self, info, obj, name, value):
        super(LogicleHandler, self).setattr(info, obj, name, value)
        #Controller.setattr(self, info, object, name, value)
        
class LogicleTransformPluginOp(LogicleTransformOp, PluginOpMixin):
    handler_factory = Callable(LogicleHandler)
    
    @on_trait_change('channels[]')
    def _on_channels_changed(self):
        for channel in self.channels:
            if channel not in self.W:
                self.W[channel] = 0.5
            if channel not in self.A:
                self.A[channel] = 0.0
    
@provides(IOperationPlugin)
class LogiclePlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.logicle'
    operation_id = 'edu.mit.synbio.cytoflow.operations.logicle'
    
    short_name = "Logicle"
    menu_group = "Transformations"
     
    def get_operation(self):
        return LogicleTransformPluginOp()
    
    def get_default_view(self):
        return None
    
    def get_icon(self):
        return ImageResource('logicle')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

    
        