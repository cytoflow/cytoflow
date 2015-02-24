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
    
    def apply(self, old_experiment):
        """
        Apply an operation to an experiment.
        
        Args:
            old_experiment(Experiment): the Experiment to apply this op to
                    
        Returns:
            A new Experiment: the old Experiment with this operation applied
        """
        pass
    
