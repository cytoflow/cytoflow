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
    
from traits.api import HasStrictTraits, List, CFloat, Str, Interface, \
                       Property, Bool, provides
from traitsui.api import View, CheckListEditor, Item, HGroup

from cytoflowgui.value_bounds_editor import ValuesBoundsEditor
import cytoflow.utility as util

class ISubset(Interface):
    name = Str
    values = List
    str = Property(Str)
    
@provides(ISubset)
class BoolSubset(HasStrictTraits):
    name = Str
    values = List # unused
    selected_t = Bool(False)
    selected_f = Bool(False)
    
    str = Property(Str, depends_on = "name, selected_t, selected_f")
    
    def default_traits_view(self):
        return View(HGroup(Item('selected_t',
                                label = self.name + "+"), 
                           Item('selected_f',
                                label = self.name + "-")))
        
    # MAGIC: gets the value of the Property trait "str"
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
    str = Property(trait = Str, depends_on = 'name, selected[]')
    
    def default_traits_view(self):
        return View(Item('subset',
                         label = self.name,
                         editor = CheckListEditor(values = self.values,
                                                  cols = 2),
                         style = 'custom'))
        
    # MAGIC: gets the value of the Property trait "str"
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
    
    str = Property(trait = Str, depends_on = "name, low, high")
    
    def default_traits_view(self):
        return View(Item('high',
                         label = self.name,
                         editor = ValuesBoundsEditor(
                                     values = self.values,
                                     low_name = 'low',
                                     high_name = 'high',
                                     auto_set = False)))
    
    def _get_str(self):
        if self.low == self.values[0] and self.high == self.values[-1]:
            return ""
         
        return "({0} >= {1} and {0} <= {2})" \
            .format(util.sanitize_identifier(self.name), self.low, self.high)
          
    
    # MAGIC: the default value for self.high
    def _high_default(self):
        return max(self.values)
    
    # MAGIC: the default value for self.low
    def _low_default(self):
        return min(self.values)
# 
# class SubsetModel(HasStrictTraits):
# 
#     # the conditions we get from the Experiment
#     conditions = Dict(Str, pd.Series)
#     
#     # the metadata from the Experiment
#     metadata = Dict(Str, Any)
#     
#     # a string to evaluate in the `metadata` dict for each condition
#     when = Str
#     
#     # the core of the model
#     condition_models = List(Instance(ICondition))
#     
#     # the actual Dict representation of the subset
#     subset = Property(Dict(Str, List), depends_on = 'condition_models.subset')
#       
#     traits_view = View(Item('condition_models',
#                             style = 'custom',
#                             show_label = False,
#                             editor = ListEditor(editor = InstanceEditor(),
#                                                 style = 'custom',
#                                                 mutable = False)))
#     
#     def include_condition(self, condition):
#         if not self.when:
#             return True
#         
#         if condition in self.metadata:
#             try:
#                 return eval(self.when, globals(), self.metadata[condition])
#             except:
#                 raise util.CytoflowError("Bad when statement: {}"
#                                          .format(self.when))
#         else:
#             return False
#         
#     # MAGIC: gets the value of the Property trait "subset"
#     def _get_subset(self):
#         return {model.name: model.subset for model in self.condition_models}
# 
#     # MAGIC: when the Property trait "subset" is assigned to,
#     # update the view
#     def _set_subset(self, value):
#         for name, subset in value.iteritems():
#             try:
#                 model = next((x for x in self.condition_models if x.name == name))
#             except StopIteration:
#                 print "Thus I die"
#                 continue
#             
#             if set(model.subset) != set(subset):
#                 model.subset = subset
#                 
#     @on_trait_change('conditions', dispatch = 'ui')
#     def _on_conditions_change(self, obj, name, old, new):
#         
#         # to prevent unnecessary updates, be careful about how these are
#         # updated
#         
#         # first, check current models against the new conditions.  remove any
#         # that are no longer present, and update the values for the rest
#         for model in list(self.condition_models):
#             if model.name not in self.conditions or not self.include_condition(model.name):
#                 self.condition_models.remove(model)
#                 continue
#             else:
#                 if set(model.values) != set(self.conditions[model.name]):
#                     model.values = list(self.conditions[model.name])
#                     
#         # then, see if there are any new conditions to add
#         for name, values in self.conditions.iteritems(): 
#             if len([x for x in self.condition_models if x.name == name]) > 0:
#                 continue
#             
#             if not self.include_condition(name):
#                 continue
#             
#             dtype = pd.Series(list(values)).dtype
#             if dtype.kind == 'b':
#                 model = BoolCondition(name = name)
#             elif dtype.kind in "ifu":
#                 model = RangeCondition(name = name,
#                                        values = list(values))
#             elif dtype.kind in "OSU":
#                 model = CategoryCondition(name = name,
#                                           values = list(values))
#             else:
#                 raise util.CytoflowError("Unknown dtype {} in SubsetEditor"
#                                          .format(dtype))
#                 
#             self.condition_models.append(model)
# 
# 
# class _SubsetEditor(Editor):
#     # the model object whose View this Editor displays
#     model = Instance(SubsetModel, args = ())
#     
#     # feed through the synchronized properties to the model
#     conditions = DelegatesTo('model')
#     
#     # feed through the synchronized properties to the model
#     metadata = DelegatesTo('model')
# 
#     # the UI for the Experiment metadata
#     _ui = Instance(UI)
#     
#     def init(self, parent):
#         """
#         Finishes initializing the editor and make the toolkit control
#         """
#         
#         if self.factory.metadata:
#             self.sync_value(self.factory.metadata, 'metadata', 'from')
#             
#         self.model.when = self.factory.when
# 
#         self.sync_value(self.factory.conditions, 'conditions', 'from')
# 
#         # now start listening for changed values
#         self.model.on_trait_change(self.update_value, "subset")
#               
#         self._ui = self.model.edit_traits(kind = 'subpanel', parent = parent)
#         self.control = self._ui.control
#         
#     def dispose(self):
#         
#         # disconnect the dynamic notifiers
#         
#         self.model.on_trait_change(self.update_value, "subset", remove = True)
#         
#         if self._ui:
#             self._ui.dispose()
#             self._ui = None
#             
#     def update_editor(self):
#         logging.debug("subset_editor: Setting editor to {}".format(self.value))
#         self.model.subset = self.value
#     
#     def update_value(self, new):
#         logging.debug("subset_editor: Setting value to {}".format(new))
#         self.value = new            
# 
# class SubsetEditor(BasicEditorFactory):
#     # the editor to be created
#     klass = _SubsetEditor
#     
#     # the name of the trait containing the names --> values dict
#     conditions = Str
#     
#     # the name of the trait containing the metadata dict
#     metadata = Str
#     
#     # a string to evaluate on the metadata to see if we include this condition
#     # in the editor
#     when = Str
# 
#     