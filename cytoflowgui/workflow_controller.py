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
cytoflowgui.workflow_controllers
--------------------------------

Controllers for `LocalWorkflow` and the `WorkflowItem`\s it contains -- these
dynamically create the `traitsui.view.View` instances for the workflow's
operations and views.

Perhaps the most confusing thing in the entire codebase is the way that these
views are created.  The difficulty is that a view for a `WorkflowItem` is
polymorphic depending on the `IWorkflowOperation` that it wraps and the
`IWorkflowView` that is currently active.

Here's how this works. The "Workflow" pane contains a view of the `LocalWorkflow`
(the model), created by `WorkflowController.workflow_traits_view`.  The editor
is a `VerticalNotebookEditor`, configured to use `WorkflowController.handler_factory`
to create a new `WorkflowItemHandler` for each `WorkflowItem` in the `LocalWorkflow`.

Here's our opportunity for polymorphism! Because each `WorkflowItem` has its own
`WorkflowItemHandler` instance, the `WorkflowItemHandler.operation_traits_view`
method can return a `traitsui.view.View` *specifically for that `WorkflowItem`'s operation.*
The `traitsui.view.View` it returns contains an `InstanceHandlerEditor`, which
uses ``WorkflowItemHandler._get_operation_handler`` to get a handler specifically
for the `IWorkflowOperation` that this `WorkflowItem` wraps.  And this handler,
in turn, creates the view specifically for the `IWorkflowOperation` (and contains
the logic for connecting it to the `IWorkflowOperation` that is its model.)

The logic for the view traits and view parameters panes is similar. Each pane
contains a view of `LocalWorkflow.selected`, the currently-selected `WorkflowItem`.
In turn that `WorkflowItem`'s handler creates a view for the currently-displayed
`IWorkflowView` (which is in `WorkflowItem.current_view`). This handler, in 
turn, creates a view for the `IWorkflowView`'s traits or plot parameters.

