#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

'''
Created on Mar 23, 2015

@author: brian
'''

# for local debugging
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"
    
import pandas as pd

from traits.api import (HasStrictTraits, List, CFloat, Str, Dict, Interface, 
                        Property, Bool, provides, on_trait_change, Any, Trait,
                        TraitPrefixList)
from traitsui.api import View, CheckListEditor, Item, HGroup

from cytoflowgui.value_bounds_editor import ValuesBoundsEditor
from cytoflowgui.vertical_list_editor import VerticalListEditor, _VerticalListEditor
import cytoflow.utility as util

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
    
    def default_traits_view(self):
        return View(HGroup(Item('selected_t',
                                label = self.name + "+"), 
                           Item('selected_f',
                                label = self.name + "-")))
    
    def _get_str(self):
        if self.selected_t and not self.selected_f:
            return "({0} == True)".format(util.sanitize_identifier(self.name))
        elif not self.selected_t and self.selected_f:
            return "({0} == False)".format(util.sanitize_identifier(self.name))
        else:
            return ""

@provides(ISubset)
class CategorySubset(HasStrictTraits):
    name = Str
    values = List
    selected = List
    
    str = Property(Str, depends_on = 'name, selected[]')
    
    def default_traits_view(self):
        return View(Item('selected',
                         label = self.name,
                         editor = CheckListEditor(values = self.values,
                                                  cols = 2),
                         style = 'custom'))
        
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

@provides(ISubset)
class RangeSubset(HasStrictTraits):
    name = Str
    values = List
    high = CFloat
    low = CFloat
    
    str = Property(Str, depends_on = "name, values, high, low")
    
    def default_traits_view(self):
        return View(Item('high',
                         label = self.name,
                         editor = ValuesBoundsEditor(
                                     values = self.values,
                                     low_name = 'low',
                                     high_name = 'high',
                                     auto_set = False)))
        
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
    
    # MAGIC: the default value for self.high
    def _high_default(self):
        if self.values:
            return max(self.values)
        else:
            return 0
    
    # MAGIC: the default value for self.low
    def _low_default(self):
        if self.values:
            return min(self.values)
        else:
            return 0    

class _SubsetListEditor(_VerticalListEditor):

    conditions = Dict(Str, pd.Series)
    metadata = Dict(Str, Any)
    when = Str
    scrollable = False

    def init(self, parent):
        
        if self.factory.metadata:
            self.sync_value(self.factory.metadata, 'metadata', 'from')
             
        self.when = self.factory.when
        
        self.sync_value(self.factory.conditions, 'conditions', 'from')
        
        _VerticalListEditor.init(self, parent)
        
    @on_trait_change('conditions', dispatch = 'ui')
    def _on_conditions_change(self, obj, name, old, new):
        value_names = set([subset.name for subset in self.value])
        condition_names = set([x for x in self.conditions.keys() if self.include_condition(x)])
        
        for name in value_names - condition_names:
            # remove subsets that aren't in conditions
            subset = next((x for x in self.value if x.name == name))
            self.value.remove(subset)
            
        for name in condition_names - value_names:
            # add subsets that are new conditions
            values = self.conditions[name].sort_values()
            dtype = pd.Series(list(values)).dtype
            if dtype.kind == 'b':
                subset = BoolSubset(name = name)
            elif dtype.kind in "ifu":
                subset = RangeSubset(name = name,
                                     values = list(values))
            elif dtype.kind in "OSU":
                subset = CategorySubset(name = name,
                                        values = list(values))
            else:
                raise util.CytoflowError("Unknown dtype {} in ViewController"
                                         .format(dtype))
             
            self.value.append(subset)    
        
        for name in condition_names & value_names:
            # update values for subsets we're already tracking
            subset = next((x for x in self.value if x.name == name))
            if set(subset.values) != set(self.conditions[name]):
                subset.values = list(self.conditions[name].sort_values())
                
    def include_condition(self, condition):
        if not self.when:
            return True
         
        if condition in self.metadata:
            try:
                return eval(self.when, globals(), self.metadata[condition])
            except:
                raise util.CytoflowError("Bad when statement: {}"
                                         .format(self.when))
        else:
            return False


class SubsetListEditor(VerticalListEditor):    
    # the name of the trait containing the names --> values dict
    conditions = Str
    
    # the name of the trait containing the metadata dict
    metadata = Str
    
    # a string to evaluate on the metadata to see if we include this condition
    # in the editor
    when = Str
    
    # override some defaults
    style = Trait("custom", TraitPrefixList('simple', 'custom', 'text', 'readonly'))
    mutable = Bool(False)
    
    # use the custom editor above, which extends the qt4.ListEditor class
    def _get_simple_editor_class(self):
        return _SubsetListEditor

    