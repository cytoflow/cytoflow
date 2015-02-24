'''
Created on Feb 15, 2015

@author: brian
'''
from FlowCytometryTools.core.transforms import Transformation
from traits.api import Instance, HasTraits, Str, ListStr, provides
from ..experiment import Experiment
from .i_operation import IOperation

@provides(IOperation)
class HlogTransformOp(HasTraits):
    
    # traits
    name = Str()
    channels = ListStr()
    _transform = Instance(Transformation)
    
    def apply(self, old_experiment):
        '''
        Applies the specified hlog transform to channels in an experiment
        '''
        
        new_experiment = Experiment(old_experiment)
        
        if(not self._transform): self._transform = Transformation("hlog")
        
        for channel in self.channels:
            new_experiment[channel] = self._transform(old_experiment[channel])

        return new_experiment