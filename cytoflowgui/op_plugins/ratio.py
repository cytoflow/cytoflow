#!/usr/bin/env python2.7
# coding: latin-1

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

from traits.api import provides, Callable
from traitsui.api import View, Item, EnumEditor, Controller, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.operations.ratio import RatioOp

from cytoflowgui.op_plugins.i_op_plugin \
    import IOperationPlugin, OpHandlerMixin, PluginOpMixin, OP_PLUGIN_EXT, shared_op_traits

class RatioHandler(OpHandlerMixin, Controller):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('numerator',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Numerator"),
                    Item('denominator',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Denominator"),
                    shared_op_traits) 

    
class RatioPluginOp(PluginOpMixin, RatioOp):
    handler_factory = Callable(RatioHandler, transient = True)

@provides(IOperationPlugin)
class RatioPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.ratio'
    operation_id = 'edu.mit.synbio.cytoflow.operations.ratio'

    short_name = "Ratio"
    menu_group = "Data"
    
    def get_operation(self):
        return RatioPluginOp()

    def get_icon(self):
        return ImageResource('ratio')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    