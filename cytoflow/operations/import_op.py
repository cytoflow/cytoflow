#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
cytoflow.operations.import_op
-----------------------------
'''

import warnings
from traits.api import (HasTraits, HasStrictTraits, provides, Str, List, Any,
                        Dict, File, Constant, Enum)

import fcsparser
import numpy as np
from pathlib import Path

import cytoflow.utility as util

from ..experiment import Experiment
from .i_operation import IOperation

class Tube(HasTraits):
    """
    Represents a tube or plate well we want to import.
    
    Attributes
    ----------
    file : File
        The file name of the FCS file to import
        
    conditions : Dict(Str, Any)
        A dictionary containing this tube's experimental conditions.  Keys
        are condition names, values are condition values.
        
    Examples
    --------
    >>> tube1 = flow.Tube(file = 'RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
    >>> tube2 = flow.Tube(file='CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
    """
    
    # the file name for the FCS file to import
    file = File
    
    # a dict of experimental conditions: name --> value
    conditions = Dict(Str, Any)

    def conditions_equal(self, other):        
        return other and len(set(self.conditions.items()) ^ 
                   set(other.conditions.items())) == 0
                   
    def __eq__(self, other):
        return other and (self.file == other.file and
                self.conditions == other.conditions)
        
    def __hash__(self):
        return hash((self.file, 
                     (frozenset(self.conditions.keys()),
                      frozenset(self.conditions.itervalues()))))

@provides(IOperation)
class ImportOp(HasStrictTraits):
    """
    An operation for importing data and making an :class:`.Experiment`.
    
    To use, set the :attr:`conditions` dict to a mapping between condition name 
    and NumPy ``dtype``.  Useful dtypes include ``category``, ``float``, 
    ``int``, ``bool``.
    
    Next, set :attr:`tubes` to a list of :class:`Tube` containing FCS filenames 
    and the corresponding conditions.
    
    If you would rather not analyze every single event in every FCS file,
    set :attr:`events` to the number of events from each FCS file you want to 
    load.
    
    Call :meth:`apply` to load the data.  The usual ``experiment`` parameter
    can be ``None``.
    
    Attributes
    ----------
    conditions : Dict(Str, Str)
        A dictionary mapping condition names (keys) to NumPy ``dtype``s (values).
        Useful ``dtype``s include ``category``, ``float``, ``int``, and ``bool``.
        
    tubes : List(Tube)
        A list of :class:``Tube`` instances, which map FCS files to their corresponding
        experimental conditions.  Each :class:``Tube`` must have a 
        :attr:``~Tube.conditions`` dict whose keys match those of 
        :attr:`conditions`.
        
    channels : Dict(Str, Str)
        If you only need a subset of the channels available in the data set,
        specify them here.  Each ``(key, value)`` pair specifies a channel to
        include in the output experiment.  The key is the channel name in the 
        FCS file, and the value is the name of the channel in the Experiment.
        You can use this to rename channels as you import data (because flow
        channel names are frequently not terribly informative.)  New channel
        names must be valid Python identifiers: start with a letter or ``_``, and
        all characters must be letters, numbers or ``_``.  If :attr:`channels` is
        empty, load all channels in the FCS files.
        
    events : Int
        If not None, import only a random subset of events of size :attr:`events`. 
        Presumably the analysis will go faster but less precisely; good for
        interactive data exploration.  Then, unset :attr:`events` and re-run
        the analysis non-interactively.
        
    name_metadata : {None, "$PnN", "$PnS"} (default = None)
        Which FCS metadata is the channel name?  If ``None``, attempt to  
        autodetect.
        
    ignore_v : List(Str)
        :class:`cytoflow` is designed to operate on an :class:`.Experiment` containing
        tubes that were all collected under the same instrument settings.
        In particular, the same PMT voltages ensure that data can be
        compared across samples.
        
        *Very rarely*, you may need to set up an :class:`.Experiment` with 
        different voltage settings on different :class:`Tube`s.  This is likely 
        only to be the case when you are trying to figure out which voltages 
        should be used in future experiments.  If so, set :attr:`ignore_v` to a 
        :class:`List` of channel names to ignore particular channels.  
        
        .. warning::
        
            THIS WILL BREAK REAL EXPERIMENTS
        
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

    # experimental conditions: name --> dtype. 
    conditions = Dict(Str, Str)
    
    # the tubes
    tubes = List(Tube)
    
    # which channels do we import?
    channels = Dict(Str, Str)
    
    # which FCS metadata has the channel names in it?
    name_metadata = Enum(None, "$PnN", "$PnS")

    # are we subsetting?
    events = util.CIntOrNone(None)
    coarse_events = util.Deprecated(new = 'events')
        
    # DON'T DO THIS
    ignore_v = List(Str)
      
    def apply(self, experiment = None):
        """
        Load a new :class:`.Experiment`.  
        
        Returns
        -------
        Experiment
            The new :class:`.Experiment`.  New channels have the following
            metadata:
            
            - **voltage** - int
                The voltage that this channel was collected at.  Determined
                by the ``$PnV`` field from the first FCS file.
                
            - **range** - int
                The maximum range of this channel.  Determined by the ``$PnR``
                field from the first FCS file.
                
            New experimental conditions do not have **voltage** or **range**
            metadata, obviously.  Instead, they have **experiment** set to 
            ``True``, to distinguish the experimental variables from the
            conditions that were added by gates, etc.
            
            If :attr:`ignore_v` is set, it is added as a key to the 
            :class:`.Experiment`-wide metadata.
            
        """
        
        if not self.tubes or len(self.tubes) == 0:
            raise util.CytoflowOpError('tubes',
                                       "Must specify some tubes!")
        
        # if we have channel renaming, make sure the new names are valid
        # python identifiers
        if self.channels:
            for old_name, new_name in self.channels.items():
                if old_name != new_name and new_name != util.sanitize_identifier(new_name):
                    raise util.CytoflowOpError('channels',
                                               "Channel name {} must be a "
                                               "valid Python identifier."
                                               .format(new_name))
        
        # make sure each tube has the same conditions
        tube0_conditions = set(self.tubes[0].conditions)
        for tube in self.tubes:
            tube_conditions = set(tube.conditions)
            if len(tube0_conditions ^ tube_conditions) > 0:
                raise util.CytoflowOpError('tubes',
                                           "Tube {0} didn't have the same "
                                           "conditions as tube {1}"
                                           .format(tube.file, self.tubes[0].file))

        # make sure experimental conditions are unique
        for idx, i in enumerate(self.tubes[0:-1]):
            for j in self.tubes[idx+1:]:
                if i.conditions_equal(j):
                    raise util.CytoflowOpError('tubes',
                                               "The same conditions specified for "
                                               "tube {0} and tube {1}"
                                               .format(i.file, j.file))
        
        experiment = Experiment()
        
        experiment.metadata["ignore_v"] = self.ignore_v
            
        for condition, dtype in list(self.conditions.items()):
            experiment.add_condition(condition, dtype)
            experiment.metadata[condition]['experiment'] = True

        try:
            # silence warnings about duplicate channels;
            # we'll figure that out below
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tube0_meta = fcsparser.parse(self.tubes[0].file,
                                             meta_data_only = True,
                                             reformat_meta = True)
        except Exception as e:
            raise util.CytoflowOpError('tubes',
                                       "FCS reader threw an error reading metadata "
                                       "for tube {}"
                                       .format(self.tubes[0].file)) from e
              
        meta_channels = tube0_meta["_channels_"]
        
        if self.name_metadata:
            experiment.metadata["name_metadata"] = self.name_metadata
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
        
        channels = list(self.channels.keys()) if self.channels \
                   else list(tube0_meta["_channel_names_"])

        # make sure everything in self.channels is in the tube channels
        
        for channel in channels:
            if channel not in meta_channels.index:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not in tube {1}"
                                           .format(channel, self.tubes[0].file))                         
        
        # now that we have the metadata, load it into experiment

        for channel in channels:
            experiment.add_channel(channel)
            
            experiment.metadata[channel]["fcs_name"] = channel
            
            # keep track of the channel's PMT voltage
            if("$PnV" in meta_channels.loc[channel]):
                v = meta_channels.loc[channel]['$PnV']
                if v: experiment.metadata[channel]["voltage"] = v
            
            # add the maximum possible value for this channel.
            data_range = meta_channels.loc[channel]['$PnR']
            data_range = float(data_range)
            experiment.metadata[channel]['range'] = data_range
        
        experiment.metadata['fcs_metadata'] = {}
        for tube in self.tubes:
            tube_meta, tube_data = parse_tube(tube.file, experiment)

            if self.events:
                if self.events <= len(tube_data):
                    tube_data = tube_data.loc[np.random.choice(tube_data.index,
                                                               self.events,
                                                               replace = False)]
                else:
                    warnings.warn("Only {0} events in tube {1}"
                                  .format(len(tube_data), tube.file),
                                  util.CytoflowWarning)

            experiment.add_events(tube_data[channels], tube.conditions)
                        
            # extract the row and column from wells collected on a 
            # BD HTS
            if 'WELL ID' in tube_meta:               
                pos = tube_meta['WELL ID']
                tube_meta['CF_Row'] = pos[0]
                tube_meta['CF_Col'] = int(pos[1:3])
                
            tube_meta['CF_File'] = Path(tube.file).stem
                             
            experiment.metadata['fcs_metadata'][tube.file] = tube_meta
                        
        for channel in channels:
            if self.channels and channel in self.channels:
                new_name = self.channels[channel]
                if channel == new_name:
                    continue
                experiment.data.rename(columns = {channel : new_name}, inplace = True)
                experiment.metadata[new_name] = experiment.metadata[channel]
                experiment.metadata[new_name]["fcs_name"] = channel
                del experiment.metadata[channel]
            
        return experiment


def check_tube(filename, experiment):
    
    if experiment is None:
        raise util.CytoflowError("No experiment specified")
    
    ignore_v = experiment.metadata['ignore_v']
    
    try:
        tube_meta = fcsparser.parse( filename, 
                                     channel_naming = experiment.metadata["name_metadata"],
                                     meta_data_only = True,
                                     reformat_meta = True)
    except Exception as e:
        raise util.CytoflowError("FCS reader threw an error reading metadata "
                                 "for tube {0}"
                                 .format(filename)) from e
    
    # first make sure the tube has the right channels    
    if not set([experiment.metadata[c]["fcs_name"] for c in experiment.channels]) <= set(tube_meta["_channel_names_"]):
        raise util.CytoflowError("Tube {0} doesn't have the same channels"
                                 .format(filename))
     
    tube_channels = tube_meta["_channels_"]
    tube_channels.set_index(experiment.metadata["name_metadata"], 
                            inplace = True)
     
    # next check the per-channel parameters
    for channel in experiment.channels:  
        fcs_name = experiment.metadata[channel]["fcs_name"]      
        # first check voltage
        if "voltage" in experiment.metadata[channel]:    
            if not "$PnV" in tube_channels.loc[fcs_name]:
                raise util.CytoflowError("Didn't find a voltage for channel {0}" \
                                   "in tube {1}".format(channel, filename))
            
            old_v = experiment.metadata[channel]["voltage"]
            new_v = tube_channels.loc[fcs_name]['$PnV']
            
            if old_v != new_v and not channel in ignore_v:
                raise util.CytoflowError("Tube {0} doesn't have the same voltages"
                                    .format(filename))

        # TODO check the delay -- and any other params?
            

# module-level, so we can reuse it in other modules
def parse_tube(filename, experiment, metadata_only = False):   
        
    check_tube(filename, experiment)
         
    try:
        if metadata_only:
            tube_data = None
            tube_meta = fcsparser.parse(
                            filename, 
                            meta_data_only = True,
                            channel_naming = experiment.metadata["name_metadata"])
        else:
            tube_meta, tube_data = fcsparser.parse(
                                    filename, 
                                    meta_data_only = metadata_only,
                                    channel_naming = experiment.metadata["name_metadata"])
    except Exception as e:
        raise util.CytoflowError("FCS reader threw an error reading data for tube {}"
                                 .format(filename)) from e
            
    del tube_meta['__header__']
            
    return tube_meta, tube_data


