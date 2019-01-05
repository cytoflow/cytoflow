#!/usr/bin/env python3.4
# coding: latin-1

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

'''
Ratio
-----

Adds a new "channel" to the workflow, where the value of the channel is the
ratio of two other channels.

.. object:: Name

    The name of the new channel.
    
.. object:: Numerator

    The numerator for the ratio.
    
.. object:: Denominator

    The denominator for the ratio.
    
'''

from traits.api import provides, Callable
from traitsui.api import View, Item, EnumEditor, Controller, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.operations.ratio import RatioOp

from cytoflowgui.op_plugins.i_op_plugin \
    import IOperationPlugin, OpHandlerMixin, PluginOpMixin, OP_PLUGIN_EXT, shared_op_traits, PluginHelpMixin

from cytoflowgui.serialization import camel_registry, traits_repr, dedent

RatioOp.__repr__ = traits_repr

class RatioHandler(OpHandlerMixin, Controller):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('numerator',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "Numerator"),
                    Item('denominator',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "Denominator"),
                    shared_op_traits) 

    
class RatioPluginOp(PluginOpMixin, RatioOp):
    handler_factory = Callable(RatioHandler, transient = True)
    
    def get_notebook_code(self, idx):
        op = RatioOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))

@provides(IOperationPlugin)
class RatioPlugin(Plugin, PluginHelpMixin):

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
    
### Serialization
@camel_registry.dumper(RatioPluginOp, 'ratio', version = 1)
def _dump(op):
    return dict(name = op.name,
                numerator = op.numerator,
                denominator = op.denominator)
    
@camel_registry.loader('ratio', version = 1)
def _load(data, version):
    return RatioPluginOp(**data)