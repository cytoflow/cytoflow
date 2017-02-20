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

'''
Created on Mar 15, 2015
@author: brian
'''

import warnings, logging, sys, threading

from traits.api import HasStrictTraits, Instance, List, DelegatesTo, Enum, \
                       Property, cached_property, on_trait_change, Bool, \
                       Str, Dict, Any, Event, Tuple
from traitsui.api import View, Item, Handler
from pyface.qt import QtGui

import matplotlib.pyplot as plt

import pandas as pd

from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflow.views.i_view import IView
from cytoflow.utility import CytoflowOpError, CytoflowViewError

from cytoflowgui.flow_task_pane import TabListEditor
from cytoflowgui.util import DelayedEvent, filter_unpicklable

# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.last_view_plotted = None

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
    # previous WorkflowItem's ``result``
    result = Instance(Experiment, transient = True)
    
    # the channels, conditions and statistics from result.  usually these would be
    # Properties (ie, determined dynamically), but that's hard with the
    # multiprocess model.
    
    channels = List(Str, status = True)
    conditions = Dict(Str, pd.Series, status = True)
    conditions_names = Property(depends_on = 'conditions')
    metadata = Dict(Str, Any, status = True)
    statistics = Dict(Tuple(Str, Str), pd.Series, status = True)
    statistics_names = Property(depends_on = 'statistics')
    
    # we have to keep copies of these around to facilitate loading
    # and saving.
    previous_channels = List(Str, status = True)
    previous_conditions = Dict(Str, pd.Series, status = True)
    previous_conditions_names = Property(depends_on = 'previous_conditions')
    previous_metadata = Dict(Str, Any, status = True)
    previous_statistics = Dict(Tuple(Str, Str), pd.Series, status = True)
    previous_statistics_names = Property(depends_on = 'previous_statistics')

    # the IViews against the output of this operation
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
    
    # the plot names for the currently selected view
    current_view_plot_names = List(Any, status = True)
    
    # if there are multiple plots, which are we viewing?
    current_plot = Any
    
    # the view for the current plot
    current_plot_view = View(Item('current_view_plot_names',
                                  editor = TabListEditor(selected = 'current_plot'),
                                  show_label = False))
    
    # the default view for this workflow item
    default_view = Instance(IView, copy = "ref")
    
    # the previous WorkflowItem in the workflow
    previous = Instance('WorkflowItem', transient = True)
    
    # the next WorkflowItem in the workflow
    next = Instance('WorkflowItem', transient = True)
    
    # is the wi valid?
    # MAGIC: first value is the default
    status = Enum("invalid", "estimating", "applying", "valid", status = True)
    
    # report the errors and warnings
    op_error = Str(status = True)
    op_warning = Str(status = True)    
    estimate_error = Str(status = True)
    estimate_warning = Str(status = True)
    view_error = Str(status = True)
    view_warning = Str(status = True)
    
    # the event to make the workflow item re-estimate its internal model
    do_estimate = Event
    
    # the icon for the vertical notebook view.  Qt specific, sadly.
    icon = Property(depends_on = 'status', transient = True)  
    
    # synchronization primitives for plotting
    matplotlib_events = Any(transient = True)
    plot_lock = Any(transient = True)
           
    @cached_property
    def _get_icon(self):
        if self.status == "valid":
            return QtGui.QStyle.SP_DialogApplyButton
        elif self.status == "estimating" or self.status == "applying":
            return QtGui.QStyle.SP_BrowserReload
        else: # self.valid == "invalid" or None
            return QtGui.QStyle.SP_DialogCancelButton
        
    @cached_property
    def _get_operation_handler(self):
        return self.operation.handler_factory(model = self.operation)
    
    @cached_property
    def _get_current_view_handler(self):
        if self.current_view:
            return self.current_view.handler_factory(model = self.current_view)
        else:
            return None

    @cached_property
    def _get_conditions_names(self):
        if self.conditions:
            return self.conditions.keys()
        else:
            return []
        
    @cached_property
    def _get_statistics_names(self):
        if self.statistics:
            return self.statistics.keys()
        else:
            return []

    @cached_property
    def _get_previous_conditions_names(self):
        if self.previous_conditions:
            return self.previous_conditions.keys()
        else:
            return []
        
    @cached_property
    def _get_previous_statistics_names(self):
        if self.previous_statistics:
            return self.previous_statistics.keys()
        else:
            return []
        
    def __str__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.operation.__class__.__name__)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.operation.__class__.__name__)

    
