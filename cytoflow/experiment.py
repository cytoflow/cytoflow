import pandas as pd
from traits.api import HasStrictTraits, Dict, List, Instance, Set, Str, Any, \
                       Property, cached_property

from utility import CytoflowError, sanitize_identifier

class Experiment(HasStrictTraits):
    """An Experiment manages all the data and metadata for a flow experiment.
    
    A flow cytometry experiment consists of:
      - A set of tubes or wells in a multi-well plate.  Each tube or well
        contains cells subjected to different experimental conditions.
      - An array of events from each well or tube.  Each event is a tuple of 
        measurements of a single cell.
        
    ....subject to the following constraints:

      - Each tube or well MUST have identical channels (including channel 
        parameters such as PMT voltage and delay.)
      - Each tube or well MUST have a unique set of metadata.
          
    An Experiment object manages all this data.  By "manage", we mean:
      - Get events that match a particular metadata "signature"
      - Add additional metadata to define populations, etc.

    NOTE: `Experiment` is not responsible for enforcing the constraints; 
    `cytoflow.ImportOp` is.  Which is to say, you can break these rules if
    you need to.  I don't recommend it.  (-;
    
    Attributes
    ----------

    data : pandas.DataFrame
        the `DataFrame` representing all the events and metadata.  Each event
        is a row; each column is either a measured channel (ie a fluorescence
        measurement), a derived channel (eg the ratio between two channels), or
        a piece of metadata.  Metadata can be either supplied by the tube 
        conditions (eg induction level, timepoint) or by operations (eg gate
        membership)
        
    metadata : Dict(Str : Any)
        The experimental metadata.  In particular, each column in self.data has
        an entry whose key is the column name and whose value is a dict of
        column-specific metadata. Operations may define their own metadata, 
        which is occasionally useful if modules are expected to work together.
        An incomplete list of column-specific metadata:
        * type (Enum: "channel", "category", "float", "int", "bool") : what kind
            of data is stored in this column?  If the column is event
            measurement data (raw, transformed, or derived), then the value is 
            "channel".  If the column is per-event metadata, then the value is
            a NumPy `dtype` -- `category`, `float`, `int`, or `bool`.
        * voltage (int) : for channels, the detector voltage used. from the FCS
            keyword "$PnV".
        * range (float) : for channels, the maximum possible value.  from the FCS
            keyword "$PnR"
        * repr : for float conditions, whether to plot it linearly or on
            a log scale.
        * xforms, xforms_inv: for channels, a list of (parameterized!) 
            transformations that have been applied.  each must be a
            one-parameter function that takes either a single value or a list 
            of values and applies the transformation (or inverse).  necessary
            for computing tic marks on plots, among other things.
            
        Note! There may be *other* experiment-wide things in `metadata`; 
        the fact that a key is in `metadata` does not mean a corresponding
        column exists in `data`.
    
    channels : List(String)
        A read-only `List` containing the channels that this experiment tracks.
    
    conditions : Dict(String : String)
        A read-only Dict of the experimental conditions and analysis metadata 
        (gate membership, etc) and that this experiment tracks.  The key is the 
        name of the condition, and the value is the string representation of the 
        `numpy` dtype (usually one of "category", "float", "int" or "bool".)
        
    Notes
    -----              
      
    Note that nowhere do we mention filters or gates.  You can define gate,
    sure .... but applying that gate to an Experiment simply adds another
    condition for each event, indicating that the event is in the new
    population or not.  This is in contrast to traditional cytometry tools,
    which allow you to define a tree-like gating "hierarchy."
        
    Finally, all this is implemented on top of a pandas DataFrame.... which
    earns us all sorts of fun optimization, and lets us select subsets easily:
        
    >>> ex.query('Induced == True') 

    Implementation details
    ----------------------
    
    The OOP programmer in me desperately wanted to subclass DataFrame, add
    some flow-specific stuff, and move on with my life.  (I may still, with
    something like https://github.com/dalejung/pandas-composition).  A few 
    things get in the way of directly subclassing pandas.DataFrame:
    
     - First, to enable some of the delicious syntactic sugar for accessing
       its contents, DataFrame redefines ``__getattribute__`` and 
       ``__setattribute__``, and making it recognize (and maintain across 
       copies) additional attributes is an unsupported (non-public) API 
       feature and introduces other subclassing weirdness.
    
     - Second, many of the operations (like appending!) don't happen in-place;
       they return copies instead.  It's cleaner to simply manage that copying
       ourselves instead of making the client deal with it.  we can pretend
       to operate on the data in-place.
       
    To maintain the ease of use, we'll override __getitem__ and pass it to
    the wrapped DataFrame.  We'll do the same with some of the more useful
    DataFrame API pieces (like query()); and of course, you can just get the
    data frame itself with Experiment.data
    
    Examples
    --------
    >>> import cytoflow as flow
    >>> tube1 = flow.Tube(file = 'cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
    ...                   conditions = {"Dox" : 10.0})
    >>> tube2 = flow.Tube(file='cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
    ...                   conditions = {"Dox" : 1.0})
    >>> 
    >>> import_op = flow.ImportOp(conditions = {"Dox" : "float"},
    ...                           tubes = [tube1, tube2])
    >>> 
    >>> ex = import_op.apply()
    >>> ex.data.shape
    (20000, 17)
    >>> ex.data.groupby(['Dox']).size()
    Dox
    1      10000
    10     10000
    dtype: int64

    """

    # this doesn't play nice with copy.copy(); clone it ourselves.
    data = Instance(pd.DataFrame, args=())
    
    # potentially mutable.  deep copy required
    metadata = Dict(Str, Any, copy = "deep")
    
    channels = Property(List, depends_on = "metadata")
    conditions = Property(Dict, depends_on = "metadata")
            
    def __getitem__(self, key):
        """Override __getitem__ so we can reference columns like ex.column"""
        return self.data.__getitem__(key)
     
    def __setitem__(self, key, value):
        """Override __setitem__ so we can assign columns like ex.column = ..."""
        return self.data.__setitem__(key, value)
    
    @cached_property
    def _get_channels(self):
        return [x for x in self.metadata
                if x in self.data
                and self.metadata[x]['type'] == "channel"]
    
    @cached_property
    def _get_conditions(self):
        return {x : self.metadata[x]['type'] for x in self.metadata
                if x in self.data
                and self.metadata[x]['type'] != "channel"}
    
    def query(self, expr, **kwargs):
        """
        Expose pandas.DataFrame.query() to the outside world

        This method "sanitizes" column names first, replacing characters that
        are not valid in a Python identifier with an underscore '_'. So, the
        column name `a column` becomes `a_column`, and can be queried with
        an `a_column == True` or such.
        
        Parameters
        ----------
        expr : string
            The expression to pass to `pandas.DataFrame.query()`.  Must be
            a valid Python expression, something you could pass to `eval()`.
            
        **kwargs : dict
            Other named parameters to pass to `pandas.DataFrame.query()`.
        """
        
        resolvers = {}
        for name, col in self.data.iteritems():
            new_name = sanitize_identifier(name)
            if new_name in resolvers:
                raise CytoflowError("Tried to sanitize column name {1} to {2} "
                                    "but it already existed in the DataFrame."
                                    .format(name, new_name))
            else:
                resolvers[new_name] = col

        return self.data.query(expr, resolvers = ({}, resolvers), **kwargs)
    
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
        CytoflowError
            If you call add_conditions() after you've already started adding
            tubes.          
            
        Examples
        --------
        >>> import cytoflow as flow
        >>> ex = flow.Experiment()
        >>> ex.add_conditions({"Time" : "float", "Strain" : "category"})      
        """
        
        if(len(self.data.index) > 0):
            raise CytoflowError("You can't add conditions after you have "
                                "already added a tube!")              
    
        for key, _ in conditions.iteritems():
            if key in self.metadata:
                raise CytoflowError("You have already added condition {0}"
                                    .format(key))
            
        for key, key_type in conditions.iteritems():
            self.data[key] = []
            self.metadata[key] = {}
            self.metadata[key]['type'] = key_type
        
    def add_tube(self, tube, conditions):
        """
        Add a tube of data, and its experimental conditions, to this Experiment.
        
        Remember: because add_tube COPIES the data into this Experiment, you can
        DELETE the tube after you add it (and save memory)
        
        Parameters
        ----------
        tube : pandas.DataFrame
            A single tube or well's worth of data. Must be a DataFrame with
            the same columns as `self.data`
        
        conditions : Dict(Str, Any)
            A dictionary of the tube's metadata.  The keys must match 
            `self.conditions`, and the values must be coercable to the
            relevant `numpy` dtype.
 
        Raises
        ------
        CytoflowError
            - If you try to add tubes with different channels
            - If you try to add tubes with identical metadata
            - If you try to add tubes with metadata that can't be converted
            
        Examples
        --------
        >>> import cytoflow as flow
        >>> import fcsparser
        >>> ex = flow.Experiment()
        >>> ex.add_conditions({"Time" : "float", "Strain" : "category"})
        >>> tube1, _ = fcparser.parse('CFP_Well_A4.fcs')
        >>> tube2, _ = fcparser.parse('RFP_Well_A3.fcs')
        >>> ex.add_tube(tube1, {"Time" : 1, "Strain" : "BL21"})
        >>> ex.add_tube(tube2, {"Time" : 1, "Strain" : "Top10G"})
        """

        # make sure the new tube's channels match the rest of the 
        # channels in the Experiment
    
        if len(self.data.index) > 0 and set(tube.columns) != set(self.channels):
            raise CytoflowError("Tube {0} doesn't have the same channels")
            
        # check that the conditions for this tube exist in the experiment
        # already

        if( any(True for k in conditions if k not in self.conditions) or \
            any(True for k in self.conditions if k not in conditions) ):
            raise CytoflowError("Metadata for this tube isn't the same as "
                                "self.conditions")
            
        # add the conditions to tube's internal data frame.  specify the conditions
        # dtype using self.conditions.  check for errors as we do so.
        
        # take this chance to up-convert the float32s to float64.
        # this happened automatically in DataFrame.append(), below, but 
        # only in certain cases.... :-/
        
        # TODO - the FCS standard says you can specify the precision.  
        # check with int/float/double files!
        
        new_data = tube.astype("float64", copy=True)
        
        for meta_name, meta_value in conditions.iteritems():
            meta_type = self.conditions[meta_name]
            try:
                new_data[meta_name] = \
                    pd.Series(data = [meta_value] * len(new_data.index),
                              index = new_data.index,
                              dtype = meta_type)
                
                # if we're categorical, merge the categories
                if meta_type == "category" and meta_name in self.data.columns:
                    cats = set(self.data[meta_name].cat.categories) | set(new_data[meta_name].cat.categories)
                    self.data[meta_name] = self.data[meta_name].cat.set_categories(cats)
                    new_data[meta_name] = new_data[meta_name].cat.set_categories(cats)
            except (ValueError, TypeError):
                raise CytoflowError("Had trouble converting conditions {1}"
                                   "(value = {2}) to type {3}" \
                                   .format(meta_name,
                                           meta_value,
                                           meta_type))
        
        self.data = self.data.append(new_data, ignore_index = True)
        del new_data

if __name__ == "__main__":
    import fcsparser
    ex = Experiment()
    ex.add_conditions({"time" : "category"})

    tube0, _ = fcsparser.parse('../cytoflow/tests/data/tasbe/BEADS-1_H7_H07_P3.fcs')
    tube1, _ = fcsparser.parse('../cytoflow/tests/data/tasbe/beads.fcs')
    tube2, _ = fcsparser.parse('../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')
    
    ex.add_tube(tube1, {"time" : "one"})
    ex.add_tube(tube2, {"time" : "two"})
    
    print(ex.data)

