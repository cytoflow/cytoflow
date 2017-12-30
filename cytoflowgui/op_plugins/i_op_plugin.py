#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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

import os
from textwrap import dedent

from pyface.qt import QtGui

from traits.api import (Interface, Str, HasTraits, Event, Instance, Property, 
                        on_trait_change, HTML)
from traitsui.api import Group, Item
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.workflow_item import WorkflowItem

OP_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.op_plugins'


class IOperationPlugin(Interface):
    """
    Attributes
    ----------
    
    id : Str
        The Envisage ID used to refer to this plugin
        
    operation_id : Str
        Same as the "id" attribute of the IOperation this plugin wraps.
        
    short_name : Str
        The operation's "short" name - for menus and toolbar tool tips
        
    menu_group : Str
        If we were to put this op in a menu, what submenu to use?
        Not currently used.
    """

    operation_id = Str
    short_name = Str
    menu_group = Str

    def get_operation(self):
        """
        Return an instance of the IOperation that this plugin wraps, along
        with the factory for the handler
        """

    def get_icon(self):
        """
        
        """
        
class PluginHelpMixin(HasTraits):
    
    _cached_help = HTML
    
    def get_help(self):
        if self._cached_help == "":
            current_dir = os.path.abspath(__file__)
            help_dir = os.path.split(current_dir)[0]
            help_dir = os.path.split(help_dir)[0]
            help_dir = os.path.join(help_dir, "help")
            
            op = self.get_operation()
            help_file = None
            for klass in op.__class__.__mro__:
                mod = klass.__module__
                mod_html = mod + ".html"
                
                h = os.path.join(help_dir, mod_html)
                if os.path.exists(h):
                    help_file = h
                    break
                
            with open(help_file, encoding = 'utf-8') as f:
                self._cached_help = f.read()
                
        return self._cached_help
                        

class PluginOpMixin(HasTraits):
    # there are a few pieces of metadata that determine which traits get
    # copied between processes and when.  if a trait has "status = True",
    # it is only copied from the remote process to the local one.
    # this is for traits that report an operation's status.  if a trait
    # has "estimate = True", it is copied local --> remote but the workflow
    # item IS NOT UPDATED in real-time.  these are for traits that are used
    # for estimating other parameters, which is assumed to be a very slow 
    # process.  if a trait has "fixed = True", then it is assigned when the
    # operation is first copied over AND NEVER SUBSEQUENTLY CHANGED.
    
    # causes this operation's estimate() function to be called
    do_estimate = Event
    
    # transmit some changing status back to the workflow
    changed = Event
    
                
    def should_apply(self, changed):
        """
        Should the owning WorkflowItem apply this operation when certain things
        change?  `changed` can be:
         - Changed.OPERATION -- the operation's parameters changed
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
        """
        return True

    
    def should_clear_estimate(self, changed):
        """
        Should the owning WorkflowItem clear the estimated model by calling
        op.clear_estimate()?  `changed` can be:
         - Changed.ESTIMATE -- the parameters required to call 'estimate()' (ie
            traits with estimate = True metadata) have changed
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         """
        return True

          
shared_op_traits = Group(Item('context.estimate_warning',
                              label = 'Warning',
                              resizable = True,
                              visible_when = 'context.estimate_warning',
                              editor = ColorTextEditor(foreground_color = "#000000",
                                                       background_color = "#ffff99")),
                         Item('context.estimate_error',
                               label = 'Error',
                               resizable = True,
                               visible_when = 'context.estimate_error',
                               editor = ColorTextEditor(foreground_color = "#000000",
                                                        background_color = "#ff9191")),
                         Item('context.op_warning',
                              label = 'Warning',
                              resizable = True,
                              visible_when = 'context.op_warning',
                              editor = ColorTextEditor(foreground_color = "#000000",
                                                       background_color = "#ffff99")),
                         Item('context.op_error',
                               label = 'Error',
                               resizable = True,
                               visible_when = 'context.op_error',
                               editor = ColorTextEditor(foreground_color = "#000000",
                                                        background_color = "#ff9191")))

        
class OpHandlerMixin(HasTraits):
    """
    Useful bits for operation handlers.
    """
    
    context = Instance(WorkflowItem)
    
    conditions_names = Property(depends_on = "context.conditions")
    previous_conditions_names = Property(depends_on = "context.previous_wi.conditions")
    statistics_names = Property(depends_on = "context.statistics")
    previous_statistics_names = Property(depends_on = "context.previous_wi.statistics")
    
    # MAGIC: gets value for property "conditions_names"
    def _get_conditions_names(self):
        if self.context and self.context.conditions:
            return list(self.context.conditions.keys())
        else:
            return []
    
    # MAGIC: gets value for property "previous_conditions_names"
    def _get_previous_conditions_names(self):
        if self.context and self.context.previous_wi and self.context.previous_wi.conditions:
            return list(self.context.previous_wi.conditions.keys())
        else:
            return []
        
    # MAGIC: gets value for property "statistics_names"
    def _get_statistics_names(self):
        if self.context and self.context.statistics:
            return list(self.context.statistics.keys())
        else:
            return []
        
    # MAGIC: gets value for property "previous_statistics_names"
    def _get_previous_statistics_names(self):
        if self.context and self.context.previous_wi and self.context.previous_wi.statistics:
            return list(self.context.previous_wi.statistics.keys())
        else:
            return []
        
    @on_trait_change('context.op_error_trait', 
                     dispatch = 'ui', 
                     post_init = True)
    def _op_trait_error(self):
        
        # check if we're getting called from the local or remote process
        if self.info is None or self.info.ui is None:
            return
        
        for ed in self.info.ui._editors:
            if ed.name == self.context.op_error_trait:
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
