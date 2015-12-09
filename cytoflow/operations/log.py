import numpy as np
import pandas as pd
from traits.api import HasStrictTraits, Str, List, Enum, Float, Constant, \
                       provides
from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError

@provides(IOperation)
class LogTransformOp(HasStrictTraits):
    """
    An operation that applies a natural log10 transformation to channels.
    
    It can be configured to mask or clip values less than some threshold.  
    The log10 transform is sometimes okay for basic visualization, but
    most analyses should be using `HlogTransformOp` or `LogicleTransformOp`. 
    
    Attributes
    ----------
    name : Str
        The name of the transformation (for UI representation; optional for
        interactive use)
        
    channels : List(Str)
        A list of the channels on which to apply the transformation
        
    mode : Enum("mask", "clip") (default = "mask")
        If `mask`, events with values <= `self.threshold` *in any channel* in
        `channels` are dropped.  If `clip`, values <= `self.threshold` are 
        transformed to `log10(self.threshold)`.
    
    threshold : Float (default = 1.0)
        The threshold for masking or truncation.
        
    Examples
    --------
    >>> tlog = flow.LogTransformOp()
    >>> tlog.channels =["V2-A", "Y2-A", "B1-A"]
    >>> ex2 = tlog.apply(ex)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.log')
    friendly_id = Constant("Log10")

    name = Str()
    channels = List(Str)
    mode = Enum("mask", "truncate")
    threshold = Float(1.0)
    
    def apply(self, experiment):
        """Applies the log10 transform to channels in an experiment.
        
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
        
        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        exp_channels = [x for x in experiment.metadata 
                        if 'type' in experiment.metadata[x] 
                        and experiment.metadata[x]['type'] == "channel"]
        
        if not set(self.channels).issubset(set(exp_channels)):
            raise CytoflowOpError("The op channels aren't in the experiment")
        
        if self.threshold <= 0:
            raise CytoflowOpError("op.threshold must be > 0")
        
        new_experiment = experiment.clone()
        
        data = new_experiment.data
        
        if self.mode == "mask":
            gt = pd.Series([True] * len(data.index))
        
            for channel in self.channels:
                gt = np.logical_and(gt, data[channel] > self.threshold)        

            data = data.loc[gt]
            data.reset_index(inplace = True, drop = True)
            
        new_experiment.data = data
        
        log_fwd = lambda x, t = self.threshold: \
            np.where(x <= t, np.log10(t), np.log10(x))
        
        log_rev = lambda x: 10**x
        
        for channel in self.channels:
            new_experiment[channel] = log_fwd(new_experiment[channel])
            
            new_experiment.metadata[channel]["xforms"].append(log_fwd)
            new_experiment.metadata[channel]["xforms_inv"].append(log_rev)

        return new_experiment
