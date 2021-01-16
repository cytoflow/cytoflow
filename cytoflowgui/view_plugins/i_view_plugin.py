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

"""
Created on Mar 15, 2015

@author: brian
"""

import os

from pyface.qt import QtGui

from traits.api import (Interface, HasTraits,
                        Property, on_trait_change, HTML, Constant)
from traitsui.api import View, Item, HGroup, TextEditor, InstanceEditor

import cytoflow.utility as util

from cytoflowgui.flow_task_pane import TabListEditor

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
    
    id = Constant("FIXME")
    view_id = Constant("FIXME")
    short_name = Constant("FIXME")

    def get_view(self):
        """
        Gets the IView instance that this plugin wraps.
        
        Returns
        -------
        :class:`IView`
            An instance of the view that this plugin wraps
        """
        
    def get_view_handler(self, model):
        """
        Gets an instance of the handler for this view.
        
        Parameters
        ----------
        model : IWorkflowView
            The model to associate with this handler.
            
        Returns
        -------
        :class:`traitsui.Controller`
        """
        
    def get_params_handler(self, model):
        """
        Gets an instance of the handler for this view's parameters
        
        Parameters
        ----------
        model : IWorkflowViewParameters
            The model to associate with this handler
            
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
        
    def get_plugin(self):
        """
        Returns an instance of :class:`envisage.Plugin` implementing
        :class:`.IViewPlugin`.  Usually returns ``self``.
        
        Returns
        -------
        :class:`envisage.Plugin`
        """
        
class PluginHelpMixin(HasTraits):
    """
    A mixin to get online HTML help for a class.  It determines the HTML
    path name from the class name.
    """
    
    _cached_help = HTML
    
    def get_help(self):
        """
        Gets the HTML help for this class.
        
        Returns
        -------
        string
            The HTML help in a single string.
        """
        
        if self._cached_help == "":
            current_dir = os.path.abspath(__file__)
            help_dir = os.path.split(current_dir)[0]
            help_dir = os.path.split(help_dir)[0]
            help_dir = os.path.join(help_dir, "help")
             
            view = self.get_view()
            help_file = None
            for klass in view.__class__.__mro__:
                mod = klass.__module__
                mod_html = mod + ".html"
                 
                h = os.path.join(help_dir, mod_html)
                if os.path.exists(h):
                    help_file = h
                    break
                 
            with open(help_file, encoding = 'utf-8') as f:
                self._cached_help = f.read()
                 
        return self._cached_help
    
        
                        
# class PluginViewMixin(HasTraits):
#     handler = Instance(Handler, transient = True)    
#     
#     # transmit some change back to the workflow
#     changed = Event
    

        

class ViewHandlerMixin(HasTraits):
    """
    Useful bits for view handlers.
    """
    
    # the view for the current plot
    current_plot_view = \
        View(
            HGroup(
                Item('plot_names_by',
                     editor = TextEditor(),
                     style = "readonly",
                     show_label = False),
                Item('current_plot',
                     editor = TabListEditor(name = 'plot_names'),
                     style = 'custom',
                     show_label = False)))
        
    plot_params_traits = View(Item('plot_params',
                                   editor = InstanceEditor(),
                                   style = 'custom',
                                   show_label = False))
    
    #context = Instance(WorkflowItem)
    
    conditions_names = Property(depends_on = "context.conditions")
    previous_conditions_names = Property(depends_on = "context.previous_wi.conditions")
    statistics_names = Property(depends_on = "context.statistics")
    numeric_statistics_names = Property(depends_on = "context.statistics")
    
    # MAGIC: gets value for property "conditions_names"
    def _get_conditions_names(self):
        if self.context and self.context.conditions:
            return sorted(list(self.context.conditions.keys()))
        else:
            return []
    
    # MAGIC: gets value for property "previous_conditions_names"
    def _get_previous_conditions_names(self):
        if self.context and self.context.previous_wi and self.context.previous_wi.conditions:
            return sorted(list(self.context.previous_wi.conditions.keys()))
        else:
            return []
        
    # MAGIC: gets value for property "statistics_names"
    def _get_statistics_names(self):
        if self.context and self.context.statistics:
            return sorted(list(self.context.statistics.keys()))
        else:
            return []

    # MAGIC: gets value for property "numeric_statistics_names"
    def _get_numeric_statistics_names(self):
        if self.context and self.context.statistics:
            return sorted([x for x in list(self.context.statistics.keys())
                                 if util.is_numeric(self.context.statistics[x])])
        else:
            return []

    @on_trait_change('context.view_error_trait', 
                     dispatch = 'ui', 
                     post_init = True)
    def _view_trait_error(self):
        
        # check if we're getting called on the local or remote process
        if self.info is None or self.info.ui is None:
            return
        
        for ed in self.info.ui._editors:  
                          
            if ed.name == self.context.view_error_trait:
                err_state = True
            else:
                err_state = False

            if not ed.label_control:
                continue
            
            item = ed.label_control
            
            if not err_state and not hasattr(item, '_ok_color'):
                continue
            
            pal = QtGui.QPalette(item.palette())  # @UndefinedVariable
            
            if err_state:
                setattr(item, 
                        '_ok_color', 
                        QtGui.QColor(pal.color(item.backgroundRole())))  # @UndefinedVariable
                pal.setColor(item.backgroundRole(), QtGui.QColor(255, 145, 145))  # @UndefinedVariable
                item.setAutoFillBackground(True)
                item.setPalette(pal)
            else:
                pal.setColor(item.backgroundRole(), item._ok_color)
                delattr(item, '_ok_color')
                item.setAutoFillBackground(False)
                item.setPalette(pal)
                