class RemoteWorkflowItem(WorkflowItem):

    changed = DelayedEvent(delay = 0.2)
    
    # the Event we use to cause the remote process to run one of our 
    # functions in the main thread
    command = DelayedEvent(delay = 0.2)
    
    lock = Instance(threading.Lock, (), transient = True)
    
    @on_trait_change('+status')
    def _wi_changed(self, obj, name, old, new):
        self.changed = "status"
        
    @on_trait_change('operation:changed', post_init = True)
    def _operation_changed(self, obj, name, old, new):
        logging.debug("RemoteWorkflowItem._operation_changed :: {}"
                      .format((self, new)))
        
        if new == "estimate" and self.operation.should_clear_estimate("estimate"):
            try:
                self.operation.clear_estimate()
            except AttributeError:
                pass
            
        if new == "api" and self.operation.should_apply("operation"):
            self.command = "apply"
            
        if new == "estimate_result" and self.operation.should_apply("estimate_result"):
            self.command = "apply"
            
        if new == "estimate_result" and self.current_view.should_plot("estimate_result"):
            self.command = "plot"
            
            
    @on_trait_change('previous.result', post_init = True)
    def _prev_result_changed(self, obj, name, old, new):
        logging.debug("RemoteWorkflowItem._prev_result_changed :: {}"
                      .format(self, new))

        if self.previous and self.previous.result:
            self.previous_channels = list(self.previous.result.channels)
            self.previous_conditions = dict(self.previous.result.conditions)
            
            # some things in metadata are unpicklable, functions and such,
            # so filter them out.
            self.previous_metadata = filter_unpicklable(dict(self.previous.result.metadata))
            
            self.previous_statistics = dict(self.previous.result.statistics)

        if self.operation.should_clear_estimate("prev_result"):
            try:
                self.operation.clear_estimate()
            except AttributeError:
                pass
        
        if self.operation.should_apply("prev_result"):
            self.status = "invalid"
            self.command = "apply"
      
        if self.current_view and self.current_view.should_plot("prev_result"):
            self.command = "plot"            
            
    @on_trait_change('result', post_init = True)
    def _result_changed(self, obj, name, old, new):
        logging.debug("RemoteWorkflowItem._result_changed :: {}"
                      .format(self))   
        
        if self.current_view and self.current_view.should_plot("result"):
            self.command = "plot"   
            
        if self.result:
            self.channels = list(self.result.channels)
            self.conditions = dict(self.result.conditions)
            
            # some things in metadata are unpicklable, functions and such,
            # so filter them out.
            self.metadata = filter_unpicklable(dict(self.result.metadata))
            
            self.statistics = dict(self.result.statistics)
#         else:
#             self.channels = []
#             self.conditions = {}
#             self.metadata = {}
#             self.statistics = {}
            
    @on_trait_change('current_view', post_init = True)
    def _current_view_changed(self, obj, name, old, new):
        logging.debug("RemoteWorkflowItem._current_view_changed :: {}"
                      .format((self, new.id)))
        
        self.command = "plot"        
        
        
    @on_trait_change('current_view:changed', post_init = True)
    def _current_view_trait_changed(self, obj, name, old, new):
        logging.debug("RemoteWorkflowItem._current_view_trait_changed :: {}"
                      .format((self, new)))       
         
        if new == "api" and self.current_view.should_plot("view"):
            self.command = "plot"
            
             
    @on_trait_change('current_view.changed', post_init = True)
    def _update_plot_names(self):
        plot_names = [x for x in self.current_view.enum_plots_wi(self)]
        if plot_names == [None] or plot_names == []:
            self.current_view_plot_names = []
        else:
            self.current_view_plot_names = plot_names      
            
    @on_trait_change('current_plot', post_init = True)
    def _current_plot_changed(self):
        self.command = "plot"


    def estimate(self):
        logging.debug("WorkflowItem.estimate :: {}".format((self)))

        prev_result = self.previous.result if self.previous else None
                 
        with warnings.catch_warnings(record = True) as w:
            try:    
                self.status = "estimating"
                self.operation.estimate(prev_result)

                self.estimate_error = ""
                if w:
                    self.estimate_warning = w[-1].message.__str__()
                else:
                    self.estimate_warning = ""
                
            except CytoflowOpError as e:
                self.estimate_error = e.__str__()    
                self.status = "invalid"
                return        
            
            
    def apply(self):
        """
        Apply this wi's operation to the previous wi's result
        """
        logging.debug("WorkflowItem.apply :: {}".format((self)))
         
        prev_result = self.previous.result if self.previous else None
         
        with warnings.catch_warnings(record = True) as w:
            try:    
                self.result = None
                self.status = "applying"
                r = self.operation.apply(prev_result)
                self.result = r

                self.op_error = ""
                if w:
                    self.op_warning = w[-1].message.__str__()
                else:
                    self.op_warning = ""
                
            except CytoflowOpError as e:
                self.op_error = e.__str__()    
                self.status = "invalid"
                return
 
        self.status = "valid"
        
        
    def plot(self):              
        logging.debug("WorkflowItem.plot :: {}".format((self)))
                     
        if not self.current_view:
            plt.clf()
            plt.show()
            return
         
        self.view_warning = ""
        self.view_error = ""
          
        with warnings.catch_warnings(record = True) as w:
            try:
                self.plot_lock.acquire()                
                self.matplotlib_events.clear()

                self.current_view.plot_wi(self)
            
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
                self.view_error = e.__str__()   
                plt.clf()
                plt.show()   
            finally:
                self.matplotlib_events.set() 
                self.plot_lock.release()

                if w:
                    self.view_warning = w[-1].message.__str__()

                    
            