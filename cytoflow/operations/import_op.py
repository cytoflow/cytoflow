'''
Created on Mar 20, 2015

@author: brian
'''
from traits.api import HasTraits, provides, Str, List, Bool, Int, Any, Float
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
    
    This model depends on duck-typing ("if it walks like a duck, and quacks
    like a duck...").  Because we want to use all of the TableEditor's nice
    features, each row needs to be an instance, and each column a Trait.
    So, each Tube instance represents a single tube, and each experimental
    condition (as well as the tube name, its file, and optional plate row and 
    col) are traits. These traits are dynamically added to Tube INSTANCES 
    (NOT THE TUBE CLASS.)  Then, we add appropriate columns to the table editor
    to access these traits.
    
    This is slightly complicated by the fact that there are two different
    kinds of traits we want to keep track of: traits that specify experimental
    conditions (inducer concentration, time point, etc.) and other things
    (file name, tube name, etc.).  We differentiate them because we enforce
    the invariant that each tube MUST have a unique combination of experimental
    conditions.  I used to do this with trait metadata (seems like the right
    thing) .... but trait metadata on dynamic traits (both instance and
    class) doesn't survive pickling.  >.>
    
    So: we keep a separate list of traits that are experimental conditions.
    Every 'public' trait (doesn't start with '_') is given a column in the
    editor; only those that are in the conditions list are considered for tests
    of equality (to make sure combinations of experimental conditions are 
    unique) and are added as conditions to the resulting Experiment.
    
    And of course, the 'transient' flag controls whether the trait is serialized
    or not.
    """
    
    Name = Str
    
    _file = Str
    _conditions = List(Str)
    
    # any added trait starting with an underscore is automatically transient
    __ = Any(transient = True)
    
    def __hash__(self):
        ret = int(0)
        for trait in self.trait_names(transient = lambda x: x is not True):
            if trait not in self._conditions:
                continue
            if not ret:
                ret = hash(self.trait_get(trait)[trait])
            else:
                ret = ret ^ hash(self.trait_get(trait)[trait])
                
        return ret
    
    def __eq__(self, other):
        for trait in self.trait_names(transient = lambda x: x is not True):
            if trait not in self._conditions:
                continue
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

    # a list of the tubes we're importing
    tubes = List(Tube)
    
    # the traits on the tube instances that are experimental conditions
    conditions = List(Str)
          
    def is_valid(self, experiment = None):
        if not self.tubes:
            return False
        
        if len(self.tubes) == 0:
            return False
        
        tube0_traits = \
            set(self.tubes[0].trait_names(transient = lambda x: x is not True))
        for tube in self.tubes:
            tube_traits = \
                set(tube.trait_names(transient = lambda x: x is not True))
            if len(tube0_traits ^ tube_traits) > 0: 
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
                          "Bool" : "bool",
                          "Int" : "int"}
            
        conditions = self.tube[0]._conditions
        
        for condition in conditions:
            
            trait = self.tubes[0].trait(condition)
            trait_type = trait.trait_type.__class__.__name__
        
            experiment.add_conditions({condition : trait_to_dtype[trait_type]})
            if trait_type == "LogFloat":
                experiment.metadata[condition]["repr"] = "Log"
        
        for tube in self.tubes:
            tube_fc = fc.FCMeasurement(ID=tube.Name, datafile=tube._file)
            experiment.add_tube(tube_fc, tube.trait_get(conditions))
            
        return experiment
