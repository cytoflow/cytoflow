from traits.api import HasStrictTraits, provides, Str, List, Float, Dict, \
                        Constant
import math
import numpy as np

from cytoflow.utility import CytoflowOpError
from logicle_ext.Logicle import Logicle
from cytoflow.operations import IOperation

@provides(IOperation)
class LogicleTransformOp(HasStrictTraits):
    """
    An implementation of the Logicle scaling method.
    
    This scaling method implements a "linear-like" region around 0, and a
    "log-like" region for large values, with a very smooth transition between
    them.  It's particularly good for compensated data, and data where you have
    "negative" events (events with a fluorescence of ~0.)
    
    If you don't have any data around 0, you might be better of with a more
    traditional log scale or a Hyperlog.
    
    The transformation has one parameter, `W`, which specifies the width of
    the "linear" range in log10 decades.  You can estimate an "optimal" value 
    with `estimate()`, or you can set it to a fixed value like 0.5.
    
    Attributes
    ----------
    name : Str 
        the name of this operation
    channels : List(Str) 
        the channels on which to apply the operation
    W : Dict(Str : float)
        for each channel, the width of the linear range, in log10 decades.  
        can estimate, or use a fixed value like 0.5.
    M : Float (default = 4.5)
        The width of the entire display, in log10 decades
    A : Dict(Str : float) 
        for each channel, additional decades of negative data to include.  
        the display usually captures all the data, so 0 is fine to start.
    r : Float
        if estimating W, the quantile of negative data used to estimate W.  
        default 0.05 is a good choice.
        
    Examples
    --------
    >>> logicle = flow.LogicleTransformOp()
    >>> logicle.channels =["V2-A", "Y2-A", "B1-A"]
    >>> logicle.estimate(ex)
    >>> ex2 = logicle.apply(ex)
        
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
    id = Constant('edu.mit.synbio.cytoflow.operations.logicle')
    friendly_id = Constant("Logicle Transform")
    
    name = Str()
    channels = List(Str)
    
    W = Dict(Str, Float, desc="the width of the linear range, in log10 decades.")
    M = Float(4.5, desc = "the width of the display in log10 decades")
    A = Dict(Str, Float, desc = "additional decades of negative data to include.")
    r = Float(0.05, desc = "quantile to use for estimating the W parameter.")
    
    def estimate(self, experiment, subset = None):
        """Estimate A and W per-channel from the data (given r.)
        
        Actually, that's not quite right. Set A to 0.0; and estimate W given r.
        
        Parameters
        ----------
        experiment : Experiment
            the Experiment to use when estimating T, A and W.
        
        subset : string
            the subset of the Experiment to use; passed to 
            pandas.DataFrame.query()
        """

        if not experiment:
            raise CytoflowOpError("no experiment specified")
        
        if self.r <= 0 or self.r >= 1:
            raise CytoflowOpError("r must be between 0 and 1")
        
        if subset:
            data = experiment.query(subset)
        else:
            data = experiment.data
        
        for channel in self.channels:          
            t = experiment.metadata[channel]['range']
            self.A[channel] = 0.0
            
            # get the range by finding the rth quantile of the negative values
            neg_values = data[data[channel] < 0][channel]
            if(not neg_values.empty):
                r_value = neg_values.quantile(self.r).item()
                self.W[channel] = (self.M - math.log10(t/math.fabs(r_value)))/2
            else:
                # ... unless there aren't any negative values, in which case
                # you probably shouldn't use this transform
                raise CytoflowOpError("You shouldn't use the Logicle transform "
                                      "for channels without any negative data. "
                                      "Try a hlog or a log10 transform instead.")
    
    def apply(self, experiment):
        """Applies the Logicle transform to channels"""
        
        if not experiment:
            raise CytoflowOpError("no experiment specified")
        
        exp_channels = [x for x in self.metadata 
                        if 'type' in self.metadata[x] 
                        and self.metadata[x]['type'] == "channel"]
        
        if not set(self.channels).issubset(set(exp_channels)):
            raise CytoflowOpError("self.channels isn't a subset "
                                  "of experiment.channels")
        
        if self.M <= 0:
            raise CytoflowOpError("M must be > 0")

        for channel in self.channels:
            # the Logicle C++/SWIG extension is REALLY picky about it
            # being a double
            
            if experiment[channel].dtype != np.float64:
                raise CytoflowOpError("The dtype for channel {0} MUST be "
                                      "np.float64.  Please submit a bug report."
                                      .format(channel))
            
            if not channel in self.W: 
                raise CytoflowOpError("W wasn't set for channel {0}"
                                      .format(channel))
                
            if self.W[channel] <= 0:
                raise CytoflowOpError("W for channel {0} must be > 0"
                                      .format(channel))
            
            if not channel in self.A:
                raise CytoflowOpError("A wasn't set for channel {0}"
                                      .format(channel))
                
            if self.A[channel] < 0:
                raise CytoflowOpError("A for channel {0} must be >= 0"
                                      .format(channel))
        
        new_experiment = experiment.clone()
        
        for channel in self.channels:
            
            el = Logicle(new_experiment.metadata[channel]['range'], 
                         self.W[channel], 
                         self.M,
                         self.A[channel])
            
            logicle_fwd = lambda x: x.apply(el.scale)
            logicle_rev = lambda x: x.apply(el.inverse)
            
            new_experiment[channel] = logicle_fwd(new_experiment[channel])
            new_experiment.metadata[channel]["xforms"].append(logicle_fwd)
            new_experiment.metadata[channel]["xforms_inv"].append(logicle_rev)
            
        return new_experiment
