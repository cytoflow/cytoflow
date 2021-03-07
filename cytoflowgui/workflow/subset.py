'''
Created on Jan 15, 2021

@author: brian
'''

from traits.api import (provides, Interface, Str, List, Property, Bool,
                        HasStrictTraits, CFloat, Undefined, on_trait_change)

from cytoflow import utility as util

from .serialization import camel_registry, traits_repr

class ISubset(Interface):
    name = Str
    values = List
    str = Property(Str)
    
@provides(ISubset)
class BoolSubset(HasStrictTraits):
    name = Str
    values = List  # unused
    selected_t = Bool(False)
    selected_f = Bool(False)
    
    str = Property(Str, depends_on = "name, selected_t, selected_f")
    
#     def default_traits_view(self):
#         return View(HGroup(Item('selected_t',
#                                 label = self.name + "+"), 
#                            Item('selected_f',
#                                 label = self.name + "-")))
    
    def _get_str(self):
        if self.selected_t and not self.selected_f:
            return "({0} == True)".format(util.sanitize_identifier(self.name))
        elif not self.selected_t and self.selected_f:
            return "({0} == False)".format(util.sanitize_identifier(self.name))
        else:
            return ""
        
    def __eq__(self, other):
        return (self.name == other.name and
                self.values == other.values and
                self.selected_t == other.selected_t and
                self.selected_f == other.selected_f)
        
    def __hash__(self):
        return hash((self.name, 
                     tuple(self.values), 
                     self.selected_t, 
                     self.selected_f))
            
        
BoolSubset.__repr__ = traits_repr
                
@camel_registry.dumper(BoolSubset, 'bool-subset', 1)
def _dump_bool_subset(bs):
    return dict(name = bs.name,
                values = bs.values,
                selected_t = bs.selected_t,
                selected_f = bs.selected_f)
    
@camel_registry.loader('bool-subset', 1)
def _load_bool_subset(data, version):
    return BoolSubset(**data)

@provides(ISubset)
class CategorySubset(HasStrictTraits):
    name = Str
    values = List
    selected = List
    
    str = Property(Str, depends_on = 'name, selected[]')
    
#     def default_traits_view(self):
#         return View(Item('selected',
#                          label = self.name,
#                          editor = CheckListEditor(name = 'values',
#                                                   cols = 2),
#                          style = 'custom'))
        
    # MAGIC: gets the value of the Property trait "subset_str"
    def _get_str(self):
        if len(self.selected) == 0:
            return ""
        
        phrase = "("
        for cat in self.selected:
            if len(phrase) > 1:
                phrase += " or "
            phrase += "{0} == \"{1}\"".format(util.sanitize_identifier(self.name), cat) 
        phrase += ")"
        
        return phrase
    
        
    def __eq__(self, other):
        return (self.name == other.name and
                self.values == other.values and
                self.selected == other.selected)
        
    def __hash__(self):
        return hash((self.name, 
                     tuple(self.values), 
                     tuple(self.selected)))
    
CategorySubset.__repr__ = traits_repr
    
@camel_registry.dumper(CategorySubset, 'category-subset', 1)
def _dump_category_subset(cs):
    return dict(name = cs.name,
                values = cs.values,
                selected = cs.selected)
    
@camel_registry.loader('category-subset', 1)
def _load_category_subset(data, version):
    return CategorySubset(**data)

@provides(ISubset)
class RangeSubset(HasStrictTraits):
    name = Str
    values = List
    high = CFloat(Undefined)
    low = CFloat(Undefined)
    
    str = Property(Str, depends_on = "name, values, high, low")
    
#     def default_traits_view(self):
#         return View(Item('high',
#                          label = self.name,
#                          editor = ValuesBoundsEditor(
#                                      name = 'values',
#                                      low_name = 'low',
#                                      high_name = 'high',
#                                      format = '%g',
#                                      auto_set = False)))
        
    # MAGIC: gets the value of the Property trait "subset_str"
    def _get_str(self):
        if self.low == self.values[0] and self.high == self.values[-1]:
            return ""
        elif self.low == self.high:
            return "({0} == {1})" \
                   .format(util.sanitize_identifier(self.name), self.low)
        else:
            return "({0} >= {1} and {0} <= {2})" \
                   .format(util.sanitize_identifier(self.name), self.low, self.high) 
        
    @on_trait_change('values, values[]')
    def _values_changed(self):
        if self.high is Undefined:
            self.high = max(self.values)
            
        if self.low is Undefined:
            self.low = min(self.values)
        
        
    def __eq__(self, other):
        return (self.name == other.name and
                self.values == other.values and
                self.low == other.low and
                self.high == other.high)
        
    def __hash__(self):
        return hash((self.name, 
                     tuple(self.values), 
                     self.low, 
                     self.high))
        
RangeSubset.__repr__ = traits_repr
        
@camel_registry.dumper(RangeSubset, 'range-subset', 1)
def _dump_range_subset(rs):
    return dict(name = rs.name,
                values = rs.values,
                high = rs.high,
                low = rs.low)
    
@camel_registry.loader('range-subset', 1)
def _load_range_subset(data, version):
    return RangeSubset(**data)


        
    