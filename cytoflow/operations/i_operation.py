from traits.api import Interface, Str

class IOperation(Interface):
    """The basic interface for an operation on cytometry data.
    
    Attributes
    ----------
    id : Str
        a unique identifier for this class. prefix: edu.mit.synbio.cytoflow.operations
        
    friendly_id : Str
        The operation's human-readable id (like "Logicle" or "Hyperlog").  Used
        for UI implementations.
        
    name : Str
        The name of this IOperation instance (like "Debris Filter").  Useful for
        UI implementations; sometimes used for naming gates' metadata
    """
    
    # interface traits
    id = Str
    friendly_id = Str
    name = Str
        
    def estimate(self, experiment, subset = None):
        """Estimate this operation's parameters from some data.
        
        For operations that are data-driven (for example, a mixture model,
        or the Logicle transform), estimate the operation's parameters from
        an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the Experiment to use in the estimation.
        
        subset : Str (optional)
            a string passed to pandas.DataFrame.query() to select the subset
            of data on which to run the parameter estimation.
            
        Raises
        ------
        CytoflowOpException
            If the operation can't be be completed because of bad op
            parameters.
        """ 
    
    def apply(self, experiment):
        """
        Apply an operation to an experiment.
        
        Parameters
        ----------
            experiment : Experiment
                the Experiment to apply this op to
                    
        Returns
        -------
            Experiment
                the old Experiment with this operation applied
                
        Raises
        ------
        CytoflowOpException
            If the operation can't be be completed because of bad op
            parameters.
        """
        
    def default_view(self):
        """
        Many operations have a "default" view.  This can either be a diagnostic
        for the operation's estimate() method, an interactive for setting
        gates, etc.  Frequently it makes sense to link the properties of the
        view to the properties of the IOperation; sometimes, *default_view()*
        is the only way to get the view (ie, it's not useful when it doesn't
        reference an IOperation instance.)
        
        Returns
        -------
            IView
                the IView instance
        """
        