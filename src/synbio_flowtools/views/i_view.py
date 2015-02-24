'''
Created on Feb 23, 2015

@author: brian
'''

from traits.api import Interface, Str
from matplotlib.pyplot import plot

class IView(Interface):
    """
    An interface for a visualization of flow data.
    
    Could be a histogram, a density plot, a scatter plot, a statistical
    visualization like a bar chart of population means; even a textual 
    representation like a table.
    """
    
    # interface traits
    name = Str
    subset = Str
    
    def plot(self, experiment, axes = None, **kwargs):
        """
        Plot a visualization of flow data.
        
        Args:
            experiment: the Experiment containing the data to plot
            axes: a matplotlib set of axes to plot on.  if none given, plot to
                pyplot's current set of axes
            kwargs: additional arguments to pass to the underlying plotting
                function.
        
        """
        pass
    