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

from builtins import zip
from past.builtins import basestring
import pandas as pd
from traits.api import (HasStrictTraits, Dict, List, Instance, Str, Any,
                       Property, Tuple)

import cytoflow.utility as util

class Experiment(HasStrictTraits):
    """An Experiment manages all the data and metadata for a flow experiment.
    
    An `Experiment` is `cytoflow`'s central data structure: it wraps a 
    `pandas.DataFrame` containing all the data from a flow experiment. Each 
    row in the table is an event.  Each column is either a measurement from one 
    of the detectors (or a "derived" measurement such as a transformed value or
    a ratio), or a piece of metadata associated with that event: which 
    tube it came from, what the experimental conditions for that tube were, 
    gate membership, etc.  The `Experiment` object lets you:
      - Add additional metadata to define subpopulations
      - Get events that match a particular metadata signature.
      
    Additionally, the `Experiment` object manages channel- and experiment-level
    metadata in the `metadata` field, which is a dictionary.  This allows
    the rest of the `cytoflow` package to track and enforce other constraints
    that are important in doing quantitative flow cytometry: for example,
    every tube must be collected with the same channel parameters (such 
    as PMT voltage.)

    NOTE: `Experiment` is not responsible for enforcing the constraints; 
    `cytoflow.ImportOp` and the other modules are.
    
    Attributes
    ----------

    data : pandas.DataFrame
        the `DataFrame` representing all the events and metadata.  Each event
        is a row; each column is either a measured channel (ie a fluorescence
        measurement), a derived channel (eg the ratio between two channels), or
        a piece of metadata.  Metadata can be either experimental conditions 
        (eg induction level, timepoint) or added by operations (eg gate 
        membership).
        
    metadata : Dict(Str : Dict(Str : Any)
        Each column in `Experiment.data` has an entry in `Experiment.metadata`
        whose key is the column name and whose value is a dict of 
        column-specific metadata.  Metadata is added by operations, and is
        occasionally useful if modules are expected to work together.  See
        individual operations' documentation for a list of the metadata that
        operation adds.  The only "required" metadata is `type`, which can
        be `channel` (if the column is a measured channel, or derived from
        one) or `condition` (if the column is an experimental condition,
        gate membership, etc.)
        
        NOTE!  There may also be experiment-wide entries in `metadata` that
        are NOT columns in `data`!
    
    history : List(IOperation)
        A list of the operations that have been applied to the raw data that
        have led to this Experiment.
        
    statistics : Dict((Str, Str) : pandas.Series)
        A dictionary of statistics and parameters computed by models that were
        fit to the data.  The key is an (Str, Str) tuple, where the first Str
        is the name of the operation that supplied the statistic, and the second
        Str is the name of the statistic. The value is a multi-indexed pandas
        Series: each level of the index is a facet, and each combination of
        indices is a subset for which the statistic was computed.  The values 
        of the series, of course, are the values of the computed parameters or
        statistics for each subset.
    
    channels : List(String)
        A read-only `List` containing the channels that this experiment tracks.
    
    conditions : Dict(String : pandas.Series)
        A read-only Dict of the experimental conditions and analysis groups 
        (gate membership, etc) and that this experiment tracks.  The key is the 
        name of the condition, and the value is a pandas.Series with that
        condition's possible values. 

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
       ourselves instead of making the client deal with it.  We can pretend
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
    
    # statistics.  mutable, deep copy required
    statistics = Dict(Tuple(Str, Str), pd.Series, copy = "deep")
    
    history = List(Any)
    
    channels = Property(List)
    conditions = Property(Dict)
            
    def __getitem__(self, key):
        """Override __getitem__ so we can reference columns like ex.column"""
        return self.data.__getitem__(key)
     
    def __setitem__(self, key, value):
        """Override __setitem__ so we can assign columns like ex.column = ..."""
        return self.data.__setitem__(key, value)
    
    def __len__(self):
        return len(self.data)

    def _get_channels(self):
        return [x for x in self.data if self.metadata[x]['type'] == "channel"]
    
    def _get_conditions(self):
        return {x : pd.Series(self.data[x].unique()).sort_values() for x in self.data
                if self.metadata[x]['type'] == "condition"}
        
    def subset(self, conditions, values):
        """
        Returns a subset of this experiment including only the events where
        each condition `condition` equals the corresponding value in `values`.
        
        
        Parameters
        ----------
        conditions : Str or Tuple(Str)
            A condition or list of conditions
            
        values : Any or Tuple(Any)
            The value(s) of the condition(s)
            
        """

        if isinstance(conditions, basestring):
            c = conditions
            v = values
            if c not in self.conditions:
                raise util.CytoflowError("{} is not a condition".format(c))
            if v not in list(self.conditions[c]):
                raise util.CytoflowError("{} is not a value of condition {}".format(v, c))
        else:
            for c, v in zip(conditions, values):
                if c not in self.conditions:
                    raise util.CytoflowError("{} is not a condition".format(c))
                if v not in list(self.conditions[c]):
                    raise util.CytoflowError("{} is not a value of condition {}".format(v, c))

        g = self.data.groupby(conditions)

        ret = self.clone()
        ret.data = g.get_group(values)
        ret.data.reset_index(drop = True, inplace = True)
        
        return ret    
    
    def query(self, expr, **kwargs):
        """
        Return an experiment whose data is a subset of this one where `expr`
        evaluates to `True`.

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
            
        Returns
        -------
        A new `Experiment`, a clone of this one with the data returned by
        `pandas.DataFrame.query()`
        """
        
        resolvers = {}
        for name, col in self.data.iteritems():
            new_name = util.sanitize_identifier(name)
            if new_name in resolvers:
                raise util.CytoflowError("Tried to sanitize column name {1} to "
                                         "{2} but it already existed in the "
                                         " DataFrame."
                                         .format(name, new_name))
            else:
                resolvers[new_name] = col
                
        ret = self.clone()
        ret.data = self.data.query(expr, resolvers = ({}, resolvers), **kwargs)
        ret.data.reset_index(drop = True, inplace = True)
        
        if len(ret.data) == 0:
            raise util.CytoflowError("No events matched {}".format(expr))
        
        return ret
    
    def clone(self):
        """Clone this experiment"""
        new_exp = self.clone_traits()
        new_exp.data = self.data.copy(deep = False)

        # shallow copy of the history
        new_exp.history = self.history[:]
        return new_exp
            
    def add_condition(self, name, dtype, data = None):
        """Add a new column of per-event metadata to this `Experiment`.  Operates
           *in place*.
        
        There are two places to call `add_condition`.
          - As you're setting up a new `Experiment`, call `add_condition()`
            with `data` set to `None` to specify the conditions the new events
            will have.
          - If you compute some new per-event metadata on an existing 
            `Experiment`, call `add_condition()` to add it. 
        
        Parameters
        ----------
        name : String
            The name of the new column in `self.data`.  Must be a valid Python
            identifier: must start with `[A-Z]`, `[a-z]` or `_` and contain
            only the characters `[A-Z]`, `[a-z]`, `[0-9]` or `_`.
        
        dtype : String
            The type of the new column in `self.data`.  Must be a string that
            `pandas.Series` recognizes as a `dtype`: common types are 
            "category", "float", "int", and "bool".
            
        data : pandas.Series (default = None)
            The `pandas.Series` to add to `self.data`.  Must be the same
            length as `self.data`, and it must be convertable to a 
            `pandas.Series` of type `dtype`.  If `None`, will add an
            empty column to the `Experiment` ... but the `Experiment` must
            be empty to do so!
             
        Raises
        ------
        CytoflowError
            If the `pandas.Series` passed in `data` isn't the same length
            as `self.data`, or isn't convertable to type `dtype`.          
            
        Examples
        --------
        >>> import cytoflow as flow
        >>> ex = flow.Experiment()
        >>> ex.add_condition("Time", "float")
        >>> ex.add_condition("Strain", "category")      
        """
        
        if name != util.sanitize_identifier(name):
            raise util.CytoflowError("Name '{}' is not a valid Python identifier"
                                     .format(name))
        
        if name in self.data:
            raise util.CytoflowError("Already a column named {0} in self.data"
                                     .format(name))
        
        if data is None and len(self) > 0:
            raise util.CytoflowError("If data is None, self.data must be empty!")
        
        if data is not None and len(self) != len(data):
            raise util.CytoflowError("data must be the same length as self.data")
        
        try:
            if data is not None:
                self.data[name] = data.astype(dtype, copy = True)
            else:
                self.data[name] = pd.Series(dtype = dtype)
          
        except (ValueError, TypeError) as exc:
                raise util.CytoflowError("Had trouble converting data to type {0}"
                                    .format(dtype)) from exc
                                        
        self.metadata[name] = {}
        self.metadata[name]['type'] = "condition"      
            
    def add_channel(self, name, data = None):
        """Add a new column of per-event "data" (as opposed to metadata) to this
          `Experiment`: ie, something that was measured per cell, or derived
          from per-cell measurements.  Operates *in place*.
        
        Parameters
        ----------
        name : String
            The name of the new column in `self.data`.
            
        data : pandas.Series
            The `pandas.Series` to add to `self.data`.  Must be the same
            length as `self.data`, and it must be convertable to a 
            dtype of `float64` of type `dtype`.  If `None`, will add an
            empty column to the `Experiment` ... but the `Experiment` must
            be empty to do so!
             
        Raises
        ------
        CytoflowError
            If the `pandas.Series` passed in `data` isn't the same length
            as `self.data`, or isn't convertable to a dtype `float64`.          
            
        Examples
        --------
        >>> ex.add_channel("FSC_over_2", ex.data["FSC-A"] / 2.0) 
        """
        
        if name in self.data:
            raise util.CytoflowError("Already a column named {0} in self.data"
                                .format(name))

        if data is None and len(self) > 0:
            raise util.CytoflowError("If data is None, self.data must be empty!")

        if data is not None and len(self) != len(data):
            raise util.CytoflowError("data must be the same length as self.data")
        
        try:
            if data is not None:
                self.data[name] = data.astype("float64", copy = True)
            else:
                self.data[name] = pd.Series(dtype = "float64")
                
        except (ValueError, TypeError) as exc:
                raise util.CytoflowError("Had trouble converting data to type \"float64\"") from exc

        self.metadata[name] = {}
        self.metadata[name]['type'] = "channel"
        
    def add_events(self, data, conditions):
        """
        Add new events to this Experiment.
        
        Each new event in `data` is appended to `self.data`, and its per-event
        metadata columns will be set with the values specified in `conditions`.
        Thus, it is particularly useful for adding tubes of data to new
        experiments, before additional per-event metadata is added by gates,
        etc.
        
        EVERY column in `self.data` must be accounted for.  Each column of
        type `channel` must appear in `data`; each column of metadata must
        have a key:value pair in `conditions`.
        
        Parameters
        ----------
        tube : pandas.DataFrame
            A single tube or well's worth of data. Must be a DataFrame with
            the same columns as `self.channels`
        
        conditions : Dict(Str, Any)
            A dictionary of the tube's metadata.  The keys must match 
            `self.conditions`, and the values must be coercable to the
            relevant `numpy` dtype.
 
        Raises
        ------
        CytoflowError
            - If there are columns in `data` that aren't channels in the 
              experiment, or vice versa. 
            - If there are keys in `conditions` that aren't conditions in
              the experiment, or vice versa.
            - If there is metadata specified in `conditions` that can't be
              converted to the corresponding metadata dtype.
            
        Examples
        --------
        >>> import cytoflow as flow
        >>> import fcsparser
        >>> ex = flow.Experiment()
        >>> ex.add_condition("Time", "float")
        >>> ex.add_condition("Strain", "category")
        >>> tube1, _ = fcparser.parse('CFP_Well_A4.fcs')
        >>> tube2, _ = fcparser.parse('RFP_Well_A3.fcs')
        >>> ex.add_events(tube1, {"Time" : 1, "Strain" : "BL21"})
        >>> ex.add_events(tube2, {"Time" : 1, "Strain" : "Top10G"})
        """

        # make sure the new tube's channels match the rest of the 
        # channels in the Experiment
    
        if len(self) > 0 and set(data.columns) != set(self.channels):
            raise util.CytoflowError("New events don't have the same channels")
            
        # check that the conditions for this tube exist in the experiment
        # already

        if( any(True for k in conditions if k not in self.conditions) or \
            any(True for k in self.conditions if k not in conditions) ):
            raise util.CytoflowError("Metadata for this tube should be {}"
                                     .format(list(self.conditions.keys())))
            
        # add the conditions to tube's internal data frame.  specify the conditions
        # dtype using self.conditions.  check for errors as we do so.
        
        # take this chance to up-convert the float32s to float64.
        # this happened automatically in DataFrame.append(), below, but 
        # only in certain cases.... :-/
        
        # TODO - the FCS standard says you can specify the precision.  
        # check with int/float/double files!
        
        new_data = data.astype("float64", copy=True)
        
        for meta_name, meta_value in conditions.items():
            meta_type = self.conditions[meta_name].dtype

            new_data[meta_name] = \
                pd.Series(data = [meta_value] * len(new_data),
                          index = new_data.index,
                          dtype = meta_type)
            
            # if we're categorical, merge the categories
            if meta_type.name == "category" and meta_name in self.data:
                cats = set(self.data[meta_name].cat.categories) | set(new_data[meta_name].cat.categories)
                self.data[meta_name] = self.data[meta_name].cat.set_categories(cats)
                new_data[meta_name] = new_data[meta_name].cat.set_categories(cats)
        
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
