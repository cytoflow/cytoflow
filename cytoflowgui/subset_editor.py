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

import logging

# for local debugging
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"
    
import pandas as pd

from traits.api import Instance, HasStrictTraits, List, CFloat, Str, Dict, Interface, \
                       Property, Bool, provides, DelegatesTo, on_trait_change, Any
from traitsui.api import BasicEditorFactory, View, UI, \
                         CheckListEditor, Item, HGroup, ListEditor, InstanceEditor
from traitsui.qt4.editor import Editor

from cytoflowgui.value_bounds_editor import ValuesBoundsEditor
import cytoflow.utility as util

class IConditionModel(Interface):
    name = Str
    values = List
    subset = Property(List)
    
@provides(IConditionModel)
class BoolCondition(HasStrictTraits):
    name = Str
    values = List  # unused
    selected_t = Bool(False)
    selected_f = Bool(False)
    
    subset = Property(List, depends_on = "selected_t, selected_f")
    
    def default_traits_view(self):
        return View(HGroup(Item('selected_t',
                                label = self.name + "+"), 
                           Item('selected_f',
                                label = self.name + "-")))
    
    # MAGIC: gets the value of the Property trait "subset"
    def _get_subset(self):
        ret = []
        if self.selected_t:
            ret += [True]
        if self.selected_f:
            ret += [False]
            
        return ret
    
    def _set_subset(self, val):
        if True in val:
            self.selected_t = True
        if False in val:
            self.selected_f = True

@provides(IConditionModel)
class CategoryCondition(HasStrictTraits):
    name = Str
    values = List
    subset = List
    
    def default_traits_view(self):
        return View(Item('subset',
                         label = self.name,
                         editor = CheckListEditor(values = self.values,
                                                  cols = 2),
                         style = 'custom'))

@provides(IConditionModel)
class RangeCondition(HasStrictTraits):
    name = Str
    values = List
    high = CFloat
    low = CFloat
    
    subset = Property(List, depends_on = "values, high, low")
    
    def default_traits_view(self):
        return View(Item('high',
                         label = self.name,
                         editor = ValuesBoundsEditor(
                                     values = self.values,
                                     low_name = 'low',
                                     high_name = 'high',
                                     auto_set = False)))
    
    # MAGIC: gets the value of the Property trait "subset_str"
    def _get_subset(self):
        if self.low == self.values[0] and self.high == self.values[-1]:
            return []
        
        return [x for x in self.values if x >= self.low and x <= self.high]
            
    # MAGIC: when the Property trait "subset_str" is set, update the editor.
    def _set_subset(self, val):
        if not val:
            self.low = self._low_default()
            self.high = self._high_default()
            return
        
        self.low = min(val)
        self.high = min(val)
    
    # MAGIC: the default value for self.high
    def _high_default(self):
        return max(self.values)
    
    # MAGIC: the default value for self.low
    def _low_default(self):
        return min(self.values)

class SubsetModel(HasStrictTraits):

    # the conditions we get from the Experiment
    conditions = Dict(Str, pd.Series)
    
    # the core of the model
    condition_models = List(Instance(IConditionModel))
    
    # the actual Dict representation of the subset
    subset = Property(Dict(Str, List), depends_on = 'condition_models.subset')
      
    traits_view = View(Item('condition_models',
                            style = 'custom',
                            show_label = False,
                            editor = ListEditor(editor = InstanceEditor(),
                                                style = 'custom',
                                                mutable = False)))
        
    # MAGIC: gets the value of the Property trait "subset"
    def _get_subset(self):
        return {model.name: model.subset for model in self.condition_models}

    # MAGIC: when the Property trait "subset" is assigned to,
    # update the view
    def _set_subset(self, value):
        for name, subset in value.iteritems():
            model = next((x for x in self.condition_models if x.name == name))
            if set(model.subset) != set(subset):
                model.subset = subset
#         for model in self.condition_models:
#             value_subset = value[model.name]
#             if set(model.subset) != set(value_subset):
#                 model.subset = value_subset
                
    @on_trait_change('conditions', dispatch = 'ui')
    def _on_conditions_change(self, obj, name, old, new):
        
        # to prevent unnecessary updates, be careful about how these are
        # updated
        
        # first, check current models against the new conditions.  remove any
        # that are no longer present, and update the values for the rest
        for model in list(self.condition_models):
            if model.name not in self.conditions:
                self.condition_models.remove(model)
                continue
            else:
                if set(model.values) != set(self.conditions[model.name]):
                    model.values = list(self.conditions[model.name])
                    
        # then, see if there are any new conditions to add
        for name, values in self.conditions.iteritems(): 
            if len([x for x in self.condition_models if x.name == name]) > 0:
                continue
            
            dtype = pd.Series(list(values)).dtype
            if dtype.kind == 'b':
                model = BoolCondition(name = name)
            elif dtype.kind in "ifu":
                model = RangeCondition(name = name,
                                       values = list(values))
            elif dtype.kind in "OSU":
                model = CategoryCondition(name = name,
                                          values = list(values))
            else:
                raise util.CytoflowError("Unknown dtype {} in SubsetEditor"
                                         .format(dtype))
                
            self.condition_models.append(model)


class _SubsetEditor(Editor):
    # the model object whose View this Editor displays
    model = Instance(SubsetModel, args = ())
    
    # feed through the synchronized properties to the model
    conditions = DelegatesTo('model')
    
    # the UI for the Experiment metadata
    _ui = Instance(UI)
    
    def init(self, parent):
        """
        Finishes initializing the editor and make the toolkit control
        """

        self.sync_value(self.factory.conditions, 'conditions', 'from')
                
        # now start listening for changed values
        self.model.on_trait_change(self.update_value, "subset")
              
        self._ui = self.model.edit_traits(kind = 'subpanel', parent = parent)
        self.control = self._ui.control
        
    def dispose(self):
        
        # disconnect the dynamic notifiers
        
        self.model.on_trait_change(self.update_value, "subset", remove = True)
        
        if self._ui:
            self._ui.dispose()
            self._ui = None
            
    def update_editor(self):
        logging.debug("subset_editor: Setting editor to {}".format(self.value))
        self.model.subset = self.value
    
    def update_value(self, new):
        logging.debug("subset_editor: Setting value to {}".format(new))
        self.value = new            

class SubsetEditor(BasicEditorFactory):
    # the editor to be created
    klass = _SubsetEditor
    
    # the name of the trait containing the names --> values dict
    conditions = Str

    