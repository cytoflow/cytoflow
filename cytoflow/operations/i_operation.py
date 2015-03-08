from traits.api import Interface, Str

class IOperation(Interface):
    """The basic interface for an operation on cytometry data.
    
    Attributes
    ----------
    name : Str
        The name of the operation.  Useful for UI implementations; sometimes
        used for naming gates' metadata
    """
    
    # interface traits
    name = Str
    
    def validate(self, experiment):
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
        
    def estimate(self, experiment, subset):
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
    
    def getDefaultView(self, experiment):
        """Get an IView suited to viewing the results of this operation.
        
        Parameters
        ----------
            experiment : Experiment 
                The Experiment we're viewing
            
        Returns
        -------
            a new IView instance, suitable for calling plot(experiment) on.
        """
    
