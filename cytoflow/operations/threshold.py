from cytoflow import Experiment
from traits.api import HasTraits, CFloat, Str
import pandas as pd
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation

@provides(IOperation)
class ThresholdOp(HasTraits):
    """Apply a threshold to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    channel : Str
        The name of the channel to apply the threshold on.
        
    threshold : Float
        The value at which to threshold this channel.
    """
    
    # traits
    id = "Threshold Gate"
    name = Str()
    channel = Str()
    threshold = CFloat()
    
    def validate(self, experiment):
        """Validate this operation against an experiment."""
        if not experiment:
            return False
        
        if self.channel not in experiment.channels:
            return False
        
        if (self.threshold > experiment[self.channel].max() or
            self.threshold < experiment[self.channel].min()):
            return False
        
        return True
        
    def apply(self, old_experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        old_experiment : Experiment
            the experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.threshold;
            it is False otherwise.
        """
        
        # make sure name got set!
        if not self.name:
            raise RuntimeError("You have to set the Threshold gate's name "
                               "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in old_experiment.data.columns):
            raise RuntimeError("Experiment already contains a column {0}"
                               .format(self.name))
        
        
        new_experiment = old_experiment.clone()
        new_experiment[self.name] = \
            pd.Series(new_experiment[self.channel] > self.threshold)
            
        return new_experiment
    
    def default_view(self, experiment):
        """Returns a histogram view with the threshold highlighted."""
        raise NotImplementedError
    