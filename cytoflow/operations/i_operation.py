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
    
    def is_valid(self, experiment):
        """Validate the parameters of this operation given an Experiment.
        
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
        
        # TODO - return something other than T/F (throw an exception, maybe?)
        # telling what, exactly, was wrong.  (File not found; bad channel names;
        # bad params; etc.)
        
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
        
        """ 
    
    def apply(self, experiment):
        """
        Apply an operation to an experiment.
        
        Parameters
        ----------
            old_experiment : Experiment
                the Experiment to apply this op to
                    
        Returns
        -------
            Experiment
                the old Experiment with this operation applied
        """