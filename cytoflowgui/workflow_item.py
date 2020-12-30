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

import warnings, logging, sys, threading

from traits.api import HasStrictTraits, Instance, List, DelegatesTo, Enum, \
                       Property, cached_property, Bool, \
                       Str, Dict, Any, Event, Tuple
from traitsui.api import View, Item, Handler, InstanceEditor
from pyface.qt import QtGui

import matplotlib.pyplot as plt

import pandas as pd

from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflow.views.i_view import IView
from cytoflow.utility import CytoflowError, CytoflowOpError, CytoflowViewError

# from cytoflowgui.flow_task_pane import TabListEditor
from cytoflowgui.serialization import camel_registry

# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.last_view_plotted = None

logger = logging.getLogger(__name__)

class WorkflowItem(HasStrictTraits):
    """        
    The basic unit of a Workflow: wraps an operation and a list of views.
    
    Notes
    -----
    Because we serialize instances of this, we have to pay careful attention
    to which traits are ``transient`` (and aren't serialized)
    """
    
    # the operation's id
    friendly_id = DelegatesTo('operation')
    
    # the operation's name
    name = DelegatesTo('operation')
    
    # the operation this Item wraps
    operation = Instance(IOperation, copy = "ref")
    
    # for the vertical notebook view, is this page deletable?
    deletable = Bool(True)
    
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
    
    # the Experiment that is the result of applying *operation* to the
    # previous_wi WorkflowItem's ``result``
    result = Instance(Experiment, transient = True)
    
    # the channels, conditions and statistics from result.  usually these would be
    # Properties (ie, determined dynamically), but that's hard with the
    # multiprocess model.
    
    channels = List(Str, status = True)
    conditions = Dict(Str, pd.Series, status = True)
    metadata = Dict(Str, Any, status = True)
    statistics = Dict(Tuple(Str, Str), pd.Series, status = True)

    # the IViews associated with this operation
    views = List(IView, copy = "ref")
    
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
    
    # the default view for this workflow item
    default_view = Instance(IView, copy = "ref")
    
    # the previous_wi WorkflowItem in the workflow
    previous_wi = Instance('WorkflowItem', transient = True)
    
    # the next_wi WorkflowItem in the workflow
    next_wi = Instance('WorkflowItem', transient = True)
    
    # is the wi valid?
    # MAGIC: first value is the default
    status = Enum("invalid", "waiting", "estimating", "applying", "valid", "loading", status = True)
    
    # report the errors and warnings
    op_error = Str(status = True)
    op_error_trait = Str(status = True)
    op_warning = Str(status = True)
    op_warning_trait = Str(status = True)    
    estimate_error = Str(status = True)
    estimate_warning = Str(status = True)
    view_error = Str(status = True)
    view_error_trait = Str(status = True)
    view_warning = Str(status = True)
    view_warning_trait = Str(status = True)

    # the central event to kick of WorkflowItem update logic
    changed = Event
    
    # the icon for the vertical notebook view.  Qt specific, sadly.
    icon = Property(depends_on = 'status', transient = True)  
    
    # synchronization primitive for updating wi traits
    lock = Instance(threading.RLock, (), transient = True)
    
    # synchronization primitives for plotting
    matplotlib_events = Any(transient = True)
    plot_lock = Any(transient = True)
           
    # events to track number of times apply() and plot() are called
    apply_called = Event
    plot_called = Event
           
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
        
    def __str__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.operation.__class__.__name__)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.operation.__class__.__name__)
    
@camel_registry.dumper(WorkflowItem, 'workflow-item', version = 2)
def _dump_wi(wi):
                          
    # we really don't need to keep copying around the fcs metadata
    # it will still get saved out in the import op
    if 'fcs_metadata' in wi.metadata:
        del wi.metadata['fcs_metadata']
                            
    return dict(deletable = wi.deletable,
                operation = wi.operation,
                views = wi.views,
                channels = wi.channels,
                conditions = wi.conditions,
                metadata = wi.metadata,
                statistics = wi.statistics,
                current_view = wi.current_view,
                default_view = wi.default_view)
    
@camel_registry.dumper(WorkflowItem, 'workflow-item', version = 1)
def _dump_wi_v1(wi):
                            
    return dict(deletable = wi.deletable,
                operation = wi.operation,
                views = wi.views,
                channels = wi.channels,
                conditions = wi.conditions,
                metadata = wi.metadata,
                statistics = list(wi.statistics.keys()),
                current_view = wi.current_view,
                default_view = wi.default_view)


