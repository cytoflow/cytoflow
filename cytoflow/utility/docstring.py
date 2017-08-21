'''
Created on Aug 13, 2017

@author: brian
'''

import re
from warnings import warn

def expand_class_attributes(cls):
    
    if cls.__doc__ is None:
        return
    
    lines = cls.__doc__.split("\n")
    
    first_attr_line, last_attr_line = find_section("Attributes", lines)
    if first_attr_line is None:
        warn("Couldn't find 'Attributes' section for {}".format(cls.__name__))
        return
    
    cls_attr = []
     
    for mro_cls in reversed(cls.__mro__):
        mro_attr = get_class_attributes(mro_cls)
                
        for mro_attr_name, mro_attr_type, mro_attr_body in mro_attr:
            do_add = True
            for cls_attr_name, _, _ in cls_attr:
                if cls_attr_name == mro_attr_name:
                    do_add = False
            if do_add:
                cls_attr.append((mro_attr_name, mro_attr_type, mro_attr_body))
                
    new_cls_attr = []
    for i in range(len(cls_attr)):
        for j in range(i+1, len(cls_attr)):
            if cls_attr[i] is not None and cls_attr[j] is not None and \
               cls_attr[i][1] == cls_attr[j][1] and \
               cls_attr[i][2] == cls_attr[j][2]:
                name = cls_attr[i][0] + ', ' + cls_attr[j][0]
                cls_attr[i] = (name, cls_attr[i][1], cls_attr[i][2])
                cls_attr[j] = None
        if cls_attr[i] is not None:
            new_cls_attr.append(cls_attr[i])

    attr_section = []
    for attr_name, attr_value, attr_body in new_cls_attr:
        attr_section.append("    " + attr_name + " : " + attr_value)
        attr_section.extend(attr_body)
        attr_section.append("")
            
    lines[first_attr_line:last_attr_line + 1] = attr_section
    
    cls.__doc__ = "\n".join(lines)
    
def expand_method_parameters(cls, method):
    if method.__doc__ is None:
        return
    
    lines = method.__doc__.split("\n")
    
    first_param_line, last_param_line = find_section("Parameters", lines)
    if first_param_line is None:
        warn("Couldn't find a 'Parameters' section for {}".format(method.__name__))
        return
    
    method_params = []
     
    for mro_cls in reversed(cls.__mro__):
        try:
            mro_method = getattr(mro_cls, method.__name__)
        except:
            continue
        
        mro_params = get_method_parameters(mro_method)
        
        for mro_param_name, mro_param_type, mro_param_body in mro_params:
            do_add = True
            for method_param_name, _, _ in method_params:
                if method_param_name == mro_param_name:
                    do_add = False
            if do_add:
                method_params.append((mro_param_name, mro_param_type, mro_param_body))
                                
    new_method_params = []
    for i in range(len(method_params)):
        for j in range(i+1, len(method_params)):
            if method_params[i] is not None and method_params[j] is not None and \
               method_params[i][1] == method_params[j][1] and \
               method_params[i][2] == method_params[j][2]:
                name = method_params[i][0] + ', ' + method_params[j][0]
                method_params[i] = (name, method_params[i][1], method_params[i][2])
                method_params[j] = None
        if method_params[i] is not None:
            new_method_params.append(method_params[i])

    params_section = []
    for param_name, param_type, param_body in new_method_params:
        params_section.append("        " + param_name + " : " + param_type)
        params_section.extend(param_body)
        params_section.append("")
        
    lines[first_param_line:last_param_line + 1] = params_section
        
    method.__doc__ = "\n".join(lines)    


def find_section(section, lines):
    # find the attributes section
    first_line = None
    for i, line in enumerate(lines):
        if "----" in line and i > 0 and section in lines[i - 1]:
            first_line = i + 1
            break    
        
    if first_line is None:
        return None, None
       
    last_line = None
        
    for i in range(first_line, len(lines)):
        if "---" in lines[i]:
            last_line = i - 2
            break
        
    if last_line is None:
        last_line = len(lines) - 1
        
    return first_line, last_line
        

def get_class_attributes(cls):
    if not cls.__doc__:
        return []

    lines = cls.__doc__.split('\n')    
    first_attr_line, last_attr_line = find_section("Attributes", lines)
        
    attributes = []
                
    # consume the attributes
    for  attr_name, attr_value, attr_body in get_params_and_attrs(lines, first_attr_line, last_attr_line):
        attributes.append((attr_name, attr_value, attr_body))
        
    return attributes

def get_method_parameters(method):
    if not method.__doc__:
        return []

    lines = method.__doc__.split('\n')    
    first_param_line, last_param_line = find_section("Parameters", lines)
        
    params = []
                
    # consume the attributes
    for param_name, param_value, param_body in get_params_and_attrs(lines, first_param_line, last_param_line):
        params.append((param_name, param_value, param_body))
        
    return params


def get_params_and_attrs(lines, first_attr_line, last_attr_line):
    if first_attr_line is None:
        return
        
    attr_names = None
    attr_type = None
    attr_body = []
    
    for i in range(first_attr_line, last_attr_line):
        if attr_names is None:
            colon_idx = lines[i].find(':')
            if colon_idx == -1:
                continue
            attr_names = lines[i][:colon_idx]
            attr_names = attr_names.split(',')
            attr_names = [x.strip() for x in attr_names]
            attr_type = lines[i][colon_idx + 1:].strip()
            
        if re.match('^\s*$', lines[i]):
            for attr_name in attr_names:
                yield attr_name, attr_type, attr_body[1:]
            attr_names = None
            attr_body = []
        else:
            attr_body.append(lines[i])
            
    if attr_names is not None:
        for attr_name in attr_names:
            yield attr_name, attr_type, attr_body[1:]

