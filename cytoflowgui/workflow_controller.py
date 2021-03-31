#!/usr/bin/env python3.4
# coding: latin-1


# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
Created on Mar 15, 2015
@author: brian
'''

import logging
from natsort import natsorted

from traits.api import List, DelegatesTo, Dict, observe, Property
from traitsui.api import View, Item, Controller, Spring
from pyface.qt import QtGui

import cytoflow.utility as util

from .workflow import WorkflowItem
from .editors import InstanceHandlerEditor
from cytoflowgui.editors import VerticalNotebookEditor

logger = logging.getLogger(__name__)
    
class WorkflowItemHandler(Controller):
    # for the vertical notebook view, is this page deletable?
    deletable = Property()
    
    # the icon for the vertical notebook view.
    icon = Property(depends_on = 'model.status')  
    
    name = DelegatesTo('model')
    friendly_id = DelegatesTo('model')
        
    # plugin lists
    op_plugins = List
    view_plugins = List
    
    conditions = Property(observe = 'model.conditions')
    conditions_names = Property(observe = "model.conditions")
    previous_conditions = Property(observe = "model.previous_wi.conditions")
    previous_conditions_names = Property(observe = "model.previous_wi.conditions")
    statistics_names = Property(observe = "model.statistics")
    numeric_statistics_names = Property(observe = "model.statistics")
    previous_statistics_names = Property(observe = "model.previous_wi.statistics")
    channels = Property(observe = "model.channels")
    previous_channels = Property(observe = "model.previous_wi.channels")

    ###### VIEWS
    # the view on that handler        
    def operation_traits_view(self):
        return View(Item('operation',
                         editor = InstanceHandlerEditor(view = 'operation_traits_view',
                                                        handler_factory = self._get_operation_handler),
                         style = 'custom',
                         show_label = False),
                    handler = self)

    # the view for the view traits
    def view_traits_view(self):     
        return View(Item('current_view',
                         editor = InstanceHandlerEditor(view = 'view_traits_view',
                                                        handler_factory = self._get_view_handler),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
    # the view for the view params
    def view_params_view(self):
        return View(Item('current_view',
                         editor = InstanceHandlerEditor(view = 'view_params_view',
                                                        handler_factory = self._get_view_handler),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
    # the view for the tab bar at the top of the plot
    def view_plot_name_view(self):
        return View(Item('current_view',
                         editor = InstanceHandlerEditor(view = 'view_plot_name_view',
                                                        handler_factory = self._get_view_handler),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
    def _get_operation_handler(self, op):
        plugin = next((x for x in self.op_plugins if op.id == x.operation_id))
        return plugin.get_handler(model = op, context = self.model)
    
    def _get_view_handler(self, view):
        plugin = next((x for x in self.view_plugins + self.op_plugins if view.id == x.view_id))
        return plugin.get_handler(model = view, context = self.model)


    ##### PROPERTIES
    # MAGIC: gets value for property "deletable"
    def _get_deletable(self):
        if self.model.operation.id == 'edu.mit.synbio.cytoflow.operations.import':
            return False
        else:
            return True
        
    # MAGIC: gets value for property "icon"
    def _get_icon(self):
        if self.model.status == "valid":
            return QtGui.QStyle.SP_DialogApplyButton  # @UndefinedVariable
        elif self.model.status == "estimating" or self.model.status == "applying":
            return QtGui.QStyle.SP_BrowserReload  # @UndefinedVariable
        else: # self.model.status == "invalid" or None
            return QtGui.QStyle.SP_DialogCancelButton  # @UndefinedVariable
        
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
        
    # MAGIC: gets value for property "numeric_statistics_names"
    def _get_numeric_statistics_names(self):
        if self.model and self.model.statistics:
            return sorted([x for x in list(self.model.statistics.keys())
                                 if util.is_numeric(self.model.statistics[x])])
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
    
    workflow_handlers = Dict(WorkflowItem, WorkflowItemHandler)
    
    # plugin lists
    op_plugins = List
    view_plugins = List
    
        
    def workflow_traits_view(self):      
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
        return View(Item('selected',
                         editor = InstanceHandlerEditor(view = 'view_params_view',
                                                        handler_factory = self.handler_factory),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
    
    def selected_view_plot_name_view(self):  
        return View(Item('selected',
                         editor = InstanceHandlerEditor(view = 'view_plot_name_view',
                                                        handler_factory = self.handler_factory),
                         style = 'custom',
                         show_label = False),
                    handler = self)
        
        
    def handler_factory(self, wi):
        if wi not in self.workflow_handlers:
            self.workflow_handlers[wi] = WorkflowItemHandler(model = wi,
                                                             op_plugins = self.op_plugins,
                                                             view_plugins = self.view_plugins)
            
        return self.workflow_handlers[wi]
    
    
    def add_operation(self, operation_id):
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
                
                
            


