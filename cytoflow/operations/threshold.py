from traits.api import HasStrictTraits, CFloat, Str, CStr, provides
import pandas as pd

from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError

@provides(IOperation)
class ThresholdOp(HasStrictTraits):
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
        
    Examples
    --------
    >>> thresh = flow.ThresholdOp()
    >>> thresh.name = "Y2-A+"
    >>> thresh.channel = 'Y2-A'
    >>> thresh.threshold = 0.3
    >>> 
    >>> ex3 = thresh.apply(ex2)    
    
    Alternately, in an IPython notebook with `%matplotlib notebook`
    
    >>> h = flow.HistogramView()
    >>> h.channel = 'Y2-A'
    >>> h.huefacet = 'Dox'
    >>> ts = flow.ThresholdSelection(view = h)
    >>> ts.plot(ex2)
    >>> ts.interactive = True
    >>> # .... draw a threshold on the plot
    >>> thresh = flow.ThresholdOp(name = "Y2-A+",
    ...                           channel = "Y2-A",
    ...                           thresh.threshold = ts.threshold)
    >>> ex3 = thresh.apply(ex2)
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.threshold"
    friendly_id = "Threshold"
    
    name = CStr()
    channel = Str()
    threshold = CFloat()
        
    def apply(self, experiment):
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
            raise CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise CytoflowOpError("Experiment already contains a column {0}"
                               .format(self.name))
            
        if self.channel not in experiment.channels:
            raise CytoflowOpError("{0} isn't a channel in the experiment"
                                  .format(self.channel))
        
        
        new_experiment = experiment.clone()
        new_experiment[self.name] = \
            pd.Series(new_experiment[self.channel] > self.threshold)
            
        new_experiment.conditions[self.name] = "bool"
        new_experiment.metadata[self.name] = {}
            
        return new_experiment
