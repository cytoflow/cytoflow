'''
Created on Mar 20, 2015

@author: brian
'''
from traits.api import HasTraits, provides, Str, List, Bool, Instance, \
                       Property, property_depends_on, Int, Any
from cytoflow.operations.i_operation import IOperation
from cytoflow import Experiment
import FlowCytometryTools as fc

class Tube(HasTraits):
    """
    The model for a tube in an experiment.
    """
    
    # these are the traits that every tube has.  every other trait is
    # dynamically created.  we use the transient flag to keep track of whether
    # a trait should contribute to the tube's hash / equality, and whether
    # it ends up in the Experiment as a condition.
    
    File = Str(transient = True)
    Name = Str(transient = True)
    
    # this is backwards from most trait definitions.  any trait starting
    # with an underscore is automatically transient and not included in 
    # the hash and equality computations
    __ = Any(transient = True)
    
    def __hash__(self):
        ret = int(0)
        for trait in self.trait_names(transient = lambda x: x is not True):
            if not ret:
                ret = hash(self.trait_get(trait)[trait])
            else:
                ret = ret ^ hash(self.trait_get(trait)[trait])
                
        return ret
    
    def __eq__(self, other):
        for trait in self.trait_names(transient = lambda x: x is not True):
            if not self.trait_get(trait)[trait] == other.trait_get(trait)[trait]:
                return False
                
        return True

@provides(IOperation)
class ImportOp(HasTraits):
    '''
    classdocs
    '''

    id = "edu.mit.synbio.cytoflow.op.import"
    friendly_id = ""
    name = "Import Data"

    coarse = Bool(False)
    coarse_events = Int(1000)
    
    tubes = List(Tube)
          
    def validate(self, experiment = None):
        if not self.tubes:
            return False
        
        if len(self.tubes) == 0:
            return False
        
        for idx, i in enumerate(self.tubes[0:-2]):
            for j in self.tubes[idx+1:]:
                if i == j:
                    return False
                
        # TODO - more error checking.  ie, does the File exist?  is it
        # readable?  etc etc.
                
        return True
      
    def apply(self, experiment = None):
        
        experiment = Experiment()

        trait_to_dtype = {"Str" : "category",
                          "Float" : "float",
                          "LogFloat" : "float",
                          "Bool" : "bool"}
        
        # get rid of the name and path traits
        trait_names = Tube.class_trait_names(transient = lambda x: x is not True)
    
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
      
    def default_view(self, experiment = None):
        raise NotImplementedError

        """ """