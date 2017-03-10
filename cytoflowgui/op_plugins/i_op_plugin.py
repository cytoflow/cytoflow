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
import logging

from traits.api import Interface, Str, HasTraits, on_trait_change, List, Property
from traitsui.api import Group, Item
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.util import DelayedEvent
from cytoflowgui.subset import ISubset

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
    
    subset_list = List(ISubset)
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change("subset_list.str", post_init = True)
    def _subset_changed(self, obj, name, old, new):
        self.changed = "api"
    
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
    # we sometimes need to override or supplement it on a per-module basis
        
    @on_trait_change("+", post_init = True)
    def _trait_changed(self, obj, name, old, new):
        logging.debug("PluginOpMixin::_trait_changed :: {}"
                      .format((obj, name, old, new)))
        if not obj.trait(name).transient:
            if obj.trait(name).status:
                self.changed = "status"
            elif obj.trait(name).estimate:
                self.changed = "estimate"
            else:
                self.changed = "api"
        
        if obj.trait(name).estimate_result:
            self.changed = "estimate_result"
                
    def should_apply(self, changed):
        """
        Should the owning WorkflowItem apply this operation when certain things
        change?  `changed` can be:
         - "operation" -- the operation's parameters changed
         - "prev_result" -- the previous WorkflowItem's result changed
         - "estimate_result" -- the results of calling "estimate" changed
        """
        return True
    
    def should_clear_estimate(self, changed):
        """
        Should the owning WorkflowItem clear the estimated model by calling
        op.clear_estimate()?  `changed` can be:
         - "estimate" -- the parameters required to call 'estimate()' (ie
            traits with estimate = True metadata) have changed
         - "prev_result" -- the previous WorkflowItem's result changed
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
    Useful bits for operation handlers.  Not currently used, but kept around
    in case it's useful some day in the future.
    """

