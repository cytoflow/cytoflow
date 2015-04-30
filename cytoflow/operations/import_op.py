'''
Created on Mar 20, 2015

@author: brian
'''
from traits.api import HasTraits, provides, Str, List, Bool, Instance, \
                       Property, property_depends_on, Int, Any, Float
from cytoflow.operations.i_operation import IOperation
from cytoflow import Experiment
import FlowCytometryTools as fc

class LogFloat(Float):
    """
    A trait to represent a numeric condition on a log scale.
    
    Since I can't figure out how to add metadata to a trait class (just an
    instance), we'll subclass it instead.  Don't need to override anything;
    all we're really looking to change is the name.
    """

class Tube(HasTraits):
    """
    The model for a tube in an experiment.
    """
    
    # these are the traits that every tube has.  every other trait is
    # dynamically created.  we use the 'condition' flag to keep track of whether
    # a trait should contribute to the tube's hash / equality, and whether
    # it ends up in the Experiment as a condition.
    
    File = Str(condition = False)
    Name = Str(condition = False)
    
    # this is backwards from most trait definitions.  any trait starting
    # with an underscore is automatically transient and not included in 
    # the hash and equality computations
    __ = Any(transient = True, condition = False)
    
    def __hash__(self):
        ret = int(0)
        for trait in self.trait_names(condition = True,
                                      transient = lambda x: x is not True):
            if not ret:
                ret = hash(self.trait_get(trait)[trait])
            else:
                ret = ret ^ hash(self.trait_get(trait)[trait])
                
        return ret
    
    def __eq__(self, other):
        for trait in self.trait_names(condition = True,
                                      transient = lambda x: x is not True):
            if not self.trait_get(trait)[trait] == other.trait_get(trait)[trait]:
                return False
                
        return True

@provides(IOperation)
class ImportOp(HasTraits):
    '''
    classdocs
    '''

    id = "edu.mit.synbio.cytoflow.operations.import"
    friendly_id = "Import"
    name = "Import Data"

    coarse = Bool(False)
    coarse_events = Int(1000)

    tubes = List(Tube)
          
    def is_valid(self, experiment = None):
        if not self.tubes:
            return False
        
        if len(self.tubes) == 0:
            return False
        
        for idx, i in enumerate(self.tubes[0:-2]):
            for j in self.tubes[idx+1:]:
                if i == j:
                    return False
                
#         tube0 = self.tubes[0]
#         for tube in self.tubes:
            
                
        # TODO - more error checking.  ie, does the File exist?  is it
        # readable?  etc etc.
                
        return True
      
    def apply(self, experiment = None):
        
        experiment = Experiment()

        trait_to_dtype = {"Str" : "category",
                          "Float" : "float",
                          "LogFloat" : "float",
                          "Bool" : "bool",
                          "Int" : "int"}
        
        # get rid of the name and path traits
        trait_names = Tube.class_trait_names(condition = True)
    
        for trait_name in trait_names:
            trait = Tube.class_traits()[trait_name]
            trait_type = trait.trait_type.__class__.__name__
        
            experiment.add_conditions({trait_name : trait_to_dtype[trait_type]})
            if trait_type == "LogFloat":
                experiment.metadata[trait_name]["repr"] = "Log"
        
        for tube in self.tubes:
            tube_fc = fc.FCMeasurement(ID=tube.Name, datafile=tube.File)
            experiment.add_tube(tube_fc, tube.trait_get(trait_names))
            
        return experiment
