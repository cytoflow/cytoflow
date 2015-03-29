import pandas as pd
import FlowCytometryTools as fc
from traits.api import HasStrictTraits, DictStrAny, ListStr, Instance, \
                       Set, DictStrStr

class Experiment(HasStrictTraits):
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

    channels : list(string)
        A list containing the channels that this experiment tracks.
    
    conditions : dict(string : string)
        A dict of the experimental conditions and analysis metadata (gate
        membership, etc) and that this experiment tracks.  The key is the name
        of the condition, and the value is the string representation of the 
        numpy dtype (usually one of "category", "float", "int" or "bool".
        
    data : pandas.DataFrame
        the DataFrame representing all the events and metadata.  Each event
        is a row; each column is either a fluorescent channel or a piece of
        metadata, either supplied by the tube conditions or by further operations
        (like gates, etc.)
        
    metadata : dict( str : dict(str : any) )
        A dict whose keys are column names (either channels or conditions)
        and whose values are dicts of metadata.  Some of this is 
        application-specific and still being determined.  Currently defined 
        metadata:
        * xforms: for chanels, a list of (parameterized!) transformations that 
                  have been applied.  necessary for computing tic marks on 
                  plots, among other things.
        * voltage: for channels, the detector voltage used. from the FCS
                   keyword "$PnV".
        * max: for channels, the maximum possible value.  from the FCS
               keyword "$PnN"
        * repr: for float conditions, whether to represent it linearly or on
                a log scale.
                
    _tube_conditions : set( dict(string : string) )
        a dictionary mapping a tube reference to the experimental conditions
        under which that sample was collected (provided by the experimenter.)
        used to make sure that no two tubes have the same conditions.  not used
        after import is done.  
        
        
    Notes
    -----              
      
    Note that nowhere do we mention filters or gates.  You can define gate,
    sure .... but applying that gate to an Experiment simply adds another
    condition for each event, indicating that the event is in the new
    population or not.  This is in contrast to traditional cytometry tools,
    which allow you to define a tree-like gating "hierarchy."
        
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
    
    # potentially mutable.  deep copy required
    conditions = DictStrStr(copy = "deep")
    
    # potentially mutable.  deep copy required
    channels = ListStr(copy = "deep")
    
    # potentially mutable.  deep copy required
    metadata = DictStrAny(copy = "deep")
    
    # this doesn't play nice with copy.copy(); clone it ourselves.
    data = Instance(pd.DataFrame, args=())
    
    # don't really have to keep this one around at all
    _tube_conditions = Set(transient = True)
            
    def __getitem__(self, key):
        """Override __getitem__ so we can reference columns like ex.column"""
        return self.data.__getitem__(key)
     
    def __setitem__(self, key, value):
        """Override __setitem__ so we can assign columns like ex.column = ..."""
        return self.data.__setitem__(key, value)
    
    def query(self, expr, **kwargs):
        """Expose pandas.DataFrame.query() to the outside world"""
        return self.data.query(expr, **kwargs)
    
    def clone(self):
        """Clone this experiment"""
        new_exp = self.clone_traits()
        new_exp.data = self.data.copy()
        return new_exp
            
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
        
        if(self._tube_conditions):
            raise RuntimeError("You have to add all your conditions before "
                               "adding your tubes!")              
            
        for key, value in conditions.iteritems():
            self.data[key] = pd.Series(dtype = value)
            self.metadata[key] = {}
        
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
    
        if(self.channels):
            # first, make sure the new tube's channels match the rest of the 
            # channels in the Experiment
            
            if(list(tube.channel_names) != self.channels):
                raise RuntimeError("Tube {0} doesn't have the same channels "
                                   "as the first tube added".format(tube.datafile))
                                            
             
            # next check the per-channel parameters
            for channel in self.channels:
                
                # first check voltage
                if "voltage" in self.metadata[channel]:
                    
                    if not "$PnV" in tube.channels:
                        raise RuntimeError("Didn't find a voltage for channel {0}" \
                                           "in tube {1}".format(channel, tube.datafile))
                    
                    old_v = self.metadata[channel]["voltage"]
                    new_v = tube.channels[tube.channels['$PnN'] == channel]['$PnV'].iloc[0]
                    
                    if old_v != new_v:
                        raise RuntimeError("Tube {0} doesn't have the same voltages "
                                           "as the first tube" \
                                           .format(tube.datafile))

                    
            # TODO check the delay -- and any other params?
        else:
            self.channels = list(tube.channel_names)
            
            for channel in self.channels:
                self.metadata[channel] = {}
                if("$PnV" in tube.channels):
                    new_v = tube.channels[tube.channels['$PnN'] == channel]['$PnV'].iloc[0]
                    if new_v: self.metadata[channel]["voltage"] = new_v
                        
                # add an empty list for channel transforms.  a transform must
                # be an object with scale(float) and inverse(float) methods,
                # each of which applies or inverts the transformation.
                # required to draw tic marks, etc.                    
                self.metadata[channel]['xforms'] = []
                
                # add the maximum possible value for this channel.
                data_max = tube.channels[tube.channels['$PnN'] == channel]['$PnR'].iloc[0]
                self.metadata[channel]['max'] = data_max
                    
        # validate the experimental conditions
        
        # first, make sure that the keys in conditions are the same as self.conditions
        if( any(True for k in conditions if k not in self.conditions) or \
            any(True for k in self.conditions if k not in conditions) ):
            raise RuntimeError("Metadata mismatch for tube {0}" \
                               .format(tube.datafile))
            
        # next, make sure that this tube's conditions doesn't match any other
        # tube's conditions
        if frozenset(conditions.iteritems()) in self._tube_conditions:
            raise RuntimeError("Tube {0} has non-unique conditions".format(tube.datafile))
                
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
                
                # if we're categorical, merge the categories
                if meta_type == "category":
                    cats = set(self.data[meta_name].cat.categories) | set(new_data[meta_name].cat.categories)
                    self.data[meta_name] = self.data[meta_name].cat.set_categories(cats)
                    new_data[meta_name] = new_data[meta_name].cat.set_categories(cats)
            except (ValueError, TypeError):
                raise RuntimeError("Tube {0} had trouble converting conditions {1}"
                                   "(value = {2}) to type {3}" \
                                   .format(tube.datafile,
                                           meta_name,
                                           meta_value,
                                           meta_type))
        
        self._tube_conditions.add(frozenset(conditions.iteritems()))
        self.data = self.data.append(new_data)
        del new_data
        
        # TODO - figure out if we can actually delete the original tube's data

if __name__ == "__main__":
    ex = Experiment()
    ex.add_conditions({"time" : "category"})
    
    tube1 = fc.FCMeasurement(ID='Test 1', 
                       datafile='../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs')
    
    tube2 = fc.FCMeasurement(ID='Test 2', 
                       datafile='../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')
    
    ex.add_tube(tube1, {"time" : "one"})
    ex.add_tube(tube2, {"time" : "two"})
    
    print(ex.data)

