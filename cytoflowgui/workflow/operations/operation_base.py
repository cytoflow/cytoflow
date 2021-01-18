'''
Created on Jan 15, 2021

@author: brian
'''

from traits.api import HasStrictTraits
from cytoflow.operations import IOperation

class IWorkflowOperation(IOperation):
    
    """
    An interface that extends an :mod:`cytoflow` operation with functions 
    required for GUI support.
    
    In addition to implementing the interface below, another common thing to 
    do in the derived class is to override traits of the underlying class in 
    order to add metadata that controls their handling by the workflow.  
    Currently, relevant metadata include:
    
      * **transient** - don't copy the trait between the local (GUI) process 
        and the remote (computation) process (in either direction).
     
      * **status** - only copy from the remote process to the local process,
        not the other way 'round.
       
      * **estimate** - copy from the local process to the remote process,
        but don't call :meth:`apply`.  (used for traits that are involved in
        estimating the operation's parameters.)
      
      * **fixed** - assigned when the operation is first created in the
        remote process *and never subsequently changed.*
    
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
    
    #handler_factory = Callable(unimplemented)
    
    # causes this operation's estimate() function to be called
    # do_estimate = Event
    
    # transmit some changing status back to the workflow
    #changed = Event
    
                
    def should_apply(self, changed, payload):
        """
        Should the owning WorkflowItem apply this operation when certain things
        change?  `changed` can be:
        
         - Changed.OPERATION -- the operation's parameters changed
         
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         
         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
        """

    
    def should_clear_estimate(self, changed, payload):
        """
        Should the owning WorkflowItem clear the estimated model by calling
        op.clear_estimate()?  `changed` can be:
        
         - Changed.ESTIMATE -- the parameters required to call :meth:`estimate` 
         (ie traits with ``estimate = True`` metadata) have changed
            
         - Changed.PREV_RESULT -- the previous :class:`.WorkflowItem`'s result changed
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
    
    def should_apply(self, changed, payload):
        return True

    
    def should_clear_estimate(self, changed, payload):
        return True
    
    
    def clear_estimate(self):
        raise NotImplementedError("clear_estimate was called but it's not implemented!")
        
    
    def get_notebook_code(self, idx):
        raise NotImplementedError("GUI plugins must override get_notebook_code()")
    

