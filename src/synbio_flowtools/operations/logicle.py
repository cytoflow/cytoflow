"""
Created on Feb 10, 2015

@author: brian
"""
from ..experiment import Experiment
from traits.api import HasTraits, CFloat, Str, ListStr, Float
import pandas as pd

class LogicleTransformOp(object):
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
    """
    
    # traits
    name = Str()
    channels = ListStr()
    
    T = Float()     # the maximum (linear) data value to be displayed
    M = Float(4.5)  # the width of the display (in decades)
    W = Float()     # the width of the linear region (in decades).  
                    # usually 0.5 <= W <= 1.5  estimated from the data as
                    # 2*r, where r is the 5th percentile of the negative
                    # values.  TODO - what if there aren't any negative values?  
                    # what's a good default?

    def __init__(self, Experiment):
        """
        Constructor
        """
    
    def apply(self, x):
    
    def scale(self, x):
        pass
    
    def invert(self, x):
        pass