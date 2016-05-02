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

import warnings

from traits.api import HasStrictTraits, Instance, List, DelegatesTo, Enum, \
                       Property, cached_property, on_trait_change, Bool, \
                       Str, Dict
from traitsui.api import View, Item, Handler
from pyface.qt import QtGui

import numpy as np
import pandas as pd

from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflow.views.i_view import IView
from cytoflow.utility import CytoflowError

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
    operation = Instance(IOperation)
    
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
    
    # the channels and conditions from result.  usually these would be
    # Properties (ie, determined dynamically), but that's currently hard
    # with the multiprocess model.
    
    channels = List(Str)
    conditions = List(Str)
        
    # we need the types and the values to set up the subset editor
    conditions_types = Dict(Str, Str)
    conditions_values = Dict(Str, List)
    
    # the IViews against the output of this operation
    views = List(IView)
    
    # the currently selected view
    current_view = Instance(IView)
    
    # the handler for the currently selected view
    current_view_handler = Property(depends_on = 'current_view',
                                    trait = Instance(Handler),
                                    transient = True) 
    
    current_view_traits = View(Item('current_view_handler',
                                    style = 'custom',
                                    show_label = False))
    
    # the default view for this workflow item
    default_view = Instance(IView)
    
    # the previous WorkflowItem in the workflow
    previous = Instance('WorkflowItem')
    
    # the next WorkflowItem in the workflow
    next = Instance('WorkflowItem')
    
    # is the wi valid?
    # MAGIC: first value is the default
    status = Enum("invalid", "estimating", "applying", "valid", transient = True)
    
    # if we errored out, what was the error string?
    error = Str()
    
    # if we got a warning, what was the warning string?
    warning = Str()
    
    # the icon for the vertical notebook view.  Qt specific, sadly.
    icon = Property(depends_on = 'status', transient = True)
        
    def update(self):
        """
        Called by the controller to update this wi
        """
             
        self.status = "invalid"             
        self.warning = ""
        self.error = ""
        self.result = None
         
        prev_result = self.previous.result if self.previous else None
         
        with warnings.catch_warnings(record = True) as w:
            try:
                if (hasattr(self.operation, "estimate") and
                    callable(getattr(self.operation, "estimate"))):
                    self.status = "estimating"
                    self.operation.estimate(prev_result)
                self.status = "applying"
                self.result = self.operation.apply(prev_result)
                if w:
                    self.warning = w[-1].message.__str__()
                    
                
            except CytoflowError as e:
                self.error = e.__str__()    
                self.status = "invalid"
                return
 
        self.status = "valid"
           
    @cached_property
    def _get_icon(self):
        if self.status == "valid":
            return QtGui.QStyle.SP_DialogOkButton
        elif self.status == "estimating" or self.status == "applying":
            return QtGui.QStyle.SP_BrowserReload
        else: # self.valid == "invalid" or None
            return QtGui.QStyle.SP_BrowserStop

    @cached_property
    def _get_operation_handler(self):
        return self.operation.handler_factory(model = self.operation)

    @cached_property
    def _get_current_view_handler(self):
        if self.current_view:
            return self.current_view.handler_factory(model = self.current_view)
        else:
            return None
         
    @on_trait_change('result')
    def _result_changed(self, experiment):
        """Update channels and conditions"""
  
        if experiment:
            self.channels = experiment.channels
            self.conditions = experiment.conditions.keys()
            
            self.conditions_types = experiment.conditions
            
            for condition in self.conditions_types.keys():
                self.conditions_values[condition] = \
                    list(np.sort(pd.unique(experiment[condition])))
                    