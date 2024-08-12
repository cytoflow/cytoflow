#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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

"""
cytoflowgui.workflow.serialization
----------------------------------

Utility bits that let us use `camel` to serialize a `RemoteWorkflow`.  

Many of the dumpers and loaders support serializing `pandas` types,
such as `pandas.Series` and `pandas.DataFrame`, or for testing
serialization with unit tests.
"""

import pandas, numpy
from pandas.api.types import CategoricalDtype

from traits.api import DelegationError

from textwrap import dedent  # @UnusedImport

#### YAML serialization

from camel import Camel, CamelRegistry, YAML_TAG_PREFIX

# the camel registry singletons
camel_registry = CamelRegistry()
standard_types_registry = CamelRegistry(tag_prefix = YAML_TAG_PREFIX)

def load_yaml(path):
    """
    Load a Python object from a YAML file.
    
    Parameters
    ----------
    path : string
        The path to the YAML file to load
           
    Returns
    -------
    object
        The Python object loaded from the YAML file
    """
    
    with open(path, 'r') as f:
        data = Camel([camel_registry]).load(f.read())
        
    return data

def save_yaml(data, path, lock_versions = {}):
    """
    Save a Python object to a YAML file
    
    Parameters
    ----------
    data : object
        The Python object to serialize
        
    path : string
        The path to save to
        
    lock_versions : dict
         A dictionary of types and versions of dumpers to use
         when serializing.
    """
    
    with open(path, 'w') as f:
        c = Camel([standard_types_registry, camel_registry])
        for klass, version in lock_versions.items():
            c.lock_version(klass, version)
        f.write(c.dump(data))

# camel adapters for traits lists and dicts, numpy types
from numpy import float64, int64, bool_
@standard_types_registry.dumper(float64, 'float', version = None)
def _dump_float(fl):
    return repr(float(fl)).lower()

@standard_types_registry.dumper(int64, 'int', version = None)
def _dump_int(i):
    return repr(int(i)).lower()

@standard_types_registry.dumper(bool_, 'bool', version = None)
def _dump_bool(b):
    return repr(bool(b)).lower()

from traits.trait_handlers import TraitListObject, TraitDictObject
from traits.api import Undefined

@standard_types_registry.dumper(TraitListObject, 'seq', version = None)
def _dump_list(tlo):
    return list(tlo)
 
@standard_types_registry.dumper(TraitDictObject, 'map', version = None)
def _dump_dict(tdo):
    return dict(tdo)

# for some reason, the version of this in camel.__init__ doesn't get called.
# if we re-define it here, everything is fine.
@standard_types_registry.dumper(tuple, 'python/tuple', version=None)
def _dump_tuple(data):
    return list(data)

@standard_types_registry.loader('python/tuple', version=None)
def _load_tuple(data, version):
    return tuple(data)

# @standard_types_registry.dumper(TraitTuple, 'python/tuple', version = None)
# def _dump_tuple(tt):
#     return list(tt)

@camel_registry.dumper(Undefined.__class__, 'undefined', version = 1)
def _dump_undef(ud):
    return "Undefined"

@camel_registry.loader('undefined', version = 1)
def _load_undef(data, version):
    return Undefined

@camel_registry.dumper(numpy.dtype, 'numpy-dtype', version = 1)
def _dump_dtype(d):
    return str(d)

@camel_registry.loader('numpy-dtype', version = 1)
def _load_dtype(data, version):
    return numpy.dtype(data)

@camel_registry.dumper(CategoricalDtype, 'pandas-categorical-dtype', version = 1)
def _dump_categorical_dtype(d):
    return dict(categories = list(d.categories),
                ordered = d.ordered)
    
@camel_registry.loader('pandas-categorical-dtype', version = 1)
def _load_categorical_dtype(data, version):
    return CategoricalDtype(categories = data['categories'],
                            ordered = data['ordered'])

@camel_registry.dumper(pandas.MultiIndex, 'pandas-multiindex', version = 1)
def _dump_multiindex_v1(d):
    return dict(levels = list(d.levels),
                labels = [x.tolist() for x in d.codes],
                names = list(d.names))
    
@camel_registry.dumper(pandas.MultiIndex, 'pandas-multiindex', version = 2)
def _dump_multiindex_v2(d):
    return dict(levels = list(d.levels),
                codes = [x.tolist() for x in d.codes],
                names = list(d.names))

@camel_registry.loader('pandas-multiindex', version = 1)
def _load_multiindex_v1(data, version):
    return pandas.MultiIndex(levels = data['levels'],
                             codes = data['labels'],
                             names = data['names'])
    
@camel_registry.loader('pandas-multiindex', version = 2)
def _load_multiindex_v2(data, version):
    return pandas.MultiIndex(levels = data['levels'],
                             codes = data['codes'],
                             names = data['names'])
    
