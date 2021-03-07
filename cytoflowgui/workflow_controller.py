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

from traits.api import List, DelegatesTo, Dict, observe, Property, cached_property
from traitsui.api import View, Item, InstanceEditor, Controller, Spring
from pyface.qt import QtGui

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
    
    # which tabs are we showing at the top of the 
    
    # plugin lists
    op_plugins = List
    view_plugins = List
        

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
        
    
    # the view for the current plot
#     def view_plot(self):
#         if self.model.current_view is None:
#             return View()
#         
#         view_plugin = next((x for x in self.view_plugins 
#                             if self.model.current_view.id == x.view_id))
#         handler = view_plugin.get_handler(model = self.model.current_view,
#                                           context = self.model)
#          
#         return View(Item('current_view',
#                          editor = InstanceEditor(view = handler.current_plot_view()),
#                          style = 'custom',
#                          show_label = False),
#                     handler = self)
           

    @cached_property
    def _get_deletable(self):
        if self.model.operation.id == 'edu.mit.synbio.cytoflow.operations.import':
            return False
        else:
            return True
        
           
    @cached_property
    def _get_icon(self):
        if self.model.status == "valid":
            return QtGui.QStyle.SP_DialogApplyButton  # @UndefinedVariable
        elif self.model.status == "estimating" or self.model.status == "applying":
            return QtGui.QStyle.SP_BrowserReload  # @UndefinedVariable
        else: # self.model.status == "invalid" or None
            return QtGui.QStyle.SP_DialogCancelButton  # @UndefinedVariable
        
        
    def _get_operation_handler(self, op):
        op_plugin = next((x for x in self.op_plugins if op.id == x.operation_id))
        return op_plugin.get_handler(model = op, context = self.model)
    
        
    def _get_view_handler(self, view):
        view_plugin = next((x for x in self.view_plugins if view.id == x.view_id))
        return view_plugin.get_handler(model = view,
                                       context = self.model)
        
        
#         
#     @cached_property
#     def _get_operation_handler(self):
#         op_plugin = next((x for x in self.op_plugins if self.model.operation.id == x.operation_id))
#         return op_plugin.get_handler(model = self.model.operation,
#                                      context = self.model)
# 
#      
#     @cached_property
#     def _get_current_view_handler(self):
#         if self.current_view:
#             view_plugin = next((x for x in self.view_plugins if self.model.current_view.id == x.view_id))
#             return view_plugin.get_view_handler(model = self.model.current_view,
#                                                 context = self.model)
#         else:
#             return None


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
        
    
#     def selected_view_plot(self):  
#         return View(Item('selected',
#                          editor = InstanceHandlerEditor(view = 'view_plot',
#                                                         handler_factory = self.handler_factory),
#                          style = 'custom',
#                          show_label = False),
#                     handler = self)
        
        
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
            idx = self.model.workflow.index(self.selected) + 1
        else:
            idx = len(self.model.workflow)
              
        # the add_remove_items handler takes care of updating the linked list
        self.model.workflow.insert(idx, wi)
         
        # and make sure to actually select the new wi
        self.model.selected = wi
        
        return wi
    
    def activate_view(self, view_id):
        # is it the default view?
        if view_id == 'default':
            self.model.selected.current_view = self.model.selected.default_view
            return
        
        # do we already have an instance?
        if view_id in [x.id for x in self.model.selected.views]:
            self.model.selected.current_view = next((x for x in self.model.selected.views
                                                     if x.id == view_id))
            
        # make a new view instance
        view_plugin = next((x for x in self.view_plugins
                            if x.view_id == view_id))
        view = view_plugin.get_view()
        self.model.selected.views.append(view)
        self.model.selected.current_view = view
        
    
    @observe('model:workflow:items', post_init = True)
    def _on_workflow_add_remove_items(self, event):
        logger.debug("WorkflowController._on_workflow_add_remove_items :: {}"
                      .format((event.index, event.added, event.removed)))

        wi = self.model.workflow[event.index]
                
        # remove deleted items from the linked list
        if event.removed:
            assert len(event.removed) == 1
            del self.workflow_handlers[wi]
            
            if wi == self.selected:
                self.selected = None
        
        # add new items to the linked list
        if event.added:
            assert len(event.added) == 1
            if wi not in self.workflow_handlers:
                self.workflow_handlers[wi] = WorkflowItemHandler(model = wi,
                                                                 op_plugins = self.op_plugins,
                                                                 view_plugins = self.view_plugins)
                
                
            


