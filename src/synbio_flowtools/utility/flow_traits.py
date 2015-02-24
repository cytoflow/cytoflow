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
    """

    default_value = None

    def is_valid(self, object, name, value):
        experiment = object.experiment
        