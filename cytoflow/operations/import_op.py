'''
Created on Mar 20, 2015

@author: brian
'''
from traits.api import HasStrictTraits, provides, Str, List, Bool, Int, Any, \
                       Dict, File
from cytoflow.operations.i_operation import IOperation
from cytoflow import Experiment
import FlowCytometryTools as fc

class Tube(HasStrictTraits):
    """
    Represents a tube or plate well we want to import.
    """
    
    # name, row and col are optional for interactive use 
    # (needed for GUI persistance)
    source = Str
    tube = Str
    row = Str
    col = Int
    
    # file and conditions are not optional.  (-:
    
    # the file name for the FCS file to import
    file = File
    
    # a dict of experimental conditions: name --> value
    conditions = Dict(Str, Any)

    def conditions_equal(self, other):        
        return len(set(self.conditions.items()) ^ 
                   set(other.conditions.items())) == 0

@provides(IOperation)
class ImportOp(HasStrictTraits):
    '''
    classdocs
    '''

    id = "edu.mit.synbio.cytoflow.operations.import"
    friendly_id = "Import"
    name = "Import Data"

    coarse = Bool(False)
    coarse_events = Int(1000)

    # experimental conditions: name --> dtype.  can also be "log"
    conditions = Dict(Str, Str)
    tubes = List(Tube)
        
    # DON'T DO THIS
    ignore_v = Bool(False)
          
    def is_valid(self, experiment = None):
        if not self.tubes:
            return False
        
        if len(self.tubes) == 0:
            return False
        
        # make sure each tube has the same conditions
        tube0_conditions = set(self.tubes[0].conditions)
        for tube in self.tubes:
            tube_conditions = set(tube.conditions)
            if len(tube0_conditions ^ tube_conditions) > 0:
                return False

        # make sure experimental conditions are unique
        for idx, i in enumerate(self.tubes[0:-1]):
            for j in self.tubes[idx+1:]:
                if i.conditions_equal(j):
                    return False
                
        if self.ignore_v:
            raise RuntimeError("Ignoring voltages?  Buddy, you're on your own.")
                
        # TODO - more error checking.  ie, does the file exist?  is it
        # readable?  etc etc.
                
        return True
      
    def apply(self, experiment = None):
        
        experiment = Experiment()
            
        for condition, dtype in self.conditions.items():
            is_log = False
            if dtype == "log":
                is_log = True
                dtype = "float"
            experiment.add_conditions({condition : dtype})
            if is_log:
                experiment.metadata[condition]["repr"] = "Log"
        
        for tube in self.tubes:
            tube_fc = fc.FCMeasurement(ID=tube.source + tube.tube, datafile=tube.file)
            if self.coarse:
                tube_fc = tube_fc.subsample(self.coarse_events, "random")
            experiment.add_tube(tube_fc, tube.conditions, ignore_v = self.ignore_v)
            
        return experiment
