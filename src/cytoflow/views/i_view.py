'''
Created on Feb 23, 2015

@author: brian
'''

from traits.api import Interface, Str, List
from matplotlib.pyplot import plot

class IView(Interface):
    """
    An interface for a visualization of flow data.
    
    Could be a histogram, a density plot, a scatter plot, a statistical
    visualization like a bar chart of population means; even a textual 
    representation like a table.
    """
    
    # interface traits
    
    # the name of the view
    name = Str       
    
    # a string describing the subset being plotted.  passed to DataFrame.query()
    subset = Str
    
    def validate(self, experiment):
        """
        Validate the parameters of this view, given a test Experiment.
        
        For example, make sure that all the channels this op asks for 
        exist; or that the subset string for a data-driven op is valid.
        
        Args:
            experiment(Experiment): the Experiment to validate this op against
            
        Returns:
            True if this op will work; False otherwise.
        """
        
        raise NotImplementedError
    
    def plot(self, experiment, **kwargs):
        """
        Plot a visualization of flow data.
        
        Args:
            experiment: the Experiment containing the data to plot
            kwargs: additional arguments to pass to the underlying plotting
                function.
                
        Returns: nothing.
        """
        raise NotImplementedError
    