One last non-obvious thing. Many of the operations and views require choosing
a value from the `Experiment`.  For example, if an `IWorkflowView` is plotting
a histogram, one of its traits is the channel whose histogram is being plotted.
These values -- channels, conditions, statistics and numeric statistics, for
both the current `WorkflowItem.result` and the previous `WorkflowItem.result` --
are presented as properties of the `WorkflowItemHandler`.  In turn, the
`WorkflowItemHandler` appears in the view's context dictionary as ``context``.
So, if a view wants to get the previous `WorkflowItem`'s channels, it can 
refer to them as ``context.channels``.  (Examples of this pattern are scattered
throughout the submodules of ``view_plugins``.
"""

import logging
from natsort import natsorted

from traits.api import List, DelegatesTo, Dict, observe, Property
from traitsui.api import View, Item, Controller, Spring

import cytoflow.utility as util

from .workflow import WorkflowItem
from .editors import InstanceHandlerEditor, VerticalNotebookEditor
from .experiment_pane_model import WorkflowItemNode, StringNode, experiment_tree_editor

logger = logging.getLogger(__name__)
    
class WorkflowItemHandler(Controller):
    """
    A controller for a `WorkflowItem`.  It dynamically creates views for the
    `IWorkflowOperation` and `IWorkflowView`\s that are contained, as well
    as exposing channels, conditions, statistics and numeric statistics as
    properties (so they can be accessed by the views.
    """
    
    deletable = Property()
    """For the vertical notebook view, is this page deletable?"""
    
    icon = Property(observe = 'model.status')  
    """The icon for the vertical notebook view"""
    
    name = DelegatesTo('model')
    
    friendly_id = DelegatesTo('model')
        
    # plugin lists
    op_plugins = List
    view_plugins = List
    
    conditions = Property(observe = 'model.conditions')
    """The conditions in this `WorkflowItem.result`"""
    
    conditions_names = Property(observe = "model.conditions")
    """The names of the conditions in this `WorkflowItem.result`"""
    
    previous_conditions = Property(observe = "model.previous_wi.conditions")
    """The conditions in the previous `WorkflowItem.result`"""

    previous_conditions_names = Property(observe = "model.previous_wi.conditions")
    """The names of the conditions in the previous `WorkflowItem.result`"""

    statistics_names = Property(observe = "model.statistics")
    """The names of the statistics in this `WorkflowItem.result`"""

    previous_statistics_names = Property(observe = "model.previous_wi.statistics")
    """The names of the statistics in the previous `WorkflowItem.result`"""

    channels = Property(observe = "model.channels")
    """The channels in this `WorkflowItem.result`"""

    previous_channels = Property(observe = "model.previous_wi.channels")
    """The channels in the previous `WorkflowItem.result`"""
    
    tree_node = Property(observe = "[model.channels,model.metadata,model.conditions,model.statistics]")

    ###### VIEWS
    # the view on that handler        
    def operation_traits_view(self):
        """
        Returns the `traitsui.view.View` of the `IWorkflowOperation` that this
        `WorkflowItem` wraps. The view is actually defined by the operation's
        handler's ``operation_traits_view`` attribute.
        """
        return View(Item('operation',
                         editor = InstanceHandlerEditor(view = 'operation_traits_view',
                                                        handler_factory = self._get_operation_handler),
                         style = 'custom',
                         show_label = False),
                    handler = self)


    # the view for the view traits
    def view_traits_view(self):     
        """
        Returns the `traitsui.view.View` showing the traits of the current 
        `IWorkflowView`. The view is actually defined by the view's handler's
        ``view_traits_view`` attribute.
        """
        return View(Item('current_view',
                         editor = InstanceHandlerEditor(view = 'view_traits_view',
                                                        handler_factory = self._get_view_handler),
                         style = 'custom',
                         show_label = False),
                    handler = self)

        
    # the view for the view params
    def view_params_view(self):
        """
        Returns the `traitsui.view.View` showing the plot parameters of the current 
        `IWorkflowView`. The view is actually defined by the view's handler's
        ``view_params_view`` attribute.
        """
        return View(Item('current_view',
                         editor = InstanceHandlerEditor(view = 'view_params_view',
                                                        handler_factory = self._get_view_handler),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
    # the view for the tab bar at the top of the plot
    def view_plot_name_view(self):
        """
        Returns the `traitsui.view.View` showing the plot names of the current 
        `IWorkflowView`. The view is actually defined by the view's handler's
        ``view_plot_name_view`` attribute.
        """
        return View(Item('current_view',
                         editor = InstanceHandlerEditor(view = 'view_plot_name_view',
                                                        handler_factory = self._get_view_handler),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
        
    def experiment_view(self):
        """
        Returns a `traitsui.view.View` of `LocalWorkflow.selected`, showing
        some things about the experiment -- channels, conditions, statistics,
        etc.
        """
        
        return View(Item('handler.tree_node',
                         editor = experiment_tree_editor,
                         style = 'simple',
                         show_label = False),
                    handler = self)
        
        
    def _get_tree_node(self):
        if self.model is None:
            return StringNode(label = "Please select an operation in the workflow")
        else:
            return WorkflowItemNode(wi = self.model)

    def _get_operation_handler(self, op):
        plugin = next((x for x in self.op_plugins if op.id == x.operation_id))
        return plugin.get_handler(model = op, context = self.model)
    
    def _get_view_handler(self, view):
        plugin = next((x for x in self.view_plugins + self.op_plugins if view.id == x.view_id))
        return plugin.get_handler(model = view, context = self.model)


    ##### PROPERTIES
    # MAGIC: gets value for property "deletable"
    def _get_deletable(self):
        if self.model.operation.id == 'cytoflow.operations.import':
            return False
        else:
            return True
        
    # MAGIC: gets value for property "icon"
    def _get_icon(self):
        if self.model.status == "valid":
            return 'ok'
        elif self.model.status == "estimating" or self.model.status == "applying":
            return 'refresh'
        else: # self.model.status == "invalid" or None
            return 'error'
        
    # MAGIC: gets value for property "conditions"
    def _get_conditions(self):
        if self.model and self.model.conditions:
            return self.model.conditions
        else:
            return {}
        
    # MAGIC: gets value for property "conditions_names"
    def _get_conditions_names(self):
        if self.model and self.model.conditions:
            return natsorted(list(self.model.conditions.keys()))
        else:
            return []

    # MAGIC: gets value for property "previous_conditions_names"
    def _get_previous_conditions(self):
        if self.model and self.model.previous_wi and self.model.previous_wi.conditions:
            return self.model.previous_wi.conditions
        else:
            return {}
    
    # MAGIC: gets value for property "previous_conditions_names"
    def _get_previous_conditions_names(self):
        if self.model and self.model.previous_wi and self.model.previous_wi.conditions:
            return natsorted(list(self.model.previous_wi.conditions.keys()))
        else:
            return []
        
    # MAGIC: gets value for property "statistics_names"
    def _get_statistics_names(self):
        if self.model and self.model.statistics:
            return natsorted(list(self.model.statistics.keys()))
        else:
            return []
        
    # MAGIC: gets value for property "previous_statistics_names"
    def _get_previous_statistics_names(self):
        if self.model and self.model.previous_wi and self.model.previous_wi.statistics:
            return natsorted(list(self.model.previous_wi.statistics.keys()))
        else:
            return [] 
        
    # MAGIC: gets value for property "channels"
    def _get_channels(self):
        if self.model and self.model.channels:
            return natsorted(self.model.channels)
        else:
            return []
        
    # MAGIC: gets value for property "previous_channels"
    def _get_previous_channels(self):
        if self.model and self.model.previous_wi and self.model.previous_wi.channels:
            return natsorted(self.model.previous_wi.channels)
        else:
            return [] 


class WorkflowController(Controller):
    """
    A controller for a `LocalWorkflow`.  It dynamically creates views for the
    major panes in the UI: the workflow, the selected view traits, and the
    selected view parameters.  It also contains the logic for adding operations
    and activating views.  Both of which are triggered by the button bars on the
    sides of their respective panes.
    """
    
    workflow_handlers = Dict(WorkflowItem, WorkflowItemHandler)
    
    # plugin lists
    op_plugins = List
    view_plugins = List
    
    def workflow_traits_view(self):  
        """
        Returns a `traitsui.view.View` of the `LocalWorkflow` for the ``Workflow``
        pane.  Its editor is a `VerticalNotebookEditor`.  Each item's instance view
        is created by `WorkflowItemHandler.operation_traits_view`.
        """
            
        return View(Item('workflow',
                         editor = VerticalNotebookEditor(view = 'operation_traits_view',
                                                         page_name = '.name',
                                                         page_description = '.friendly_id',
                                                         page_icon = '.icon',
                                                         delete = True,
                                                         page_deletable = '.deletable',
                                                         selected = 'selected',
                                                         handler_factory = self.handler_factory,
                                                         multiple_open = False),
                         show_label = False),
                    handler = self,
                    scrollable = True)
        
        
    def selected_view_traits_view(self):
        """
        Returns a `traitsui.view.View` of `LocalWorkflow.selected` for the
        ``View traits`` pane.  The actual view is created by 
        `WorkflowItemHandler.view_traits_view`.
        """
        
        return View(Item('selected',
                         editor = InstanceHandlerEditor(view = 'view_traits_view',
                                                        handler_factory = self.handler_factory),
                         style = 'custom',
                         show_label = False),
                    Spring(),
                    Item('apply_calls',
                         style = 'readonly',
                         visible_when = 'debug'),
                    Item('plot_calls',
                         style = 'readonly',
                         visible_when = 'debug'),
                    handler = self,
                    kind = 'panel',
                    scrollable = True)
        
        
    def selected_view_params_view(self):
        """
        Returns a `traitsui.view.View` of `LocalWorkflow.selected` for the
        ``View parameters`` pane.  The actual view is created by 
        `WorkflowItemHandler.view_params_view`.
        """
        
        return View(Item('selected',
                         editor = InstanceHandlerEditor(view = 'view_params_view',
                                                        handler_factory = self.handler_factory),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
    
    def selected_view_plot_name_view(self):  
        """
        Returns a `traitsui.view.View` of `LocalWorkflow.selected` for the
        plot names toolbar.  The actual view is created by 
        `WorkflowItemHandler.view_plot_name_view`.
        """
        
        return View(Item('selected',
                         editor = InstanceHandlerEditor(view = 'view_plot_name_view',
                                                        handler_factory = self.handler_factory),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
        
    def experiment_view(self):  
        """
        Returns a `traitsui.view.View` of `LocalWorkflow.selected` for the
        experiment viewer.
        """
        
        return View(Item('selected',
                         editor = InstanceHandlerEditor(view = 'experiment_view',
                                                        handler_factory = self.handler_factory),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
        
    def handler_factory(self, wi):
        """
        Return an instance of `WorkflowItemHandler` for a `WorkflowItem` in `LocalWorkflow`
        """
        
        if wi not in self.workflow_handlers:
            self.workflow_handlers[wi] = WorkflowItemHandler(model = wi,
                                                             op_plugins = self.op_plugins,
                                                             view_plugins = self.view_plugins)
            
        return self.workflow_handlers[wi]
    
    
    def add_operation(self, operation_id):
        """
        The logic to add an `IWorkflowOperation` to `LocalWorkflow`.  Creates a 
        new `WorkflowItem`, figures out where to add it, inserts it into the model
        and activates the default view (if present.)
        """
        
        # find the operation plugin
        op_plugin = next((x for x in self.op_plugins 
                          if x.operation_id == operation_id))
        
        # make a new workflow item
        wi = WorkflowItem(operation = op_plugin.get_operation(), 
                          workflow = self.model)
        
        # figure out where to add it
        if self.model.selected:
            idx = self.model.workflow.index(self.model.selected) + 1
        else:
            idx = len(self.model.workflow)
              
        # the add_remove_items handler takes care of updating the linked list
        self.model.workflow.insert(idx, wi)
         
        # and make sure to actually select the new wi
        self.model.selected = wi
        
        # if we have a default view, activate it
        if self.model.selected.default_view:
            self.activate_view(self.model.selected.default_view.id)
        
        return wi
    
    def activate_view(self, view_id):
        """
        The logic to activate a view on the selected `WorkflowItem`.  Creates a new
        instance of the view if necessary and makes it the current view; event handlers
        on `WorkflowItem.current_view` take care of everything else.
        """
        
        # is it the default view?
        if view_id == 'default':
            view_id = self.model.selected.default_view.id
        
        # do we already have an instance?
        if view_id in [x.id for x in self.model.selected.views]:
            self.model.selected.current_view = next((x for x in self.model.selected.views
                                                     if x.id == view_id))
            return
            
        # make a new view instance
        if self.model.selected.default_view and view_id == self.model.selected.default_view.id:
            view = self.model.selected.default_view
        else:
            view_plugin = next((x for x in self.view_plugins
                                if x.view_id == view_id))
            view = view_plugin.get_view()
            
        self.model.selected.views.append(view)
        self.model.selected.current_view = view
    
    @observe('model:workflow:items', post_init = True)
    def _on_workflow_add_remove_items(self, event):
        logger.debug("WorkflowController._on_workflow_add_remove_items :: {}"
                      .format((event.index, event.added, event.removed)))
                
        # remove deleted items from the linked list
        if event.removed:
            assert len(event.removed) == 1
            wi = event.removed[0]
            del self.workflow_handlers[wi]
            
            if wi == self.model.selected:
                self.model.selected = None
        
        # add new items to the linked list
        if event.added:
            assert len(event.added) == 1
            wi = event.added[0]
            if wi not in self.workflow_handlers:
                self.workflow_handlers[wi] = WorkflowItemHandler(model = wi,
                                                                 op_plugins = self.op_plugins,
                                                                 view_plugins = self.view_plugins)
                
                
            


