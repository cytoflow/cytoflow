from cytoflow import Experiment
from traits.api import HasTraits, CFloat, Str
import pandas as pd
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation

@provides(IOperation)
class RangeOp(HasTraits):
    """Apply a range gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    xchannel : Str
        The name of the first channel to apply the range gate.
        
    xlow : Float
        The lowest value in xchannel to include in this gate.
        
    xhigh : Float
        The highest value in xchannel to include in this gate.
        
    ychannel : Str
        The name of the secon channel to apply the range gate.
        
    ylow : Float
        The lowest value in ychannel to include in this gate.
        
    yhigh : Float
        The highest value in ychannel to include in this gate.
    """
    
    # traits
    name = Str()
    
    xchannel = Str()
    xlow = CFloat()
    xhigh = CFloat()
    
    ychannel = Str()
    ylow = CFloat()
    yhigh = CFloat()
    
    def validate(self, experiment):
        """Validate this operation against an experiment."""
        
        if not self.xchannel or not self.ychannel:
            return False
        
        if (not self.xchannel in experiment.channels or
            not self.ychannel in experiment.channels):
            return False
        
        if (self.xlow < experiment[self.xchannel].min() or
            self.xhigh > experiment[self.xchannel].max() or
            self.ylow < experiment[self.ychannel].min() or
            self.yhigh > experiment[self.ychannel].max):
           return False
       
        return True
        
    def apply(self, old_experiment):
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
            raise RuntimeError("You have to set the Threshold gate's name "
                               "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in old_experiment.data.columns):
            raise RuntimeError("Experiment already contains a column {0}"
                               .format(self.name))
        
        
        new_experiment = old_experiment.clone()
        new_experiment[self.name] = \
            pd.Series(new_experiment[self.xchannel] > self.xlow and
                      new_experiment[self.xchannel] < self.xhigh and
                      new_experiment[self.ychannel] > self.ylow and
                      new_experiment[self.ychannel] < self.yhigh)
            
        return new_experiment
    
    def default_view(self, experiment):
        """Returns a histogram view with the threshold highlighted."""
        raise NotImplementedError
    