"""
Created on Feb 10, 2015

@author: brian
"""
from ..experiment import Experiment
from traits.api import HasTraits, CFloat, Str, ListStr, provides
import pandas as pd
from synbio_flowtools.operations.i_operation import IOperation

@provides(IOperation)
class LogicleTransformOp(HasTraits):
    """
    Transforms the specified channels using the Logicle display method.
    
    Better than biexponential; parameters can be learned from data.
    
    Ref:
    A new "Logicle" display method avoids deceptive effects of logarithmic
    scaling for low signals and compensated data.
    Parks DR, Roederer M, Moore WA.
    Cytometry A. 2006 Jun;69(6):541-51.
    PMID: 16604519
    http://www.ncbi.nlm.nih.gov/pubmed/16604519
    
    and
    
    Update for the logicle data scale including operational code implementations
    Wayne A. Moore and David R. Parks
    Cytometry Part A
    Volume 81A, Issue 4, pages 273–277, April 2012
    http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.22030
    """
    
    # traits
    name = Str()
    channels = ListStr()

    def apply(self, old_experiment):
        
        new_experiment = Experiment(old_experiment)
        
        for channel in self.channels:
            pass
        
    def logicle_fn(self):
        pass
    
    def logicle_invert_fn(self):
        pass
    
