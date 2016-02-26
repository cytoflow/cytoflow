#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Mar 20, 2015

@author: brian
'''
from __future__ import absolute_import

import warnings

from traits.api import (HasStrictTraits, provides, Str, List, Bool, Int, Any,
                        Dict, File, Constant, Enum)

import fcsparser
import numpy as np

import cytoflow.utility as util

from cytoflow import Experiment
from .i_operation import IOperation

#from cytoflow.operations import IOperation
#from cytoflow.utility import CytoflowError, CytoflowOpError

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
        
    channels = List(Str)
        If you only need a subset of the channels available in the data set,
        specify them here.
        
    coarse_events : Int (default = 0)
        If >= 0, import only a random subset of events of size `coarse_events`. 
        Presumably the analysis will go faster but less precisely; good for
        interactive data exploration.  Then, set `coarse_events = 0` and re-run
        the analysis non-interactively.
        
    name_metadata : Enum(None, "$PnN", "$PnS") (default = None)
        Which FCS metadata is the channel name?  If `None`, attempt to  
        autodetect.
        
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

    # experimental conditions: name --> dtype.  can also be "log"
    conditions = Dict(Str, Str)
    
    # the tubes
    tubes = List(Tube)
    
    # which FCS metadata has the channel names in it?
    name_metadata = Enum(None, "$PnN", "$PnS")

    # are we subsetting?
    coarse_events = Int(0)
        
    # DON'T DO THIS
    ignore_v = Bool(False)
      
    def apply(self, experiment = None):
        
        if not self.tubes or len(self.tubes) == 0:
            raise util.CytoflowOpError("Must specify some tubes!")
        
        # make sure each tube has the same conditions
        tube0_conditions = set(self.tubes[0].conditions)
        for tube in self.tubes:
            tube_conditions = set(tube.conditions)
            if len(tube0_conditions ^ tube_conditions) > 0:
                raise util.CytoflowOpError("Tube {0} didn't have the same "
                                      "conditions as tube {1}"
                                      .format(tube.file, self.tubes[0].file))

        # make sure experimental conditions are unique
        for idx, i in enumerate(self.tubes[0:-1]):
            for j in self.tubes[idx+1:]:
                if i.conditions_equal(j):
                    raise util.CytoflowOpError("The same conditions specified for "
                                          "tube {0} and tube {1}"
                                          .format(i.file, j.file))
        
        experiment = Experiment()
        
        experiment.metadata["ignore_v"] = self.ignore_v
            
        for condition, dtype in self.conditions.items():
            is_log = False
            if dtype == "log":
                is_log = True
                dtype = "float"
            experiment.add_condition(condition, dtype)
            if is_log:
                experiment.metadata[condition]["repr"] = "log"

        try:
            # silence warnings about duplicate channels;
            # we'll figure that out below
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tube0_meta = fcsparser.parse(self.tubes[0].file,
                                             meta_data_only = True,
                                             reformat_meta = True)
        except Exception as e:
            raise util.CytoflowOpError("FCS reader threw an error reading metadata "
                                       " for tube {0}: {1}"
                                       .format(self.tubes[0].file, str(e)))
              
        meta_channels = tube0_meta["_channels_"]
        
        if self.name_metadata:
            experiment.metadata["name_meta"] = self.name_metadata
        else:
            # try to autodetect the metadata
            if "$PnN" in meta_channels and not "$PnS" in meta_channels:
                experiment.metadata["name_metadata"] = "$PnN"
            elif "$PnN" not in meta_channels and "$PnS" in meta_channels:
                experiment.metadata["name_metadata"] = "$PnS"
            else:
                PnN = meta_channels["$PnN"]
                PnS = meta_channels["$PnS"]
                
                # sometimes one is unique and the other isn't
                if (len(set(PnN)) == len(PnN) and 
                    len(set(PnS)) != len(PnS)):
                    experiment.metadata["name_metadata"] = "$PnN"
                elif (len(set(PnN)) != len(PnN) and 
                      len(set(PnS)) == len(PnS)):
                    experiment.metadata["name_metadata"] = "$PnS"
                else:
                    # as per fcsparser.api, $PnN is the "short name" (like FL-1)
                    # and $PnS is the "actual name" (like "FSC-H").  so let's
                    # use $PnS.
                    experiment.metadata["name_metadata"] = "$PnS"

        meta_channels.set_index(experiment.metadata["name_metadata"], 
                                inplace = True)
        
        # now that we have the metadata, load it into experiment

        for channel in meta_channels.index:
            experiment.add_channel(channel)
            
            # keep track of the channel's PMT voltage
            if("$PnV" in meta_channels.ix[channel]):
                v = meta_channels.ix[channel]['$PnV']
                if v: experiment.metadata[channel]["voltage"] = v
            
            # add the maximum possible value for this channel.
            data_range = meta_channels.ix[channel]['$PnR']
            data_range = float(data_range)
            experiment.metadata[channel]['range'] = data_range
        
        for tube in self.tubes:
            tube_data = parse_tube(tube.file, experiment, self.ignore_v)

            if self.coarse_events:
                tube_data = tube_data.loc[np.random.choice(tube_data.index,
                                                           self.coarse_events,
                                                           replace = False)]

            experiment.add_events(tube_data, tube.conditions)
            
        return experiment


def check_tube(filename, experiment, ignore_v = False):
    try:
        tube_meta = fcsparser.parse( filename, 
                                     channel_naming = experiment.metadata["name_metadata"],
                                     meta_data_only = True,
                                     reformat_meta = True)
    except Exception as e:
        raise util.CytoflowOpError("FCS reader threw an error reading metadata "
                              " for tube {0}: {1}"
                              .format(filename, str(e)))
    
    # first make sure the tube has the right channels    
    if set(tube_meta["_channel_names_"]) != set(experiment.channels):
        raise util.CytoflowError("Tube {0} doesn't have the same channels "
                           "as the first tube added".format(filename))
     
    tube_channels = tube_meta["_channels_"]
    tube_channels.set_index(experiment.metadata["name_metadata"], 
                            inplace = True)
     
    # next check the per-channel parameters
    for channel in experiment.channels:        
        # first check voltage
        if "voltage" in experiment.metadata[channel]:    
            if not "$PnV" in tube_channels.ix[channel]:
                raise util.CytoflowError("Didn't find a voltage for channel {0}" \
                                   "in tube {1}".format(channel, filename))
            
            old_v = experiment.metadata[channel]["voltage"]
            new_v = tube_channels.ix[channel]['$PnV']
            
            if old_v != new_v and not ignore_v:
                raise util.CytoflowError("Tube {0} doesn't have the same voltages"
                                    .format(filename))

        # TODO check the delay -- and any other params?
            

# module-level, so we can reuse it in other modules
def parse_tube(filename, experiment, ignore_v = False):   
    
    check_tube(filename, experiment, ignore_v)
         
    try:
        _, tube_data = fcsparser.parse(
                            filename, 
                            channel_naming = experiment.metadata["name_metadata"])
    except Exception as e:
        raise util.CytoflowOpError("FCS reader threw an error reading data for tube "
                              "{0}: {1}".format(filename, str(e)))
            
    return tube_data

