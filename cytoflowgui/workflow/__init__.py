    
class Changed(object):
    # the operation's parameters needed to apply() changed.  
    # payload:
    # - the name of the changed trait
    # - the new trait value
    APPLY = "APPLY"
     
    # the operation's parameters to estimate() changed   
    # payload:
    # - the name of the changed trait
    # - the new trait value
    ESTIMATE = "ESTIMATE"    
     
    # the current view's parameters have changed
    # payload:
    # - the IView object that changed
    # - the name of the changed trait
    # - the new trait value 
    VIEW = "VIEW"         
     
    # the result of calling estimate() changed
    # payload: unused
    ESTIMATE_RESULT = "ESTIMATE_RESULT"  
     
    # some operation status info changed
    # payload:
    # - the name of the changed trait
    # - the new trait value
    OP_STATUS = "OP_STATUS"     
     
    # some view status changed
    # payload:
    # - the IView object that changed
    # - the name of the changed trait
    # - the new trait value
    # FIXME this is really only for exporting a table view -- 
    #       but we have the statistics locally too!  so just export from there.
    # VIEW_STATUS = "VIEW_STATUS" 
     
    # the result of calling apply() changed
    # payload: unused
    RESULT = "RESULT"        
     
    # the previous WorkflowItem's result changed
    # payload: unused
    PREV_RESULT = "PREV_RESULT"  


from .workflow import LocalWorkflow, RemoteWorkflow
from .workflow_item import WorkflowItem
