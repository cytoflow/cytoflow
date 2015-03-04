"""
Created on Feb 10, 2015

@author: brian
"""


from ..experiment import Experiment
from traits.api import HasTraits, Str, Instance, provides
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from synbio_flowtools.views.i_view import IView

@provides(IView)
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
    name = Str
    channel = Str
    xfacet = Str
    yfacet = Str
    huefacet = Str
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted histogram view of a channel
        """
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('bins', 200) # Do not move above
        
        if not self.subset:
            x = experiment.data
        else:
            x = experiment.query(self.subset)

        # FacetGrid makes its own figure
        g = sns.FacetGrid(x, 
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None))
        
        g.map(plt.hist, self.channel, **kwargs)
        
        
            
        
    