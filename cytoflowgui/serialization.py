'''
Keep all the camel serialization bits together.
Created on Dec 2, 2017

@author: brian
'''

from textwrap import dedent

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

# camel adaptors for traits lists, dicts, numpy types
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
        code = "op_{} = {}\n\n".format(i, repr(wi.operation))
        
        if(hasattr(wi.operation, 'estimate')):
            code += "op_{}.estimate()\n".format(i)
            
        if i == 0:
            code += "ex_{} = op_{}.apply()\n".format(i, i)
        else:
            code += "ex_{} = op_{}.apply(ex_{})\n".format(i, i, i-1)
            
#         code = FormatCode(code)
        nb['cells'].append(nbf.v4.new_code_cell(code))
            
        for view in wi.views:
            code = "{}.plot(ex_{})\n".format(repr(view), i)
#             code = FormatCode(code)
            nb['cells'].append(nbf.v4.new_code_cell(code))
            
    with open(path, 'w') as f:
        nbf.write(nb, f)