@camel_registry.loader('workflow-item', version = 1)
def _load_wi_v1(data, version):
    
    data['statistics'] = {tuple(k) : pd.Series() for k in data['statistics']}
    
    ret = WorkflowItem(**data)
        
    return ret

@camel_registry.loader('workflow-item', version = 2)
def _load_wi(data, version):
    return WorkflowItem(**data)
    
class RemoteWorkflowItem(WorkflowItem):
    
    def estimate(self):
        logger.debug("WorkflowItem.estimate :: {}".format((self)))

        prev_result = self.previous_wi.result if self.previous_wi else None
                 
        with warnings.catch_warnings(record = True) as w:
            try:    
                self.status = "estimating"
                
                try:
                    plt.gcf().canvas.set_working(True)
                except AttributeError:
                    pass

                self.operation.estimate(prev_result)

                self.estimate_error = ""
                if w:
                    self.estimate_warning = w[-1].message.__str__()
                else:
                    self.estimate_warning = ""
                
                return True
                
            except CytoflowError as e:
                self.estimate_error = e.__str__()    
                self.status = "invalid"
                return False 
            
            finally:
                try:
                    plt.gcf().canvas.set_working(False)
                except AttributeError:
                    pass
                
            
            
    def apply(self):
        """
        Apply this wi's operation to the previous_wi wi's result
        """
        logger.debug("WorkflowItem.apply :: {}".format((self)))
        self.apply_called = True
         
        prev_result = self.previous_wi.result if self.previous_wi else None
         
        with warnings.catch_warnings(record = True) as w:
            try:    
                self.status = "applying"
                
                try:
                    plt.gcf().canvas.set_working(True)
                except AttributeError:
                    pass
                
                r = self.operation.apply(prev_result)
                self.result = r

                self.op_error = ""
                self.op_error_trait = ""
                if w:
                    self.op_warning = w[-1].message.__str__()
                else:
                    self.op_warning = ""
                    self.op_warning_trait = ""
                    
                self.status = "valid"
            
            except CytoflowOpError as e:                
                self.result = None
                if e.args[0]:
                    self.op_error_trait = e.args[0]
                self.op_error = e.args[-1]    
                self.status = "invalid"
                
            except CytoflowError as e:
                self.result = None
                self.op_error = e.args[-1]    
                self.status = "invalid"
            
            finally:
                try:
                    plt.gcf().canvas.set_working(False)
                except AttributeError:
                    pass

        
    def plot(self):              
        logger.debug("WorkflowItem.plot :: {}".format((self)))
        self.plot_called = True
                     
        if not self.current_view:
            self.plot_lock.acquire()                
            self.matplotlib_events.clear()
            plt.clf()
            plt.show()
            self.matplotlib_events.set() 
            self.plot_lock.release()
            return

        try:
            if len(self.current_view.plot_names) > 0 and self.current_view.current_plot not in self.current_view.plot_names:
                self.view_error = "Plot {} not in current plot names {}".format(self.current_view.current_plot, self.current_view.plot_names)
                return
        except Exception as e:
            # occasionally if the types are really different the "in" statement 
            # above will throw an error
            self.view_error = "Plot {} not in current plot names {}".format(self.current_view.current_plot, self.current_view.plot_names)
            return
          
        with warnings.catch_warnings(record = True) as w:
            try:
                self.plot_lock.acquire()                
                self.matplotlib_events.clear()
                
                try:
                    plt.gcf().canvas.set_working(True)
                except AttributeError:
                    pass
                
                self.current_view.plot_wi(self)
                self.view_error = ""
                self.view_error_trait = ""
            
                if this.last_view_plotted and "interactive" in this.last_view_plotted.traits():
                    this.last_view_plotted.interactive = False
                 
                if "interactive" in self.current_view.traits():
                    self.current_view.interactive = True
                   
                this.last_view_plotted = self.current_view
                  
                # the remote canvas/pyplot interface of the multiprocess backend
                # is NOT interactive.  this call lets us batch together all 
                # the plot updates
                plt.show()
                
            except CytoflowViewError as e:                
                if e.args[0]:
                    self.view_error_trait = e.args[0]
                self.view_error = e.args[-1]    
                plt.clf()
                plt.show()
                                     
            except CytoflowError as e:
                self.view_error = e.__str__()   
                plt.clf()
                plt.show() 
            finally:
                self.matplotlib_events.set()
                try:
                    plt.gcf().canvas.set_working(False)
                except AttributeError:
                    pass
                 
                self.plot_lock.release()

                if w:
                    self.view_warning = w[-1].message.__str__()
                else:
                    self.view_warning = ""
                    
            return True

                    
            