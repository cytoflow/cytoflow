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
Created on Mar 15, 2015

@author: brian
"""
from traits.api import Interface, Str, HasTraits, Event, on_trait_change
from traitsui.api import Group, Item
from cytoflowgui.workflow import WorkflowItem
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.util import DelayedEvent

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

class PluginOpMixin(HasTraits):
    changed = DelayedEvent(delay = 0.2)
    
    # there are a few pieces of metadata that determine which traits get
    # copied between processes and when.  if a trait has "status = True",
    # it is only copied from the remote process to the local one.
    # this is for traits that report an operation's status.  if a trait
    # has "estimate = True", it is copied local --> remote but the workflow
    # item IS NOT UPDATED in real-time.  these are for traits that are used
    # for estimating other parameters, which is assumed to be a very slow 
    # process.  if a trait has "fixed = True", then it is assigned when the
    # operation is first copied over AND NEVER SUBSEQUENTLY CHANGED.
    
    # why can't we just put this in a workflow listener?  it's because
    # we sometimes need to override it on a per-module basis
    
    @on_trait_change("+status", post_init = True)
    def _status_changed(self):
        self.changed = "status"
        
    @on_trait_change("-status", post_init = True)
    def _api_changed(self, obj, name, old, new):
        if not obj.trait(name).transient:
            if obj.trait(name).estimate:
                self.changed = "estimate"
            else:
                self.changed = "api"
            
shared_op_traits = Group(Item('context.op_warning',
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
    This used to hold properties for dynamically updated metadata lists ....
    but now those are updated elsewhere.  Keep this around in case a mixin
    becomes useful again.
    """
    
    pass
