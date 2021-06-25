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


from traits.api import Interface, Constant
from envisage.api import contributes_to

OP_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.op_plugins'

class IOperationPlugin(Interface):
    """
    Attributes
    ----------
    
    id : Constant
        The Envisage ID used to refer to this plugin
        
    operation_id : Constant
        Same as the "id" attribute of the IOperation this plugin wraps.
        
    short_name : Constant
        The operation's "short" name - for menus and toolbar tool tips
    """

    operation_id = Constant
    short_name = Constant

    def get_operation(self):
        """
        Makes an instance of the IWorkflowOperation that this plugin wraps.
        
        Returns
        -------
        :class:`.IWorkflowOperation`
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
        :class:`traitsui.Controller`
        """

    def get_icon(self):
        """
        Gets the icon for this operation.
        
        Returns
        -------
        :class:`pyface.ImageResource`
            The SVG icon
        """
        
        
    def get_help(self):
        """
        Gets the HTML help text for this plugin, deriving the filename from the class name.
        Probably best to use the default implementation in :class:`PluginHelpMixin`
        
         
        Returns
        -------
        string
            The HTML help, in a single string.
        """      
        
        
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        """
        Gets the :mod:`envisage` plugin for this operation (usually `self`).
        
        Returns
        -------
        :class:`envisage.Plugin`
            the plugin instance
        """
        
