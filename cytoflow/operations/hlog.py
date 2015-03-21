from FlowCytometryTools.core.transforms import Transformation
from traits.api import HasTraits, Str, ListStr, provides
from ..experiment import Experiment 
from .i_operation import IOperation

@provides(IOperation)
class HlogTransformOp(HasTraits):
    """An operation that applies the Hyperlog transformation to channels.
    
    Attributes
    ----------
    name : Str
        The name of the transformation (for UI representation)
    channels : ListStr
        A list of the channels on which to apply the transformation
    
    References
    ----------
    .. [1] "Hyperlog-a flexible log-like transform for negative, 
           zero, and  positive valued data."
           Bagwell CB.
           Cytometry A. 2005 Mar;64(1):34-42.
           PMID: 15700280 [PubMed - indexed for MEDLINE] 
    """
    
    # traits
    id = "Hyperlog Transformation"
    name = Str()
    channels = ListStr()
    
    def valid(self, experiment):
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
        
        raise NotImplementedError
    
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
        
        transform = Transformation("hlog")
        
        for channel in self.channels:
            new_experiment[channel] = transform(old_experiment[channel])
            new_experiment.metadata[channel]["xforms"].append(transform)

        return new_experiment