from traits.api import HasStrictTraits, CFloat, Str, CStr, provides
from .i_operation import IOperation
from ..utility import CytoflowOpError
from cytoflow.utility.util import CytoflowOpError

@provides(IOperation)
class RangeOp(HasStrictTraits):
    """Apply a range gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    channel : Str
        The name of the channel to apply the range gate.
        
    low : Float
        The lowest value to include in this gate.
        
    high : Float
        The highest value to include in this gate.
        
    Examples
    --------
    >>> range = flow.RangeOp()
    >>> range.name = "Y2-A+"
    >>> range.channel = 'Y2-A'
    >>> range.low = 0.3
    >>> range.high = 0.8
    >>> 
    >>> ex3 = range.apply(ex2)
    
    Alternately  (in an IPython notebook with `%matplotlib notebook`)
    
    >>> h = flow.HistogramView()
    >>> h.channel = 'Y2-A'
    >>> rs = flow.RangeSelection(view = h)
    >>> rs.plot(ex2)
    >>> rs.interactive = True
    >>> # ... draw a range on the plot ....
    >>> range.low, range.high = rs.low, rs.high
    >>> ex3 = range.apply(ex2)
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.range"
    friendly_id = "Range"
    
    name = CStr()
    channel = Str()
    low = CFloat()
    high = CFloat()
        
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.low and
            less than self.high; it is False otherwise.
        """

        # make sure name got set!
        if not self.name:
            raise CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")

        if self.name in experiment.data.columns:
            raise CytoflowOpError("Experiment already has a column named {0}"
                                  .format(self.name))
        
        if not self.channel:
            raise CytoflowOpError("Channel not specified")
        
        if not self.channel in experiment.channels:
            raise CytoflowOpError("Channel {0} not in the experiment"
                                  .format(self.channel))
        
        if self.high <= self.low:
            raise CytoflowOpError("range high must be > range low")
        
        if self.high <= experiment[self.channel].min():
            raise CytoflowOpError("range high must be > {0}"
                                  .format(experiment[self.channel].min()))
        if self.low >= experiment[self.channel].max:
            raise CytoflowOpError("range low must be < {0}"
                                  .format(experiment[self.channel].max()))
        
        new_experiment = experiment.clone()
        new_experiment[self.name] = \
            new_experiment[self.channel].between(self.low, self.high)
            
        new_experiment.conditions[self.name] = "bool"
        new_experiment.metadata[self.name] = {}
            
        return new_experiment
    