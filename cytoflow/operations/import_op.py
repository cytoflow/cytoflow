'''
Created on Mar 20, 2015

@author: brian
'''
from traits.api import HasStrictTraits, provides, Str, List, Bool, Int, Any, \
                       Dict, File, Constant, Enum

import fcsparser
import numpy as np

from cytoflow import Experiment
from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError

class Tube(HasStrictTraits):
    """
    Represents a tube or plate well we want to import.
    
    Attributes
    ----------
    file : File
        The file name of the FCS file to import
        
    conditions : Dict(Str, Any)
        A dictionary containing this tube's experimental conditions.  Keys
        are condition names, values are condition values.
    
    source : Str
        The sample source, from the $SRC FCS file keyword.  Optional for 
        interactive use.
        
    tube : Str
        The sample tube, from the TUBE NAME or SMNO FCS keyword.  Optional for
        interactive use.
        
    row : Str
        If this FCS file was a well from a multi-well plate, `row` contains
        the well's row.  Optional for interactive use.
        
    col : Int
        If this FCS file was a well from a multi-well plate, `col` contains the
        well's column.  Optional for interactive use.
        
    Examples
    --------
    >>> tube1 = flow.Tube(file = 'RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
    >>> tube2 = flow.Tube(file='CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
    """
    
    # source, name, row and col are optional for interactive use 
    # (needed for GUI persistance)
    source = Str
    tube = Str
    row = Str
    col = Int
    
    # file and conditions are not optional.
    
    # the file name for the FCS file to import
    file = File
    
    # a dict of experimental conditions: name --> value
    conditions = Dict(Str, Any)

    def conditions_equal(self, other):        
        return len(set(self.conditions.items()) ^ 
                   set(other.conditions.items())) == 0

@provides(IOperation)
class ImportOp(HasStrictTraits):
    """
    An operation for importing data and making an `Experiment`.
    
    To use, set the `conditions` dict to a mapping between condition name and
    NumPy `dtype`.  Useful dtypes include `category`, `float`, `int`, `bool`, 
    and `log`. (`log` is not a NumPy `dtype`: instead, it is converted to 
    `float`, but all plots are displayed on a log scale.)
    
    Next, set `tubes` to a list of `Tube` containing FCS filenames and the
    corresponding conditions.
    
    If you would rather not analyze every single event in every FCS file,
    set `coarse` to `True` and `coarse_events` to the number of events from
    each FCS file you want to load.
    
    Call `apply()` to load the data.
    
    Attributes
    ----------
    
    conditions : Dict(Str, Str)
        A dictionary mapping condition names (keys) to NumPy `dtype`s (values).
        Useful `dtype`s include "category", "float", "int", "bool", and "log". 
        ("log" is not a NumPy `dtype`: instead, it is converted to `float`, 
        but all plots are displayed on a log scale.)
        
    tubes : List(Tube)
        A list of `Tube` instances, which map FCS files to their corresponding
        experimental conditions.  Each `Tube` must have a `conditions` dict
        whose keys match `self.conditions.keys()`.
        
    coarse : Bool
        Do we want to import a random subset of events?  Presumably the analysis
        will go faster but less precisely; good for interactive exploration.
        Then, set `coarse = False` and re-run the analysis non-interactively.
        
    coarse_events : Int (default = 1000)
        If `coarse == True`, how many random events to choose from each FCS 
        file.
        
    name_metadata : Enum("$PnN", "$PnS") (default = "$PnN")
        Which FCS metadata is the channel name?
        
    ignore_v : Bool
        **CytoFlow** is designed to operate on an `Experiment` containing tubes
        that were all collected under the instrument settings.  In particular,
        the same PMT voltages ensure that data can be compared across samples.
        
        *Very rarely*, you may need to set up an Experiment with different 
        voltage settings.  This is likely only to be the case when you are
        trying to figure out which voltages should be used in future
        experiments.  If so, set `ignore_v` to `True` to disable the voltage
        sanity check.  **BE WARNED - THIS WILL BREAK REAL EXPERIMENTS.**
        
    Examples
    --------
    >>> tube1 = flow.Tube(file = 'RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
    >>> tube2 = flow.Tube(file='CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
    >>> import_op = flow.ImportOp(conditions = {"Dox" : "float"},
    ...                           tubes = [tube1, tube2])
    >>> ex = import_op.apply()
    """

    id = Constant("edu.mit.synbio.cytoflow.operations.import")
    friendly_id = Constant("Import")
    name = Constant("Import Data")

    coarse = Bool(False)
    coarse_events = Int(1000)

    # experimental conditions: name --> dtype.  can also be "log"
    conditions = Dict(Str, Str)
    tubes = List(Tube)
        
    # which FCS metadata has the channel name in it?
    name_meta = Enum("$PnN", "$PnS")
        
    # DON'T DO THIS
    ignore_v = Bool(False)
      
    def apply(self, experiment = None):
        
        if not self.tubes or len(self.tubes) == 0:
            raise CytoflowOpError("Must specify some tubes!")
        
        # make sure each tube has the same conditions
        tube0_conditions = set(self.tubes[0].conditions)
        for tube in self.tubes:
            tube_conditions = set(tube.conditions)
            if len(tube0_conditions ^ tube_conditions) > 0:
                raise CytoflowOpError("Tube {0} didn't have the same "
                                      "conditions as tube {1}"
                                      .format(tube.file, self.tubes[0].file))

        # make sure experimental conditions are unique
        for idx, i in enumerate(self.tubes[0:-1]):
            for j in self.tubes[idx+1:]:
                if i.conditions_equal(j):
                    raise CytoflowOpError("The same conditions specified for "
                                          "tube {0} and tube {1}"
                                          .format(i.file, j.file))
        
        experiment = Experiment()
            
        for condition, dtype in self.conditions.items():
            is_log = False
            if dtype == "log":
                is_log = True
                dtype = "float"
            experiment.add_conditions({condition : dtype})
            if is_log:
                experiment.metadata[condition]["repr"] = "log"
        
        experiment.metadata["name_meta"] = self.name_meta
        
        for tube in self.tubes:
            tube_fc = fcsparser.parse(tube.file, 
                                      channel_naming = self.name_meta,
                                      reformat_meta = True)
            
            if self.coarse:
                tube_meta, tube_data = tube_fc
                tube_data = tube_data.loc[np.random.choice(tube_data.index,
                                                           self.coarse_events,
                                                           replace = False)]
                tube_fc = (tube_meta, tube_data)
            experiment.add_tube(tube_fc, tube.conditions, ignore_v = self.ignore_v)
            
        return experiment
