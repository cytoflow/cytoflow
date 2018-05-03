'''
Keep all the camel serialization bits together.
Created on Dec 2, 2017

@author: brian
'''

from textwrap import dedent
import pandas, numpy
from pandas.api.types import CategoricalDtype

from pyface.api import error
from traits.api import DelegationError

#### YAML serialization

from camel import Camel, CamelRegistry, YAML_TAG_PREFIX

# the camel registry singletons
camel_registry = CamelRegistry()
standard_types_registry = CamelRegistry(tag_prefix = YAML_TAG_PREFIX)

def load_yaml(path):
    with open(path, 'r') as f:
        data = Camel([camel_registry]).load(f.read())
        
    return data

def save_yaml(data, path):
    with open(path, 'w') as f:
        f.write(Camel([standard_types_registry,
                       camel_registry]).dump(data))

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
def _dump_multiindex(d):
    return dict(levels = list(d.levels),
                labels = [x.tolist() for x in d.labels],
                names = list(d.names))

@camel_registry.loader('pandas-multiindex', version = 1)
def _load_multiindex(data, version):
    return pandas.MultiIndex(levels = data['levels'],
                             labels = data['labels'],
                             names = data['names'])

@camel_registry.dumper(pandas.Int64Index, 'pandas-int64index', version = 1)
def _dump_int64index(d):
    return dict(name = d.name,
                values = d.values.tolist())

@camel_registry.loader('pandas-int64index', version = 1)
def _load_int64index(data, version):
    return pandas.Int64Index(name = data['name'],
                             data = data['values'])

@camel_registry.dumper(pandas.Float64Index, 'pandas-float64index', version = 1)
def _dump_float64index(d):
    return dict(name = d.name,
                values = d.values.tolist())

@camel_registry.loader('pandas-float64index', version = 1)
def _load_float64index(data, version):
    return pandas.Float64Index(name = data['name'],
                               data = data['values'])

@camel_registry.dumper(pandas.CategoricalIndex, 'pandas-categoricalindex', version = 1)
def _dump_categoricalindex(d):
    return dict(name = d.name,
                values = d.get_values().tolist(),
                categories = d.categories.values.tolist(),
                ordered = d.ordered)

@camel_registry.loader('pandas-categoricalindex', version = 1)
def _load_categoricalindex(data, version):
    return pandas.CategoricalIndex(name = data['name'],
                                   data = data['values'],
                                   categories = data['categories'],
                                   ordered = data['ordered'])

@camel_registry.dumper(pandas.Series, 'pandas-series', version = 2)
def _dump_series(s):
    return dict(index = s.index,
                data = s.values.tolist(),
                dtype = s.dtype)
    
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
    
# a few bits for testing serialization
def traits_eq(self, other):
    return self.trait_get(self.copyable_trait_names()) == other.trait_get(self.copyable_trait_names())

def traits_hash(self):
    return hash(tuple(self.trait_get(self.copyable_trait_names()).items()))
    
#### Jupyter notebook serialization

import nbformat as nbf
from yapf.yapflib.yapf_api import FormatCode

def save_notebook(workflow, path):
    nb = nbf.v4.new_notebook()
    
    # todo serialize here
    header = dedent("""\
        from cytoflow import *
        %matplotlib inline""")
    nb['cells'].append(nbf.v4.new_code_cell(header))
        
    for i, wi in enumerate(workflow):
        try:
            code = wi.operation.get_notebook_code(i)
            code = FormatCode(code, style_config = 'pep8')[0]
        except:
            error(parent = None,
                  message = "Had trouble serializing the {} operation"
                            .format(wi.operation.friendly_id))
        
        nb['cells'].append(nbf.v4.new_code_cell(code))
                    
        for view in wi.views:
            try:
                code = view.get_notebook_code(i)
                code = FormatCode(code, style_config = 'pep8')[0]
            except:
                error(parent = None,
                      message = "Had trouble serializing the {} view of the {} operation"
                                 .format(view.friendly_id, wi.operation.friendly_id))
            
            nb['cells'].append(nbf.v4.new_code_cell(code))
            
    with open(path, 'w') as f:
        nbf.write(nb, f)

# set underlying cytoflow repr
def traits_repr(obj):
    return obj.__class__.__name__ + '(' + traits_str(obj) + ')'

def traits_str(obj):
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