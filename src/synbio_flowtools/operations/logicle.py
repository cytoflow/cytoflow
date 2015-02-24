"""
Created on Feb 16, 2015

@author: brian


Refs:
A new "Logicle" display method avoids deceptive effects of logarithmic scaling 
for low signals and compensated data.
Parks DR, Roederer M, Moore WA.
Cytometry A. 2006 Jun;69(6):541-51.
PMID: 16604519
http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.20258/full

and 

Update for the logicle data scale including operational code implementations.
Moore WA, Parks DR.
Cytometry A. 2012 Apr;81(4):273-7. doi: 10.1002/cyto.a.22030. Epub 2012 Mar 12. 
PMID: 22411901
http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.22030/full
"""

from traits.api import HasTraits, provides, Str, ListStr, Float, DictStrFloat
from logicle_ext.Logicle import Logicle
from .i_operation import IOperation
from ..experiment import Experiment

@provides(IOperation)
class LogicleTransformOp(HasTraits):
    """
    An implementation of the Logicle scaling method.
    """
    
    #traits
    name = Str()
    channels = ListStr()
    
    T = DictStrFloat(desc = "the maximum data value.  for a BD instrument, 2^18.")
    W = DictStrFloat(desc="the width of the linear range.")
    M = Float(4.5, 
              desc = "the width of the display in log decades")
    A = DictStrFloat(desc = "additional decades of negative data to include.")
    r = Float(0.05,
              desc = "quantile to use for estimating the W parameter.")
    
    def estimateParameters(self, experiment):
        for channel in self.channels:
            # get the range by finding the rth quantile of the negative values
            neg_values = experiment[experiment[channel] < 0][channel]
            if(not neg_values.empty):
                self.W[channel] = -2 * neg_values.quantile(self.r).item()
            else:
                # ... unless there aren't any negative values, in which case
                # you probably shouldn't use this transform
                # TODO - raise an exception instead
                self.W[channel] = experiment[channel].quantile(0.5).item()
            
            # get the maximum range for T
            # should be the same for each tube, so we'll just suck it off
            # the first one.
            # TODO - should this be experiment[channel].max()?
            keywords = experiment.tube_keywords.itervalues().next()
            self.T[channel] = float(keywords[keywords["$PnN"] == channel]["$PnR"].item())
            
            self.A[channel] = 0.0
                          
    
    def apply(self, old_experiment):
        """
        Applies the Logicle transform to channels
        """
        
        new_experiment = Experiment(old_experiment)
        
        for channel in self.channels:
            el = Logicle(self.T[channel], 
                         self.W[channel], 
                         self.M,
                         self.A[channel])
            
            new_experiment[channel] = old_experiment.apply(el.scale)
            
        return new_experiment
    
    def scale(self, x):
        pass
    
    def invert(self, x):
        pass

