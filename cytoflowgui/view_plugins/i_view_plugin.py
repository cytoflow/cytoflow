#!/usr/bin/env python3.8
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

"""
Created on Mar 15, 2015

@author: brian
"""

from traits.api import Interface, Constant, List
from envisage.api import Plugin, ExtensionPoint

VIEW_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.view_plugins'

class IViewPlugin(Interface):
    """
    
    Attributes
    ----------
    
    id : Str
        The envisage ID used to refer to this plugin
        
    view_id : Str
        Same as the "id" attribute of the IView this plugin wraps
        Prefix: edu.mit.synbio.cytoflowgui.view
        
    short_name : Str
        The view's "short" name - for menus, toolbar tips, etc.
    """
    
    
    id = Constant
    view_id = Constant
    short_name = Constant


    def get_view(self):
        """
        Gets the IView instance that this plugin wraps.
        
        Returns
        -------
        :class:`IView`
            An instance of the view that this plugin wraps
        """
        
        
    def get_handler(self, model):
        """
        Gets an instance of the handler for this view or params model.
        
        NOTE: You have to check to see what the class of `model` is, and return
        an appropriate handler!
        
        Parameters
        ----------
        model : IWorkflowView
            The model to associate with this handler.
            
        context : WorkflowItem
            The WorkflowItem that this model is a part of.
            
        Returns
        -------
        :class:`traitsui.Controller`
        """
        

    def get_icon(self):
        """
        Returns an icon for this plugin
        
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
        
        
    def get_plugin(self):
        """
        Returns an instance of :class:`envisage.Plugin` implementing
        :class:`.IViewPlugin`.  Usually returns ``self``.
        
        Returns
        -------
        :class:`envisage.Plugin`
        """
        
              
class ViewPluginManager(Plugin):
    view_plugins = ExtensionPoint(List(IViewPlugin), VIEW_PLUGIN_EXT)
