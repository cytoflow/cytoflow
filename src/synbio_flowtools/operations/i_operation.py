"""
Created on Feb 15, 2015

@author: brian
"""
from traits.api import Interface, Str

class IOperation(Interface):
    """
    classdocs
    """
    
    # interface traits
    name = Str
    
    def validate(self, experiment):
        """
        Validate the parameters of this operation given an Experiment.
        
        For example, make sure that all the channels this op asks for 
        exist; or that the subset string for a data-driven op is valid.
        
        Args:
            experiment(Experiment): the Experiment to validate this op against
            
        Returns:
            True if this op will work; False otherwise.
        """
        
        return False   # make sure this gets implemented.
            
    
    def apply(self, experiment):
        """
        Apply an operation to an experiment.
        
        Args:
            old_experiment(Experiment): the Experiment to apply this op to
                    
        Returns:
            A new Experiment: the old Experiment with this operation applied
        """
        return None   # make sure this gets implemented
    
