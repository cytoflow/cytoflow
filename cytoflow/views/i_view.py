'''
Created on Feb 23, 2015

@author: brian
'''

from traits.api import Interface, Str, List
from matplotlib.pyplot import plot

class IView(Interface):
    """An interface for a visualization of flow data.
    
    Could be a histogram, a density plot, a scatter plot, a statistical
    visualization like a bar chart of population means; even a textual 
    representation like a table.
    
    Attributes
    ----------
    name : Str
        The name of this view: for UI, etc.  NOT user-specified (like the
        IOperation name is), but set by the programmer!
        
    id : Str
        A unique id for this view, for application logic etc.
        
    subset : Str
        A string specifying the subset of the data to be plotted.
        Passed to pandas.DataFrame.query().
    """
    

    name = Str
    id = Str       
    subset = Str
    
    def validate(self, experiment):
        """Validate the parameters of this view, given a test Experiment.
        
        For example, make sure that all the channels this op asks for 
        exist; or that the subset string for a data-driven op is valid.
        
        Parameters
        ----------
        experiment : Experiment 
            the Experiment to validate this op against
            
        Returns
        -------
            True if this op will work; False otherwise.
        """
    
    def plot(self, experiment, **kwargs):
        """Plot a visualization of flow data.
        
        Parameters
        ----------
        experiment : Experiment 
            the Experiment containing the data to plot
        kwargs : dict
            additional arguments to pass to the underlying plotting function.
        """
    