@camel_registry.dumper(pandas.Index, 'pandas-index', version = 1)
def _dump_index(d):
    return dict(name = d.name,
                values = d.values.tolist(),
                dtype = str(d.dtype))
    
@camel_registry.loader('pandas-index', version = 1)
def _load_index(data, version):
    return pandas.Index(name = data['name'],
                        data = data['values'],
                        dtype = data['dtype'])


# Int64Index went away in pandas 2.0
# @camel_registry.dumper(pandas.Int64Index, 'pandas-int64index', version = 1)
# def _dump_int64index(d):
#     return dict(name = d.name,
#                 values = d.values.tolist())

@camel_registry.loader('pandas-int64index', version = 1)
def _load_int64index(data, version):
    return pandas.Index(name = data['name'],
                        data = data['values'],
                        dtype = numpy.int64)

# Float64Index went away in pandas 2.0
# @camel_registry.dumper(pandas.Float64Index, 'pandas-float64index', version = 1)
# def _dump_float64index(d):
#     return dict(name = d.name,
#                 values = d.values.tolist())

@camel_registry.loader('pandas-float64index', version = 1)
def _load_float64index(data, version):
    return pandas.Index(name = data['name'],
                        data = data['values'],
                        dtype = numpy.float64)

@camel_registry.dumper(pandas.CategoricalIndex, 'pandas-categoricalindex', version = 1)
def _dump_categoricalindex(d):
    return dict(name = d.name,
                values = d.values.tolist(),
                categories = d.categories.values.tolist(),
                ordered = d.ordered)

@camel_registry.loader('pandas-categoricalindex', version = 1)
def _load_categoricalindex(data, version):
    return pandas.CategoricalIndex(name = data['name'],
                                   data = data['values'],
                                   categories = data['categories'],
                                   ordered = data['ordered'])

    
@camel_registry.dumper(pandas.Series, 'pandas-series', version = 1)
def _dump_series_v1(s):
    return dict(index = list(s.index),
                data = list(s.values))

@camel_registry.dumper(pandas.Series, 'pandas-series', version = 2)
def _dump_series_v2(s):
    return dict(index = s.index,
                data = s.values.tolist(),
                dtype = s.dtype)

@camel_registry.dumper(pandas.Series, 'pandas-series', version = 3)
def _dump_series(s):
    return dict(index = s.index,
                data = s.values.tolist(),
                dtype = str(s.dtype))
    
@camel_registry.loader('pandas-series', version = 1)
def _load_series_v1(data, version):
    ret = pandas.Series(data = data['data'],
                        index = data['index'])

    if str(ret.dtype) == 'object':
        ret = pandas.Series(data = data['data'],
                            index = data['index'],
                            dtype = "category")
        
    return ret
    
@camel_registry.loader('pandas-series', version = 2)
def _load_series_v2(data, version):
    return pandas.Series(data = data['data'],
                         index = data['index'],
                         dtype = data['dtype'])

@camel_registry.loader('pandas-series', version = 3)
def _load_series_v3(data, version):
    return pandas.Series(data = data['data'],
                         index = data['index'],
                         dtype = data['dtype'])
    
# a few bits for testing serialization
def traits_eq(self, other):
    """Are the copyable traits of two `traits.has_traits.HasTraits` equal?"""
    return self.trait_get(self.copyable_trait_names()) == other.trait_get(self.copyable_trait_names())

def traits_hash(self):
    """Get a unique hash of a `traits.has_traits.HasTraits`"""
    return hash(tuple(self.trait_get(self.copyable_trait_names()).items()))

# set underlying cytoflow repr
def traits_repr(obj):
    """A uniform implementation of **__repr__** for `traits.has_traits.HasTraits`"""
    return obj.__class__.__name__ + '(' + traits_str(obj) + ')'

def traits_str(obj):
    """A uniform implementation of **__str__** for `traits.has_traits.HasTraits`"""
    try:
        traits = obj.trait_get(transient = lambda x: x is not True,
                               status = lambda x: x is not True,
                               type = lambda x: x != 'delegate')
        
        traits.pop('op', None)
        
        # filter out traits that haven't changed
        default_traits = obj.__class__().trait_get(transient = lambda x: x is not True,
                                                   status = lambda x: x is not True,
                                                   type = lambda x: x != 'delegate')
        
        traits = [(k, v) for k, v in traits.items() if k not in default_traits 
                                            or v != default_traits[k]]

        # %s uses the str function and %r uses the repr function
        traits_str = ', '.join(["%s = %s" % (k, v.__name__) 
                                if callable(v)
                                else "%s = %r" % (k, v)  
                                for k, v in traits])
        
        return traits_str
                
    except DelegationError:
        return obj.__class__.__name__ + '(<Delegation error>)'