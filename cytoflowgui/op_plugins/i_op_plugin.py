#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflowgui.op_plugins.i_op_plugin
----------------------------------

"""

from traits.api import Interface, Constant, List
from envisage.api import Plugin, ExtensionPoint

OP_PLUGIN_EXT = 'cytoflow.op_plugins'

class IOperationPlugin(Interface):
    """
    Attributes
    ----------
    
    id : Constant
        The Envisage ID used to refer to this plugin
        
    operation_id : Constant
        Same as the ``id`` attribute of the IOperation this plugin wraps.
        
    name : Constant
        The operation's ``short`` name - for menus and toolbar tool tips
    """

    operation_id = Constant
    name = Constant

    def get_operation(self):
        """
        Makes an instance of the `IWorkflowOperation` that this plugin wraps.
        
        Returns
        -------
        `IWorkflowOperation`
        """
        
    def get_handler(self, model):
        """
        Makes an instance of a Controller for the operation.  
        
        Parameters
        ----------
        model : IWorkflowOperation
            The model that this handler handles.
        
        Returns
        -------
        `traitsui.handler.Controller`
        """

    def get_icon(self):
        """
        Gets the icon for this operation.
        
        Returns
        -------
        `pyface.i_image_resource.IImageResource`
            The SVG icon
        """
        
        
    def get_help(self):
        """
        Gets the HTML help text for this plugin, deriving the filename from the class name.
        Probably best to use the default implementation in `cytoflowgui.op_plugins.op_plugin_base.PluginHelpMixin`
        
         
        Returns
        -------
        string
            The HTML help, in a single string.
        """      
        
        
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        """
        Gets the `envisage` plugin for this operation (usually `self`).
        
        Returns
        -------
        `envisage.plugin.Plugin`
            the plugin instance
        """
        

class OpPluginManager(Plugin):
    op_plugins = ExtensionPoint(List(IOperationPlugin), OP_PLUGIN_EXT)
    id = "cytoflow.op_plugin_manager"
