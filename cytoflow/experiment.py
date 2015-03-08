import pandas as pd
import FlowCytometryTools as fc
import copy

class Experiment(object):
    """An Experiment manages all the data and metadata for a flow experiment.
    
    A flow cytometry experiment consists of:
      - A set of tubes or wells in a multi-well plate.  Each tube or well
        contains cells subjected to different experimental conditions.
      - An array of events from each well or tube.  Each event is a tuple of 
        measurements of a single cell.
        
    An Experiment is built from a set of FCMeasurement objects, subject to
    a set of constraints:
      - Each FCMeasurement object MUST have identical channels (including
        channel parameters such as PMT voltage and delay.)
      - Each FCMeasurement MUST have a unique set of metadata.
          
    An Experiment object manages all this data.  By "manage", we mean:
      - Get events that match a particular metadata "signature"
      - Add additional metadata to define populations
      
    TODO - how many of these attributes need to be public?  Many are just
    internal record-keeping.....
    
    Attributes
    ----------
    version : small integer
        The version of this Experiment (ie, how many predecessors does it
        have?)
        
    conditions : dict(string : any)
        A dict of the tube "conditions" that this experiment tracks.
        
    channels : dict(string : any)
        A dict containing the channels that this experiment tracks.
        
    channel_metadata : dict( str : dict(str : any) )
        A dict whose keys are channel names and whose values are dicts of
        metadata.  Some of this is application-specific and still being
        determined.  Currently defined metadata:
        * xforms: a list of (parameterized!) transformations that have been 
                  applied to this channel.  necessary for computing tic marks
                  on plots, among other things.
        * voltage: the detector voltage used for this channel, from the FCS
                   keyword "$PnV".
    
    tubes : list(FCMeasurement)
        a list of the FCMeasurements that we're a container for.  
        TODO - do we really need to keep these around?  i think we're sucking
        all the relevant metadata out already, and we're certainly capturing
        all the events.....  though at the moment we use them as keys for the
        next two dicts.
        
    tube_keywords : dict(FCMeasurement : dict(string : string) )
        a dictionary containing all the FCS metadata keywords for each tube.
        things like channel name, maximum value, etc etc etc, but in a really
        awful format.  See the FCS spec for details.
        
    tube_conditions : dict(FCMeasurement : dict(string : any) )
        a dictionary mapping a tube reference to the experimental conditions
        under which that sample was collected (provided by the experimenter.)
        used to make sure that no two tubes have the same conditions.
        
    successor : Experiment
        the Experiment derived from this one (or None, if there isn't one.)
        useful for invalidating future versions if, say, a transformation's
        parameters are changed.  TODO - this isn't yet implemented.
        
    data : pandas.DataFrame
        the DataFrame representing all the events and metadata.  Each event
        is a row; each column is either a fluorescent channel or a piece of
        metadata, either supplied by the tube conditions or by further operations
        (like gates, etc.)
        
    Notes
    -----              
          
    Note that nowhere do we mention filters or gates.  You can define gate,
    sure .... but applying that gate to an Experiment simply adds another
    piece of metadata for each event, indicating that the event is in the new
    population or not.  This is in contrast to traditional cytometry tools,
    which allow you to define a tree-like gating "hierarchy."
        
    Also, an Experiment instance is *versioned*.  That is, when you apply a 
    filter, gate or transformation, you get back a new Experiment with the 
    version attribute incremented.  The old Experiment (version i) retains a
    link to the new Experiment (version i+1), which allows for dynamic updating;
    so if you change the parameters of the filter that created version i, 
    version i+1 can recompute its gates etc.  This isn't an issue for 
    user-defined gates, but if they're data-driven then they need to be updated
    if the (meta)data changes.
        
    This versioning lets an Experiment be smart about data copying, too;
    applying gates or transformations only creates the new columns that it has
    to, and simply uses references to access unchanged data.
        
    Finally, all this is implemented on top of a pandas DataFrame.... which
    earns us all sorts of fun optimization, and lets us select subsets easily:
        
    ex.query('Induced == True') ... etc

    Implementation details
    ----------------------
    
    The OOP programmer in me desperately wanted to subclass DataFrame, add
    some flow-specific stuff, and move on with my life.  A few things get in 
    the way.
    
     - First, to enable some of the delicious syntactic sugar for accessing
       its contents, DataFrame redefines __{get,set}attribute__, and making
       it recognize (and maintain across copies) additional attributes
       is an unsupported (non-public) API feature and introduces other
       subclassing weirdness.
    
     - Second, many of the operations (like appending!) don't happen in-place;
       they return copies instead.  It's cleaner to simply manage that copying
       ourselves instead of making the client deal with it.  we can pretend
       to operate on the data in-place.
       
    To maintain the ease of use, we'll override __getitem__ and pass it to
    the wrapped DataFrame.  We'll do the same with some of the more useful
    DataFrame API pieces (like query()); and of course, you can just get the
    data frame itself with Experiment.data
    """

    def __init__(self, prev_experiment = None, *args, **kwargs):
        """Initializes a new Experiment, possibly from an old Experiment.
        
        Parameters
        ----------
        prev_experiment : Experiment
            the previous version of this experiment.
        """
    
        self.version = 1
        self.conditions = {}
        self.channels = {}
        self.channel_metadata = {}
        self.tubes = []
        self.tube_conditions = {}
        self.tube_keywords = {}
        self.successor = None
        self.data = pd.DataFrame()
            
        if(prev_experiment != None):
            self.version = prev_experiment.version + 1

            # copy most of the metadata so if the op needs to change the
            # new experiment it won't affect the old experiment.
            self.conditions = copy.deepcopy(prev_experiment.conditions)
            self.channels = copy.deepcopy(prev_experiment.channels)
            self.channel_metadata = copy.deepcopy(prev_experiment.channel_metadata)
            self.tubes = prev_experiment.tubes # no copy, just reference
            self.tube_conditions = copy.deepcopy(prev_experiment.tube_conditions)
            prev_experiment.successor = self 
            self.data = prev_experiment.data.copy()  # shallow copy!
            
    def __getitem__(self, key):
        """Override __getitem__ so we can reference columns like ex.column"""
        return self.data.__getitem__(key)
    
    def __setitem__(self, key, value):
        """Override __setitem__ so we can assign columns like ex.column = ..."""
        return self.data.__setitem__(key, value)
    
    def query(self, expr, **kwargs):
        """Expose pandas.DataFrame.query() to the outside world"""
        return self.data.query(expr, **kwargs)
            
    def add_conditions(self, conditions):
        """Add one or more conditions as a dictionary. Call before adding tubes.
        
        We keep track of this for metadata validation as tubes are added.
        
        Parameters
        ----------
        conditions : dict(name : dtype): 
            a dictionary of name:dtype pairs that define the tubes' conditions.
            useful dtypes: "category", "float", "int", "bool"
            
        Raises
        ------
        RuntimeError
            If you call add_conditions() after you've already started adding
            tubes.                
        """
        
        if(self.tubes):
            raise RuntimeError("You have to add all your conditions before "
                               "adding your tubes!")              
            
        for key, value in conditions.iteritems():
            self.data[key] = pd.Series(dtype = value)
        
        self.conditions.update(conditions)
             
    def add_tube(self, tube, conditions):
        """Add an FCMeasurement, and its experimental conditions, to this Experiment.
        
        Remember: because add_tube COPIES the data into this Experiment, you can
        DELETE the tube after you add it (and save memory)
        
        Parameters
        ----------
        tube : FCMeasurement
            a single tube or well's worth of data
        
        conditions : dict(string : any)
            the tube's experimental conditions in (condition:value) pairs
        """
    
        if(self.tubes):
            # first, make sure the new tube's channels match the rest of the channels
            # in the Experiment
            
            if(tube.channel_names != self.tubes[0].channel_names):
                raise RuntimeError("Tube {0} doesn't have the same channels "
                                   "as tube {1}".format(tube.datafile,
                                                        self.tubes[0].datafile))
             
            # next check the voltage   
            if("$PnV" in tube.channels or "$PnV" in self.tubes[0].channels):
                old_v = self.tubes[0].channels["$PnV"]
                new_v = tube.channels["$PnV"]
                
                if(not all(old_v[old_v.notnull()] == new_v[new_v.notnull()])):
                    raise RuntimeError("Tube {0} doesn't have the same voltages "
                                       "as tube {1}" \
                                       .format(tube.datafile,
                                               self.tubes[0].datafile))
                    
            # TODO check the delay -- and any other params?
        else:
            self.channels = tube.channel_names
            
            for channel_name in tube.channel_names:
                if(channel_name not in self.channel_metadata):
                    self.channel_metadata[channel_name] = {}
                if("$PnV" in tube.channels):
                    self.channel_metadata[channel_name]["voltage"] = \
                        tube.channels["$PnV"]
                        
                # add an empty list for channel transforms.  a transform must
                # be an object with scale(float) and inverse(float) methods,
                # each of which applies or inverts the transformation.
                # required to draw tic marks, etc.                    
                self.channel_metadata[channel_name]["xforms"] = []
                    
        # validate the conditions
        
        # first, make sure that the keys in conditions are the same as self.conditions
        if( any(True for k in conditions if k not in self.conditions) or \
            any(True for k in self.conditions if k not in conditions) ):
            raise RuntimeError("Metadata mismatch for tube {0}" \
                               .format(tube.datafile))
            
        # next, make sure that this tube's conditions doesn't match any other
        # tube's conditions
        for prev_tube, prev_meta in self.tube_conditions.iteritems():
            if(cmp(prev_meta, conditions) == 0):
                raise RuntimeError("Tube {0} has the same conditions as tube {1}"\
                                   .format(tube.datafile, prev_tube.datafile))
                
        # add the conditions to tube's internal data frame.  specify the conditions
        # dtype using self.conditions.  check for errors as we do so.
        
        new_data = tube.data.copy(deep=True)
        
        for meta_name, meta_value in conditions.iteritems():
            if(meta_name not in self.conditions):
                raise RuntimeError("Tube {0} asked to add conditions {1} which" \
                                   "hasn't been specified as a condition" \
                                   .format(tube.datafile,
                                           meta_name))
            meta_type = self.conditions[meta_name]
            try:
                new_data[meta_name] = pd.Series([meta_value] * tube.data.size,
                                             dtype = meta_type)
            except ValueError:
                raise RuntimeError("Tube {0} had trouble converting conditions {1}"
                                   "(value = {2}) to type {3}" \
                                   .format(tube.datafile,
                                           meta_name,
                                           meta_value,
                                           meta_type))
        
        self.tubes.append(tube)
        self.tube_conditions[tube] = conditions
        self.tube_keywords[tube] = tube.channels
        self.data = self.data.append(new_data)
        del new_data
        
        # TODO - figure out if we can actually delete the original tube's data

if __name__ == "__main__":
    ex = Experiment()
    ex.add_conditions({"time" : "float"})
    
    tube1 = fc.FCMeasurement(ID='Test 1',
                             datafile='/home/brian/RFP_Well_A3.fcs')
    tube2 = fc.FCMeasurement(ID='Test 2', 
                       datafile='/home/brian/CFP_Well_A4.fcs')
    
    ex = ex.add_tube(tube1, {"time" : 10.0})
    ex = ex.add_tube(tube2, {"time" : 20.0})
    
    print(ex.data)

