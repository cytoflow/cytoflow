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

import logging, re

# for local debugging
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import Instance, HasStrictTraits, List, CFloat, Str, Dict, Interface, \
                       Property, Bool, provides, on_trait_change, DelegatesTo, Any
from traitsui.api import BasicEditorFactory, View, UI, \
                         CheckListEditor, Item, HGroup, ListEditor, InstanceEditor
from traitsui.qt4.editor import Editor

from cytoflow.utility import sanitize_identifier
from cytoflowgui.value_bounds_editor import ValuesBoundsEditor

class ICondition(Interface):
    name = Str
    values = List
    subset_str = Property
    
@provides(ICondition)
class BoolCondition(HasStrictTraits):
    name = Str
    values = List  # unused
    selected_t = Bool(False)
    selected_f = Bool(False)
    subset_str = Property(trait = Str,
                          depends_on = "name, selected_t, selected_f")
    
    def default_traits_view(self):
        return View(HGroup(Item('selected_t',
                                label = self.name + "+"), 
                           Item('selected_f',
                                label = self.name + "-")))
    
    # MAGIC: gets the value of the Property trait "subset_str"
    def _get_subset_str(self):
        if self.selected_t and not self.selected_f:
            return "({0} == True)".format(sanitize_identifier(self.name))
        elif not self.selected_t and self.selected_f:
            return "({0} == False)".format(sanitize_identifier(self.name))
        else:
            return ""
    
    def _set_subset_str(self, val):
        """Update the view based on a subset string"""
        if val == "({0} == True)".format(sanitize_identifier(self.name)):
            self.selected_t = True
            self.selected_f = False
        elif val == "({0} == False)".format(sanitize_identifier(self.name)):
            self.selected_t = False
            self.selected_f = True
        else:
            self.selected_t = False
            self.selected_f = False

@provides(ICondition)
class CategoryCondition(HasStrictTraits):
    name = Str
    values = List
    selected = List
    subset_str = Property(trait = Str,
                          depends_on = 'name, selected[]')
    
    def default_traits_view(self):
        return View(Item('selected',
                         label = self.name,
                         editor = CheckListEditor(values = self.values,
                                                  cols = 2),
                         style = 'custom'))

    # MAGIC: gets the value of the Property trait "subset_str"
    def _get_subset_str(self):
        if len(self.selected) == 0:
            return ""
        
        phrase = "("
        for cat in self.selected:
            if len(phrase) > 1:
                phrase += " or "
            phrase += "{0} == \"{1}\"".format(sanitize_identifier(self.name), cat) 
        phrase += ")"
        
        return phrase
    
    def _set_subset_str(self, val):
        if not val:
            self.selected = []
            return
        
        if val.startswith("("):
            val = val[1:]
        if val.endswith(")"):
            val = val[:-1]
            
        selected = []
        for s in val.split(" or "):
            cat = re.search(" == \"(\w+)\"$", s).group(1)
            selected.append(cat)
            
        self.selected = selected

@provides(ICondition)
class RangeCondition(HasStrictTraits):
    name = Str
    values = List
    high = CFloat
    low = CFloat
    
    subset_str = Property(trait = Str,
                          depends_on = "name, low, high")
    
    def default_traits_view(self):
        return View(Item('high',
                         label = self.name,
                         editor = ValuesBoundsEditor(
                                     values = self.values,
                                     low_name = 'low',
                                     high_name = 'high',
                                     auto_set = False)))
    
    # MAGIC: gets the value of the Property trait "subset_str"
    def _get_subset_str(self):
        if self.low == self.values[0] and self.high == self.values[-1]:
            return ""
         
        return "({0} >= {1} and {0} <= {2})" \
            .format(sanitize_identifier(self.name), self.low, self.high)
            
    # MAGIC: when the Property trait "subset_str" is set, update the editor.
    def _set_subset_str(self, val):
        # because low and high are CFloats, we can just assign the string
        # and they'll get "C"onverted
        if not val:
            self.low = self._low_default()
            self.high = self._high_default()
            return
        
        self.low = re.search(r">= ([0-9.]+)", val).group(1)
        self.high = re.search(r"<= ([0-9.]+)", val).group(1)
    
    # MAGIC: the default value for self.high
    def _high_default(self):
        return max(self.values)
    
    # MAGIC: the default value for self.low
    def _low_default(self):
        return min(self.values)

