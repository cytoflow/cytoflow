import numpy as np
from traits.api import HasStrictTraits, Str, ListStr, provides
from .i_operation import IOperation

@provides(IOperation)
class LogTransformOp(HasStrictTraits):
    """An operation that applies a natural log transformation to channels.
    
    Attributes
    ----------
    name : Str
        The name of the transformation (for UI representation)
    channels : ListStr
        A list of the channels on which to apply the transformation
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.log"
    friendly_id = "Natural Log"
    name = Str()
    channels = ListStr()
    
    def is_valid(self, experiment):
        """Validate this transform instance against an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            The Experiment against which to validate this op.
            
        Returns
        -------
        True if this is a valid operation on the given experiment; 
        False otherwise.
        """
        
        if not experiment:
            return False
        
        if not self.name:
            return False
        
        if not set(self.channels).issubset(set(experiment.channels)):
            return False
        
        return True
    
    def apply(self, old_experiment):
        """Applies the hlog transform to channels in an experiment.
        
        Parameters
        ----------
        old_experiment : Experiment
            The Experiment on which to apply this transformation.
            
        Returns
        -------
        Experiment
            A new Experiment, identical to old_experiment except for the
            transformed channels.
        """
        
        new_experiment = old_experiment.clone()
        
        for channel in self.channels:
            new_experiment[channel] = old_experiment[channel].apply(np.log10)
            
        new_experiment = new_experiment.data.dropna()
            
            # TODO - figure out transformation craps
            #new_experiment.metadata[channel]["xforms"].append(transform)

        return new_experiment