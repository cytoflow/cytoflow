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

from pyface.qt import QtGui

from traits.api import (Interface, Constant, HasTraits, Event, Instance, Property, 
                        on_trait_change, HTML, Callable)
from traitsui.api import Group, Item
from envisage.api import contributes_to
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.workflow_item import WorkflowItem

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

    operation_id = Constant("FIXME")
    short_name = Constant("FIXME")

    def get_operation(self):
        """
        Makes an instance of the IOperation that this plugin wraps.
        
        Returns
        -------
        :class:`.IOperation`
        """

    def get_icon(self):
        """
        Gets the icon for this operation.
        
        Returns
        -------
        :class:`pyface.ImageResource`
            The icon, 32x32.
        """
        pass
        
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        """
        Gets the :mod:`envisage` plugin for this operation (usually `self`).
        
        Returns
        -------
        :class:`envisage.Plugin`
            the plugin instance
        """
        
class PluginHelpMixin(HasTraits):
    
    _cached_help = HTML
    
    def get_help(self):
        """
        Gets the HTML help for this module, deriving the filename from
        the class name.
        
        Returns
        -------
        string
            The HTML help, in a single string.
        """
        
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
                        

def unimplemented(*args, **kwargs):
    raise NotImplementedError("A plugin op must have a handler_factory trait")

class PluginOpMixin(HasTraits):
    """
    A mixin class that adds GUI support to an underlying :mod:`cytoflow`
    operation.
    
    Another common thing to do in the derived class is to override traits
    of the underlying class in order to add metadata that controls their
    handling by the workflow.  Currently, relevant metadata include:
    
      * **transient** - don't copy the trait between the local (GUI) process 
        and the remote (computation) process (in either direction).
     
      * **status** - only copy from the remote process to the local process,
        not the other way 'round.
       
      * **estimate** - copy from the local process to the remote process,
        but don't call :meth:`apply`.  (used for traits that are involved in
        estimating the operation's parameters.)
      
      * **fixed** - assigned when the operation is first created in the
        remote process *and never subsequently changed.*
    
    Attributes
    ----------
    
    handler_factory : Callable
        A callable that returns a GUI handler for the operation.  **MUST**
        be overridden in the derived class.
        
    do_estimate : Event
        Firing this event causes the operation's :meth:`estimate` method 
        to be called.
        
    changed : Event
        Used to transmit status information back from the operation to the
        workflow.  Set its value to a tuple (message, payload).  See 
        :class:`.workflow.Changed` for possible values of the message
        and their corresponding payloads.

    """
    
    handler_factory = Callable(unimplemented)
    
    # causes this operation's estimate() function to be called
    do_estimate = Event
    
    # transmit some changing status back to the workflow
    changed = Event
    
                
    def should_apply(self, changed, payload):
        """
        Should the owning WorkflowItem apply this operation when certain things
        change?  `changed` can be:
        
         - Changed.OPERATION -- the operation's parameters changed
         
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         
         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
        """
        return True

    
    def should_clear_estimate(self, changed, payload):
        """
        Should the owning WorkflowItem clear the estimated model by calling
        op.clear_estimate()?  `changed` can be:
        
         - Changed.ESTIMATE -- the parameters required to call :meth:`estimate` 
         (ie traits with ``estimate = True`` metadata) have changed
            
         - Changed.PREV_RESULT -- the previous :class:`.WorkflowItem`'s result changed
         """
        return True
    
    def get_notebook_code(self, idx):
        """
        Return Python code suitable for a Jupyter notebook cell that runs this
        operation.
        
        Parameters
        ----------
        idx : integer
            The index of the :class:`.WorkflowItem` that holds this operation.
            
        Returns
        -------
        string
            The Python code that calls this module.
        """
        raise NotImplementedError("GUI plugins must override get_notebook_code()")

          
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
    
    # the default traits view
    def default_traits_view(self):
        """
        Gets the default :class:`traits.View` for an operation.
        
        Returns
        -------
        traits.View
            The view for an operation.
        """
        
        raise NotImplementedError("Op handlers must override 'default_traits_view")
    
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
        
    # MAGIC: gets value for property "previous_statistics_names"
    def _get_previous_statistics_names(self):
        if self.context and self.context.previous_wi and self.context.previous_wi.statistics:
            return sorted(list(self.context.previous_wi.statistics.keys()))
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
                # TODO - this worked in Qt4 but not in Qt5.  at least on linux,
                # the color isn't changing.  i wonder if it has to do with the
                # fixed theme engine we're using...
                setattr(item, 
                        '_ok_color', 
                        QtGui.QColor(pal.color(item.backgroundRole())))  # @UndefinedVariable
                pal.setColor(item.backgroundRole(), QtGui.QColor(255, 145, 145))  # @UndefinedVariable
                item.setAutoFillBackground(True)
                item.setPalette(pal)
                item.repaint()
            else:
                pal.setColor(item.backgroundRole(), item._ok_color)
                delattr(item, '_ok_color')
                item.setAutoFillBackground(False)
                item.setPalette(pal)
                item.repaint()