class SubsetModel(HasStrictTraits):

    # the core of the model; the traits view is a bunch of
    # InstanceEditors for this list.
    conditions = List(ICondition)
    
    # maps a condition name to an ICondition instance
    conditions_map = Dict(Str, Instance(ICondition))
    
    # the pieces needed to set up the editors
    conditions_types = Dict(Str, Str)
    conditions_values = Dict(Str, List(Any))
    
    # the actual string representation of this model: something you
    # can feed to pandas.DataFrame.subset()    
    subset_str = Property(trait = Str,
                          depends_on = "conditions.subset_str")
      
    traits_view = View(Item('conditions',
                            style = 'custom',
                            show_label = False,
                            editor = ListEditor(editor = InstanceEditor(),
                                                style = 'custom',
                                                mutable = False)))
        
    # MAGIC: gets the value of the Property trait "subset_string"
    def _get_subset_str(self):
        subset_strings = [c.subset_str for c in self.conditions]
        subset_strings = filter(lambda x: x, subset_strings)
        return " and ".join(subset_strings)

    # MAGIC: when the Property trait "subset_string" is assigned to,
    # update the view
    def _set_subset_str(self, value):
        # reset everything
        for condition in self.conditions:
            condition.subset_str = ""
            
        # abort if there's nothing to parse
        if not value:
            return
        
        # this parser is ugly and brittle.  TODO - replace me with
        # something from pyparsing.  ie, see
        # http://pyparsing.wikispaces.com/file/view/simpleBool.py
        
        print "set overall subset str ''{0}''".format(value)
        
        phrases = value.split(r") and (")
        if phrases[0] == "":  # only had one phrase, not a conjunction
            phrases = [value]
            
        for phrase in phrases:
            if not phrase.startswith("("):
                phrase = "(" + phrase
            if not phrase.endswith(")"):
                phrase = phrase + ")"
            name = re.match(r"\((\w+) ", phrase).group(1)
            
            # update the subset editor ui
            self.conditions_map[name].subset_str = phrase
            
            
    def _on_types_change(self, obj, name, old, new):
        model_map = {"bool" : BoolCondition,
                    "category" : CategoryCondition,
                    "float" : RangeCondition,
                    "int" : RangeCondition}
         
        for name, dtype in self.conditions_types.iteritems(): 
            if name in self.conditions_values:            
                condition = model_map[dtype](name = name, 
                                             values = self.conditions_values[name])
                
                self.conditions.append(condition)
                self.conditions_map[name] = condition
        
    
    def _on_values_change(self, obj, name, old, new):        
        model_map = {"bool" : BoolCondition,
                    "category" : CategoryCondition,
                    "float" : RangeCondition,
                    "int" : RangeCondition}
        
        for name, values in self.conditions_values.iteritems():
            if name in self.conditions_map:
                self.conditions_map[name].values = values
            elif name in self.conditions_types:
                dtype = self.conditions_types[name]
                condition = model_map[dtype](name = name, 
                                             values = self.conditions_values[name])
                 
                self.conditions.append(condition)
                self.conditions_map[name] = condition


class _SubsetEditor(Editor):
    # the model object whose View this Editor displays
    model = Instance(SubsetModel, args = ())
    
    # feed through the synchronized properties to the model
    conditions_types = DelegatesTo('model')
    conditions_values = DelegatesTo('model')
    
    # the UI for the Experiment metadata
    _ui = Instance(UI)
    
    def init(self, parent):
        """
        Finishes initializing the editor and make the toolkit control
        """
    
        # usually, we'd make these static notifiers.  however, in this case we
        # have to set a dynamic notifier because this is changed by the 
        # receiving thread in LocalWorkflow, and we need to re-dispatch
        # to the ui thread.
        
        # TODO - when the next version of Traits is released, change this
        # to a static decorator with a 'dispatch' arg (it's already been fixed 
        # on Github)
        self.model.on_trait_change(self.model._on_types_change, "conditions_types", 
                                   dispatch = 'ui')
          
        self.model.on_trait_change(self.model._on_values_change, "conditions_values", 
                             dispatch = 'ui')

        self.sync_value(self.factory.conditions_types, 'conditions_types', 'from')
        self.sync_value(self.factory.conditions_values, 'conditions_values', 'from')
                
        # now start listening for changed values
        self.model.on_trait_change(self.update_value, "subset_str")
              
        self._ui = self.model.edit_traits(kind = 'subpanel',
                                          parent = parent)
        self.control = self._ui.control
        
    def dispose(self):
        
        # disconnect the dynamic notifiers
        
        self.model.on_trait_change(self.update_value, "subset_str", remove = True)

        self.model.on_trait_change(self.model._on_types_change, "conditions_types", 
                                   dispatch = 'ui', remove = True)
          
        self.model.on_trait_change(self.model._on_values_change, "conditions_values", 
                             dispatch = 'ui', remove = True)
        
        if self._ui:
            self._ui.dispose()
            self._ui = None
            
    def update_editor(self):
        logging.debug("subset_editor: Setting editor to {}".format(self.value))
        self.model.subset_str = self.value
    
    def update_value(self, new):
        logging.debug("subset_editor: Setting value to {}".format(new))
        self.value = new            

class SubsetEditor(BasicEditorFactory):
    # the editor to be created
    klass = _SubsetEditor
    
    # the name of the trait containing the names --> types dict
    conditions_types = Str
    
    # the name of the trait containing the names --> values dict
    conditions_values = Str
    