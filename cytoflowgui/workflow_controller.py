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

from traits.api import Instance, List, DelegatesTo, \
                       Property, cached_property
from traitsui.api import View, Item, Handler, InstanceEditor, Controller
from pyface.qt import QtGui

from cytoflow.views.i_view import IView
# from cytoflowgui.op_plugins import IOperationPlugin
# from cytoflowgui.view_plugins.i_view_plugin import IViewPlugin
from cytoflowgui.vertical_notebook_editor import VerticalNotebookEditor
    
class WorkflowItemController(Controller):
    # for the vertical notebook view, is this page deletable?
    deletable = Property()
    
    name = DelegatesTo('model')
    
    # the handler that's associated with this operation; we get it from the 
    # operation plugin, and it controls what operation traits are in the UI
    # and any special handling (heh) of them.  since the handler doesn't 
    # maintain any state, we can make and destroy as needed.
    operation_handler = Property(depends_on = 'operation', 
                                 trait = Instance(Handler), 
                                 transient = True)
    
    operation_traits = View(Item('operation_handler',
                                 style = 'custom',
                                 show_label = False))
    
    
    # the currently selected view
    current_view = Instance(IView, copy = "ref")
    
    # the handler for the currently selected view
    current_view_handler = Property(depends_on = 'current_view',
                                    trait = Instance(Handler),
                                    transient = True) 
    
    current_view_traits = View(Item('current_view_handler',
                                    style = 'custom',
                                    show_label = False))
    
    # the view for the plot params
    plot_params_traits = View(Item('current_view_handler',
                                   editor = InstanceEditor(view = 'plot_params_traits'),
                                   style = 'custom',
                                   show_label = False))
    
    # the view for the current plot
    current_plot_view = View(Item('current_view_handler',
                                  editor = InstanceEditor(view = 'current_plot_view'),
                                  style = 'custom',
                                  show_label = False))
    


    # the central event to kick of WorkflowItem update logic
#     changed = Event
    
    # the icon for the vertical notebook view.  Qt specific, sadly.
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
        return self.operation.handler_factory(model = self.operation, context = self)
    
    @cached_property
    def _get_current_view_handler(self):
        if self.current_view:
            return self.current_view.handler_factory(model = self.current_view, context = self)
        else:
            return None


class WorkflowController(Controller):
    
    workflow_handlers = List(WorkflowItemController)
    selected = Instance(WorkflowItemController)
    
    # plugin lists, to setup the interface
    op_plugins = List
    view_plugins = List
    
    workflow_view = View(Item('controller.workflow_handlers',
                              editor = VerticalNotebookEditor(view = 'operation_traits',
                                                              page_name = '.name',
                                                              page_description = '.friendly_id',
                                                              page_icon = '.icon',
                                                              delete = True,
                                                              page_deletable = '.deletable',
                                                              selected = 'controller.selected',
                                                              multiple_open = False),
                                show_label = False),
                             scrollable = True)
    
    def add_handler(self):
        pass
    
    # TODO add change handlers for selected
             