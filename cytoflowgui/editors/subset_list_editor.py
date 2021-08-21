#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
cytoflowgui.editors.subset_list_editor
--------------------------------------

"""

import pandas as pd

from traits.api import Dict, Str, Bool, Any, Trait, on_trait_change
from traits.trait_handlers import TraitPrefixList

import cytoflow.utility as util

from cytoflowgui.workflow.subset import BoolSubset, RangeSubset, CategorySubset

from .vertical_list_editor import _VerticalListEditor, VerticalListEditor

class _SubsetListEditor(_VerticalListEditor):

    conditions = Dict(Str, pd.Series)
    metadata = Dict(Str, Any)
    when = Str
    scrollable = False

    def init(self, parent):
        
        if self.factory.metadata:
            self.sync_value(self.factory.metadata, 'metadata', 'from', is_list = True)
             
        self.when = self.factory.when
        
        self.sync_value(self.factory.conditions, 'conditions', 'from', is_list = True)
        
        _VerticalListEditor.init(self, parent)
        
    @on_trait_change('conditions, metadata', dispatch = 'ui')
    def _on_conditions_change(self, obj, name, old, new):
        value_names = set([subset.name for subset in self.value])
        condition_names = set([x for x in list(self.conditions.keys()) if self.include_condition(x)])
        
        loading = (self.ui.context["context"].status == "loading")
        
        if not loading:
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
                                        values = sorted(list(values)))
            else:
                raise util.CytoflowError("Unknown dtype {} in ViewController"
                                         .format(dtype))
             
            self.value.append(subset)
        
        for name in condition_names & value_names:
            # update values for subsets we're already tracking
            subset = next((x for x in self.value if x.name == name))
            if set(subset.values) != set(self.conditions[name]):
                subset.values = list(self.conditions[name].sort_values())
                
        self.value = sorted(self.value, key = lambda x: x.name)
                
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

