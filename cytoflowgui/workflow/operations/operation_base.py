'''
Created on Jan 15, 2021

@author: brian
'''

from traits.api import HasStrictTraits, Event
from cytoflow.operations import IOperation

class IWorkflowOperation(IOperation):
    
    """
    An interface that extends an :mod:`cytoflow` operation with functions 
    required for GUI support.
    
    In addition to implementing the interface below, another common thing to 
    do in the derived class is to override traits of the underlying class in 
    order to add metadata that controls their handling by the workflow.  
    Currently, relevant metadata include:
    
      * **apply** - This trait is used by the operations :meth:`apply` method.
       
      * **estimate** - This trait is used by the operation's :meth:`estimate` method.
        
      * **estimate_result** - This trait is set as a result of calling :meth:`estimate`.
     
      * **status** - Holds status variables like the number of events from the :mod:`ImportOp`.
    
      * **transient** - A temporary variable (not copied between processes or serialized).
    
    Attributes
    ----------
    
    handler_factory : Callable
        A callable that returns a GUI handler for the operation.  **MUST**
        be set in the derived class.
        
    do_estimate : Event
        Firing this event causes the operation's :meth:`estimate` method 
        to be called.
        
    changed : Event
        Used to transmit status information back from the operation to the
        workflow.  Set its value to a tuple (message, payload).  See 
        :class:`.workflow.Changed` for possible values of the message
        and their corresponding payloads.

    """
        
    # causes this operation's estimate() function to be called. observed in LocalWorkflow.
    do_estimate = Event

                
    def should_apply(self, changed, payload):
        """
        Should the owning WorkflowItem apply this operation when certain things
        change?  `changed` can be:
        
         - Changed.APPLY -- the parameters required to run apply() changed
         
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         
         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
         
        If `should_apply` is called from a notification handler, then `payload` is
        the `event` object.
        """

    
    def should_clear_estimate(self, changed, event):
        """
        Should the owning WorkflowItem clear the estimated model by calling
        op.clear_estimate()?  `changed` can be:
        
         - Changed.ESTIMATE -- the parameters required to call :meth:`estimate` 
         (ie traits with ``estimate = True`` metadata) have changed
            
         - Changed.PREV_RESULT -- the previous :class:`.WorkflowItem`'s result changed    
              
        If `should_clear_estimate` is called from a notificaiont handler, then `payload` is
        the `event` object.
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
            The index of the :class:`.WorkflowItem` that holds this operation.
            
        Returns
        -------
        string
            The Python code that calls this module.
        """
        

class WorkflowOperation(HasStrictTraits):
    """
    A default implementation of :class:`IWorkflowOperation`
    """
    
    # causes this operation's estimate() function to be called. observed in LocalWorkflow.
    do_estimate = Event
    
    def should_apply(self, changed, payload):
        return True

    
    def should_clear_estimate(self, changed, payload):
        return True
    
    
    def clear_estimate(self):
        raise NotImplementedError("clear_estimate was called but it's not implemented!")
        
    
    def get_notebook_code(self, idx):
        raise NotImplementedError("GUI plugins must override get_notebook_code()")
    

