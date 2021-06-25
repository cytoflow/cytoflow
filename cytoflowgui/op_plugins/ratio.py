#!/usr/bin/env python3.4
# coding: latin-1

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

from traits.api import provides
from traitsui.api import (View, Item, TextEditor, EnumEditor)
from pyface.api import ImageResource
from envisage.api import Plugin, contributes_to
                       
from ..workflow.operations import RatioWorkflowOp

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT 
from .op_plugin_base import OpHandler, PluginHelpMixin, shared_op_traits_view

class RatioHandler(OpHandler):
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False, placeholder = "None")),
             Item('numerator',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "Numerator"),
             Item('denominator',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "Denominator"),
             shared_op_traits_view) 
    

@provides(IOperationPlugin)
class RatioPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.op_plugins.ratio'
    operation_id = 'edu.mit.synbio.cytoflow.operations.ratio'
    view_id = None

    short_name = "Ratio"
    menu_group = "Data"
    
    def get_operation(self):
        return RatioWorkflowOp()

    def get_handler(self, model, context):
        return RatioHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('ratio')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self

