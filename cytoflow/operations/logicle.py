from traits.api import HasStrictTraits, provides, Str, ListStr, Float, \
                       DictStrFloat
from logicle_ext.Logicle import Logicle
from .i_operation import IOperation
import math
import numpy as np

@provides(IOperation)
class LogicleTransformOp(HasStrictTraits):
    """An implementation of the Logicle scaling method.
    
    This scaling method implements a "linear-like" region around 0, and a
    "log-like" region for large values, with a very smooth transition between
    them.  It's particularly good for compensated data, and data where you have
    "negative" events (events with a fluorescence of ~0.)
    
    If you don't have any data around 0, you might be better of with a more
    traditional log scale or a Hyperlog.
    
    Attributes
    ----------
    name : Str 
        the name of this operation
    channels : ListStr 
        the channels on which to apply the operation
    T : dict(Str : float)
        for each channel, the maximum data value for this channel.  
        On a BD instrument, 2^18.
    W : dict(Str : float)
        for each channel, the width of the linear range, in log10 decades.  
        can estimate, or use a fixed value like 0.5.
    A : dict(Str : float) 
        for each channel, additional decades of negative data to include.  
        the display usually captures all the data, so 0 is fine to start.
    r : Float
        if estimating W, the quantile of negative data used to estimate W.  
        default 0.05 is a good choice.
        
    References
    ----------
    [1] A new "Logicle" display method avoids deceptive effects of logarithmic 
        scaling for low signals and compensated data.
        Parks DR, Roederer M, Moore WA.
        Cytometry A. 2006 Jun;69(6):541-51.
        PMID: 16604519
        http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.20258/full
        
    [2] Update for the logicle data scale including operational code 
        implementations.
        Moore WA, Parks DR.
        Cytometry A. 2012 Apr;81(4):273-7. 
        doi: 10.1002/cyto.a.22030 
        PMID: 22411901
        http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.22030/full
    """
    
    #traits
    id = "edu.mit.synbio.cytoflow.operations.logicle"
    friendly_id = "Logicle Transform"
    name = Str()
    channels = ListStr()
    
    T = DictStrFloat(desc = "the maximum data value.  for a BD instrument, 2^18.")
    W = DictStrFloat(desc="the width of the linear range, in log10 decades.")
    M = Float(4.5, 
              desc = "the width of the display in log10 decades")
    A = DictStrFloat(desc = "additional decades of negative data to include.")
    r = Float(0.05,
              desc = "quantile to use for estimating the W parameter.")
    
    def estimate(self, experiment, subset = None):
        """Estimate T, A and W per-channel from the data (given r.)
        
        Actually, that's not quite right.  Set T based on the maximum value in
        the FCS metadata; set A to 0.0; and estimate W given r.
        
        Parameters
        ----------
        experiment : Experiment
            the Experiment to use when estimating T, A and W.
        
        subset : string
            the subset of the Experiment to use; passed to 
            pandas.DataFrame.query()
        """
        
        if subset:
            data = experiment.query(subset)
        else:
            data = experiment.data
        
        for channel in self.channels:
            self.T[channel] = experiment.metadata[channel]['range']            
            self.A[channel] = 0.0
            
            # get the range by finding the rth quantile of the negative values
            neg_values = data[data[channel] < 0][channel]
            if(not neg_values.empty):
                r_value = neg_values.quantile(self.r).item()
                self.W[channel] = (self.M - math.log10(self.T[channel]/math.fabs(r_value)))/2
            else:
                # ... unless there aren't any negative values, in which case
                # you probably shouldn't use this transform
                raise RuntimeError("You shouldn't use the Logicle transform "
                                   "for channels without any negative data. "
                                   "Try a regular log10 transform instead.")
    
    def apply(self, old_experiment):
        """Applies the Logicle transform to channels"""
        
        # TODO - a little basic checking to make sure that T, W, M, A are
        # set for each channel, and okay (mirroring Logicle.cpp's initialize()
        # function .... because the errors that SWIG throws are not useful.
        #
        # or (and?) -- fix the SWIG error situation.
        
        new_experiment = old_experiment.clone()
        
        for channel in self.channels:
            el = Logicle(self.T[channel], 
                         self.W[channel], 
                         self.M,
                         self.A[channel])
            
            new_experiment[channel] = old_experiment[channel].apply(el.scale)
            new_experiment.metadata[channel]["xforms"].append(el)
            
        return new_experiment
    
    def is_valid(self, experiment):
        """ Validate this transformation against an experiment"""
        if not experiment:
            return False
        
        if not self.name:
            return False
        
        if not set(self.channels).issubset(set(experiment.channels)):
            return False
        
        if self.M <= 0 or self.r <= 0 or self.r >= 1:
            return False
        
        for channel in self.channels:
            # the Logicle C++/SWIG extension is REALLY picky about it
            # being a double
            
            if experiment[channel].dtype != np.float64:
                return False
            
            # Logicle works best if there's some data < 0.
            # TODO: how to report this if it's not true?
            neg_values = experiment[experiment[channel] < 0][channel]
            if neg_values.empty:
                return False
            
            if not channel in self.T or self.T[channel] <= 0:
                return False
            
            if not channel in self.W or self.W[channel] <= 0:
                return False
            
            if not channel in self.A or self.A[channel] < 0:
                return False
            
        return True