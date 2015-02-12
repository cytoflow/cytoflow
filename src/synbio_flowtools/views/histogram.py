"""
Created on Feb 10, 2015

@author: brian
"""


from ..experiment import Experiment
from traits.api import HasTraits, CFloat, Str
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns


class HistogramView(HasTraits):
    """
    Plots a one-channel histogram
    
    Traits:
        name: The HistogramView name (for serialization, etc.)
        channel: the flow channel we're plotting
        xfacet: the conditioning variable for multiple plots (horizontal)
        yfacet: the conditioning variable for multiple plots (vertical)
        huefacet: the conditioning variable for multiple plots (color)
        subset: a string passed to pandas.DataFrame.query() to subset the
            data before we plot it.
    """
    
    # traits    
    name = Str()
    channel = Str()
    xfacet = Str()
    yfacet = Str()
    huefacet = Str()
    subset = Str()

    def __init__(self, experiment):
        """
        Builds a new Histogram view.
        
        Args:
            experiment: an Experiment instance.
        """
        
    def plot(self):
        """
        Plot a faceted histogram view of 
        """
        pass
    