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
cytoflowgui.workflow.operations.operation_base
----------------------------------------------

"""

from traits.api import HasStrictTraits, Event
from cytoflow.operations import IOperation

class IWorkflowOperation(IOperation):
    """
    An interface that extends a `cytoflow` operation with functions 
    required for GUI support.
    
    In addition to implementing the interface below, another common thing to 
    do in the derived class is to override traits of the underlying class in 
    order to add metadata that controls their handling by the workflow.  
    Currently, relevant metadata include:
    
      * **apply** - This trait is used by the operations `apply` method.
       
      * **estimate** - This trait is used by the operation's `estimate` method.
        
      * **estimate_result** - This trait is set as a result of calling `estimate`.
     
      * **status** - Holds status variables like the number of events from the `ImportOp`.
    
      * **transient** - A temporary variable (not copied between processes or serialized).
    
    Attributes
    ----------
        
    do_estimate : Event
        Firing this event causes the operation's `estimate` method 
        to be called.
        
    changed : Event
        Used to transmit status information back from the operation to the
        workflow.  Set its value to the name of the trait that was changed

    """
        
    # causes this operation's estimate() function to be called. observed in LocalWorkflow.
    do_estimate = Event
    
    # an all-purpose "this thing changed" event
    # set it to the name of the trait that changed
    changed = Event

                
    def should_apply(self, changed, payload):
        """
        Should the owning WorkflowItem apply this operation when certain things
        change?  `changed` can be:
        
         - Changed.APPLY -- the parameters required to run apply() changed
         
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         
         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
         
        If `should_apply` is called from a notification handler, then ``payload`` is
        the ``event`` object from the notification handler.
        """

    
    def should_clear_estimate(self, changed, payload):
        """
        Should the owning WorkflowItem clear the estimated model by calling
        op.clear_estimate()?  ``changed`` can be:
        
         - Changed.ESTIMATE -- the parameters required to call `estimate` 
           (ie traits with ``estimate = True`` metadata) have changed
            
         - Changed.PREV_RESULT -- the previous `WorkflowItem`'s result changed    
              
        If `should_clear_estimate` is called from a notificaion handler, then ``payload`` is
        the ``event`` object.
         """
    
    
    def clear_estimate(self):
        """
        Clear whatever variables hold the results of calling estimate()
        """
        
    
    def get_notebook_code(self, idx):
        """
        Return Python code suitable for a Jupyter notebook cell that runs this
        operation.
        
        Parameters
        ----------
        idx : integer
            The index of the `WorkflowItem` that holds this operation.
            
        Returns
        -------
        string
            The Python code that calls this module.
        """
        

class WorkflowOperation(HasStrictTraits):
    """
    A default implementation of `IWorkflowOperation`
    """
    
    # causes this operation's estimate() function to be called. observed in LocalWorkflow.
    do_estimate = Event
    
    # an all-purpose "this thing changed" event
    # set it to the name of the trait that changed
    # should ONLY ever be set in the LOCAL process
    changed = Event(apply = True, estimate = True)
    
    def should_apply(self, changed, payload):
        return True

    
    def should_clear_estimate(self, changed, payload):
        return True
    
    
    def clear_estimate(self):
        pass
    
    def get_notebook_code(self, idx):
        raise NotImplementedError("GUI plugins must override get_notebook_code()")
    

