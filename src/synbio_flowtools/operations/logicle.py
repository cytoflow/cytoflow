"""
Created on Feb 10, 2015

@author: brian
"""
from ..experiment import Experiment
from traits.api import HasTraits, CFloat, Str, ListStr
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
    

    def __init__(self, params):
        """
        Constructor
        """
        