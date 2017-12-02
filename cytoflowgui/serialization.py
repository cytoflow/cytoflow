'''
Keep all the camel serialization bits together.
Created on Dec 2, 2017

@author: brian
'''

from camel import CamelRegistry, YAML_TAG_PREFIX

# the camel registry singletons
camel_registry = CamelRegistry()
standard_types_registry = CamelRegistry(tag_prefix = YAML_TAG_PREFIX)

# camel adaptors for traits lists, dicts
from numpy import float64
@standard_types_registry.dumper(float64, 'float', version = None)
def _dump_float(fl):
    return repr(float(fl)).lower()

from traits.trait_handlers import TraitListObject, TraitDictObject

@standard_types_registry.dumper(TraitListObject, 'seq', version = None)
def _dump_list(tlo):
    return list(tlo)
 
@standard_types_registry.dumper(TraitDictObject, 'map', version = None)
def _dump_dict(tdo):
    return dict(tdo)

