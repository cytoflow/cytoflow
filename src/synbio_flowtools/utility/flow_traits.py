'''
Created on Feb 15, 2015

@author: brian
'''
from traits.trait_handlers import TraitType

class Channel(TraitType):
    """
    A Trait that specifies a valid channel for an operation or view.
    
    Requires an Instance(Experiment) trait named "experiment" to be defined
    on any object on which a Channel is defined.  This allows for validation,
    and also for construction of an appropriate TraitsUI editor.
    
    TODO - do we actually need this?  at the moment, I think I want to push
    validation to (a) op/view validate() function, and (b) to a ModelView class
    so that the TraitUI Views get built with pre-validated inputs.
    """

    default_value = None

    def is_valid(self, object, name, value):
        experiment = object.experiment
        return False
        
        
class SubsetStr(TraitType):
    """
    A Trait that specifies a string for pandas.DataFrame.query().
    
    Must be a valid numexpr-compilable string.  We can validate it against
    an Instance(Experiment) trait named "experiment" defined on the same
    object as this trait.  Also allows for the construction of an appropriate
    TraitsUI editor.
    """
    
    default_value = None
    
    def is_valid(self, object, name, value):
        return False
