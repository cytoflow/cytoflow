'''
Created on Feb 9, 2015

@author: brian
'''

from ..experiment import Experiment
from traits.api import HasTraits, CFloat, Str
import pandas as pd
from traits.has_traits import provides
from synbio_flowtools.operations.i_operation import IOperation

@provides(IOperation)
class ThresholdOp(HasTraits):
    '''
    classdocs
    '''
    
    # traits
    name = Str()
    channel = Str()
    threshold = CFloat()

    def __init__(self, name="", channel = "", threshold = None):
        '''
        Builds a threshold operation instance.
        
        Args:
            name(string) : name of the operation.
            channel(string) : the channel to which the threshold should be applied
            threshold(float) : a float defining the threshold
        '''
    
        self.name = name
        self.channel = channel
        self.threshold = threshold
        
    def apply(self, old_experiment):
        '''
        Applies the threshold to an experiment.
        
        Args:
            old_experiment(Experiment): the experiment to which this op is applied
            
        Returns:
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.threshold;
            it is False otherwise.
        '''
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in old_experiment.data.columns):
            raise RuntimeError("Experiment already contains a column {0}"
                               .format(self.name))
        
        
        new_experiment = Experiment(old_experiment)
        new_experiment[self.name] = \
            pd.Series(new_experiment[self.channel] > self.threshold)
            
        return new_experiment
            
        
        
        
        
