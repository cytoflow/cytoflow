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
from cytoflowgui.editors import VerticalNotebookEditor

logger = logging.getLogger(__name__)
    
class WorkflowItemHandler(Controller):
    # for the vertical notebook view, is this page deletable?
    deletable = Property()
    
    name = DelegatesTo('model')
    friendly_id = DelegatesTo('model')
    
    # plugin lists
    op_plugins = List
    view_plugins = List
        
    # the handler that's associated with this operation; we get it from the 
    # operation plugin, and it controls what operation traits are in the UI
    # and any special handling of them.  since the handler doesn't 
    # maintain any state, we can make and destroy as needed.
#     operation_handler = Property(depends_on = 'operation', 
#                                  trait = Instance(Handler), 
#                                  transient = True)

    # the view on that handler        
    def operation_traits_view(self):
        op_plugin = next((x for x in self.op_plugins if self.model.operation.id == x.operation_id))
        handler = op_plugin.get_handler(model = self.model.operation,
                                        context = self.model)
        return View(Item('operation',
                         style = 'custom',
                         show_label = False),
                    handler = handler)
        
    # the handler for the currently selected view
#     current_view_handler = Property(depends_on = 'current_view',
#                                     trait = Instance(Handler),
#                                     transient = True) 
    
    # the view for the view params
    def current_view_traits_view(self):
        view_plugin = next((x for x in self.view_plugins if self.model.current_view.id == x.view_id))
        handler = view_plugin.get_view_handler(model = self.model.current_view,
                                               context = self.model)
        
        return View(Item('current_view',
                         style = 'custom',
                         show_label = False),
                    handler = handler)
    
    # the view for the plot params
    def current_view_plot_params_view(self):
        view_plugin = next((x for x in self.view_plugins if self.model.current_view.id == x.view_id))
        handler = view_plugin.get_view_handler(model = self.model.current_view,
                                               context = self.model)
        
        return View(Item('current_view',
                         editor = InstanceEditor(view = 'plot_params_view'),
                         style = 'custom',
                         show_label = False),
                    handler = handler)
    
    # the view for the current plot
    def current_plot_view(self):
        view_plugin = next((x for x in self.view_plugins if self.model.current_view.id == x.view_id))
        handler = view_plugin.get_view_handler(model = self.model.current_view,
                                               context = self.model)
        
        return View(Item('current_view',
                         editor = InstanceEditor(view = 'current_plot_view'),
                         style = 'custom',
                         show_label = False),
                    handler = handler)

    # the icon for the vertical notebook view.  Qt specific.
    icon = Property(depends_on = 'status', transient = True)  

    @cached_property
    def _get_deletable(self):
        if self.model.operation.id == 'edu.mit.synbio.cytoflow.operations.import':
            return False
        else:
            return True
           
    @cached_property
    def _get_icon(self):
        if self.status == "valid":
            return QtGui.QStyle.SP_DialogApplyButton  # @UndefinedVariable
        elif self.status == "estimating" or self.status == "applying":
            return QtGui.QStyle.SP_BrowserReload  # @UndefinedVariable
        else: # self.valid == "invalid" or None
            return QtGui.QStyle.SP_DialogCancelButton  # @UndefinedVariable
        
    @cached_property
    def _get_operation_handler(self):
        op_plugin = next((x for x in self.op_plugins if self.model.operation.id == x.operation_id))
        return op_plugin.get_handler(model = self.model.operation,
                                     context = self.model)

     
    @cached_property
    def _get_current_view_handler(self):
        if self.current_view:
            view_plugin = next((x for x in self.view_plugins if self.model.current_view.id == x.view_id))
            return view_plugin.get_view_handler(model = self.model.current_view,
                                                context = self.model)
        else:
            return None


class WorkflowController(Controller):
    
    workflow_handlers = Dict(WorkflowItem, WorkflowItemHandler)
    
    # plugin lists
    op_plugins = List
    view_plugins = List
    
    
    def current_plot_view(self):  
        return View(Item('selected',
                         editor = InstanceEditor(view = 'current_plot_view'),
                         style = 'custom',
                         show_label = False),
                    handler = self.workflow_handlers[self.model.selected] if self.model.selected else None)
        
        
    def workflow_view(self):
        return View(Item('workflow',
                         editor = VerticalNotebookEditor(view = 'operation_traits_view',
                                                         page_name = '.name',
                                                         page_description = '.friendly_id',
                                                         page_icon = '.icon',
                                                         delete = True,
                                                         page_deletable = '.deletable',
                                                         selected = 'selected',
                                                         multiple_open = False),
                               show_label = False),
                         handler = self,
                         scrollable = True)
        
        
    def selected_view_traits(self):
        return View(Item('selected',
                         editor = InstanceEditor(view = 'current_view_traits_view'),
                         style = 'custom',
                         show_label = False),
                    Spring(),
                    Item('apply_calls',
                         style = 'readonly',
                         visible_when = 'debug'),
                    Item('plot_calls',
                         style = 'readonly',
                         visible_when = 'debug'),
                    handler = self.workflow_handlers[self.model.selected] if self.model.selected else None,
                    kind = 'panel',
                    scrollable = True)
        
        
    def selected_view_plot_params(self):
        return View(Item('selected',
                         editor = InstanceEditor(view = 'current_view_plot_params_view'),
                         style = 'custom',
                         show_label = False),
                    handler = self.workflow_handlers[self.model.selected] if self.model.selected else None)
        
    
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
            self.workflow_handlers[wi] = WorkflowItemHandler(model = wi,
                                                             op_plugins = self.op_plugins,
                                                             view_plugins = self.view_plugins)
            


