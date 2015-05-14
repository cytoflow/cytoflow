'''
Created on Mar 23, 2015

@author: brian
'''
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traitsui.api import BasicEditorFactory, View, UI, \
                         CheckListEditor, Item, HGroup, ListEditor, InstanceEditor
from traitsui.qt4.editor import Editor
from traits.api import Instance, HasTraits, List, Float, Int, Str, Dict, \
                       Interface, Property, Bool, provides, on_trait_change, DelegatesTo
from cytoflow import Experiment
from value_bounds_editor import ValuesBoundsEditor
import pandas as pd
import numpy as np

class ISubsetModel(Interface):
    name = Str
    subset_str = Property
    experiment = Instance(Experiment)
    
@provides(ISubsetModel)
class BoolSubsetModel(HasTraits):
    name = Str
    experiment = Instance(Experiment)
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
            return "{0} == True".format(self.name)
        elif not self.selected_t and self.selected_f:
            return "{0} == False".format(self.name)
        else:
            return ""
    
    def _set_subset_str(self, val):
        """Update the view based on a subset string"""
        if val == "{0} == True".format(self.name):
            self.selected_t = True
            self.selected_f = False
        elif val == "{0} == False".format(self.name):
            self.selected_t = False
            self.selected_f = True

@provides(ISubsetModel)
class CategorySubsetModel(HasTraits):
    name = Str
    experiment = Instance(Experiment)
    selected = List
    values = Property(trait = List,
                      depends_on = 'experiment')
    subset_str = Property(trait = Str,
                          depends_on = 'name, values')
    
    def default_traits_view(self):
        return View(Item('selected',
                         label = self.name,
                         editor = CheckListEditor(values = self.values,
                                                  cols = len(self.values))))
    
    # MAGIC: gets the value of the Property trait "values"
    def _get_values(self):
        return list(self.experiment[self.name].cat.categories)

    # MAGIC: gets the value of the Property trait "subset_str"
    def _get_subset_str(self):
        phrase = "("
        for cat in self.values:
            if len(phrase) > 1:
                phrase += " or "
            phrase += "{0} == {1}".format(self.name, cat) 
        phrase += ")"
        
        return phrase

@provides(ISubsetModel)
class RangeSubsetModel(HasTraits):
    name = Str
    experiment = Instance(Experiment)
    values = Property(depends_on = 'experiment')
    high = Float
    low = Float
    
    subset_str = Property(trait = Str,
                          depends_on = "name, low, high")
    
    def default_traits_view(self):
        return View(Item('high',
                         label = self.name,
                         editor = ValuesBoundsEditor(
                                     values = self.values,
                                     low_name = 'low',
                                     high_name = 'high')))
    
    # MAGIC: gets the value of the Property trait "values"
    def _get_values(self):
        return list(np.sort(pd.unique(self.experiment[self.name])))
    
    # MAGIC: gets the value of the Property trait "subset_str"
    def _get_subset_str(self):
        return "({0} >= {1} and {0} <= {2})" \
            .format(self.name, self.low, self.high)
    
    # MAGIC: the default value for self.high
    def _high_default(self):
        return self.experiment[self.name].max()
    
    # MAGIC: the default value for self.low
    def _low_default(self):
        return self.experiment[self.name].min()

class SubsetModel(HasTraits):
    experiment = Instance(Experiment)
    subset_list = List(ISubsetModel)
    
    subset_str = Property(trait = Str,
                          depends_on = "subset_list.subset_str")
      
    traits_view = View(Item('subset_list',
                            style = 'custom',
                            show_label = False,
                            editor = ListEditor(editor = InstanceEditor(),
                                                style = 'custom',
                                                mutable = False)))

    # MAGIC: gets the value of the Property trait "subset_string"
    def _get_subset_str(self):
        return " and ".join([s.subset_str for s in self.subset_list])

    # MAGIC: when the Property trait "subset_string" is assigned to,
    # update the view    
    def _set_subset_str(self, value):
        print "TODO - set editor to {0}".format(value)
        
    @on_trait_change('experiment')
    def _on_experiment_change(self):
        print "experiment changed"
        cond_map = {"bool" : BoolSubsetModel,
                    "category" : CategorySubsetModel,
                    "float" : RangeSubsetModel,
                    "int" : RangeSubsetModel}
        
        subset_list = []
        for name, dtype in self.experiment.conditions.iteritems():
            subset_list.append(cond_map[dtype](name = name,
                                               experiment = self.experiment))        
        self.subset_list = subset_list

class _SubsetEditor(Editor):
    
    # the cytoflow.Experiment construct the UI
    #experiment = Instance(Experiment)
    
    # the model object whose traits view we'll display
    model = Instance(SubsetModel, args = ())
    
    experiment = DelegatesTo('model')
    
    # the UI for the Experiment metadata
    _ui = Instance(UI)
     
#     # the object we create to represent the Experiment conditions.
#     # make a default instance
#     _obj = Instance(HasTraits)
#     
#     # the parent layout.  we need to keep this around to update dynamically
#     _layout = Instance(QtGui.QVBoxLayout)
    
    def init(self, parent):
        """
        Finishes initializing the editor and make the toolkit control
        """

        self.model = SubsetModel()
        self.sync_value(self.factory.experiment, 'experiment', 'from')
        #self.on_trait_change(self.update_experiment, 'experiment', dispatch = 'ui')
        
        #self.sync_value(self.model.subset_str, 'value', 'both')
        #self.factory.sync_value(self.model.experiment, 'experiment', 'both')
        
        self._ui = self.model.edit_traits(kind = 'subpanel',
                                          parent = parent)
        self.control = self._ui.control
        
#         assert(isinstance(parent, QtGui.QLayout))
#         self._layout = QtGui.QVBoxLayout()
#         
#         self.control = QtGui.QWidget()
#         self.control.setLayout(self._layout)
#   
#         obj, group = self._make_view()
#         self._obj = obj
#         self._obj.on_trait_change(self._view_changed)
#         self._ui = self._obj.edit_traits(kind = 'subpanel',
#                                          parent = self._parent,
#                                          view = View(group))
#         self._layout.addWidget(self._ui.control)
        
    def dispose(self):
        if self._ui:
            self._ui.dispose()
            self._ui = None
            
    def update_editor(self):
        print "update editor with value: {0}".format(self.value)
        self.model.subset_str = self.value
    
    @on_trait_change('model.subset_str')
    def update_value(self, new):
        print "updating value from editor: {0}".format(new)
        self.value = new
    
#     def update_editor(self):
#         print "TODO - update editor with value: {0}".format(self.value)
#         pass  #for the moment
#             
# #         if self._obj:
# #             self._obj.on_trait_change(self._view_changed, remove = True)
# #             
#         super(_SubsetEditor, self).dispose()

#     def update_experiment(self):
#         
#         print "updating subset experiment"
#         
#         self._layout.parentWidget().setUpdatesEnabled(False)
#         
#         if self._ui:
#             #idx = self._layout.indexOf(self._ui.control)
#             #print "layout idx: {0}".format(idx)
#             self._layout.takeAt(self._layout.indexOf(self._ui.control))
#             self._ui.dispose()
#             self._ui = None
#         
#         if self._obj:
#             self._obj.on_trait_change(self._view_changed, remove = True)
#         
#         obj, group = self._make_view()
#         
#         self._obj = obj
#         self._obj.on_trait_change(self._view_changed)
#         self._ui = self._obj.edit_traits(kind = 'subpanel',
#                                          parent = self._parent,
#                                          view = View(group))
#         self.control = self._ui.control
#         self._layout.addWidget(self.control) 
#         
#         self._layout.parentWidget().setUpdatesEnabled(True)
#     
#     def _make_view(self):
#         
#         obj = HasTraits()   # the underlying object whose traits we're viewing
#         group = Group()     # the TraitsUI Group with the editors in it
# 
#         if not self.experiment:
#             return obj, group
# 
#         for name, dtype in self.experiment.conditions.iteritems():
#             if dtype == 'bool':
#                 values = [name + '-', name + '+']
#                 obj.add_trait(name, List(editor = CheckListEditor(
#                                                     values = values,
#                                                     cols = 2)))
#                 group.content.append(Item(name, 
#                                           style = 'custom'))
#                    
#             elif dtype == 'category':
#                 values = list(self.experiment[name].cat.categories)
#                 obj.add_trait(name, List(editor = CheckListEditor(
#                                                     values = values,
#                                                     cols = len(values))))
#                 group.content.append(Item(name, 
#                                           style = 'custom'))
#                    
#             elif dtype == 'float':
#                 values = list(np.sort(pd.unique(self.experiment[name])))
#                 obj.add_trait(name + "Min", Float(self.experiment[name].min()))
#                 obj.add_trait(name + "Max", 
#                               Float(default_value = self.experiment[name].max(),
#                                     editor = ValuesBoundsEditor( 
#                                                 values = values,
#                                                 low_name = name + "Min",
#                                                 high_name = name + "Max"))
#                             )
#                 group.content.append(Item(name + "Max", 
#                                           label = name, 
#                                           style = 'custom'))
#                    
#             elif dtype == 'int':
#                 values = list(np.sort(pd.unique(self.experiment[name])))
#                 obj.add_trait(name + "Min", Int(self.experiment[name].min()))
#                 obj.add_trait(name + "Max", 
#                               Int(default_value = self.experiment[name].max(),
#                                   editor = ValuesBoundsEditor(
#                                                 values = values,
#                                                 low_name = name + "Min",
#                                                 high_name = name + "Max"))
#                             )
#                    
#                 group.content.append(Item(name + "Max", 
#                                           label = name, 
#                                           style = 'custom'))
#                 
#         return obj, group
#  
# 
#          
# 
#     
#     def _view_changed(self, name, new, old):
#         
#         # we want to spit out a value in a standard form so we can easily
#         # parse it back in.
#         
#         subsets = []
#         
#         for name, dtype in self.experiment.conditions.iteritems(): 
#             if dtype == 'bool':
#                 val = self._obj.trait_get(name)[name]
#                 if name + '+' in val and not name + '-' in val:
#                     subsets.append("({0} == True)".format(name))
#                 elif name + '+' not in val and name + '-' in val:
#                     subsets.append("({0} == False)".format(name))
#                 else:
#                     # "name" is any value; dont' include specifier
#                     pass
#                 
#             elif dtype == 'category':
#                 val = self._obj.trait_get(name)[name]
#                 phrase = "("
#                 for cat in val:
#                     if len(phrase) > 1:
#                         phrase += " or "
#                     phrase += "{0} == {1}".format(name, cat) 
#                 phrase += ")"
#                 
#             elif dtype == 'float':
#                 min_val = self._obj.trait_get(name + "Min")[name + "Min"]
#                 max_val= self._obj.trait_get(name + "Max")[name + "Max"]
#                 subsets.append("({0} >= {1} and {0} <= {2})"
#                                .format(name, min_val, max_val))
#                 
#             elif dtype == 'int':
#                 min_val = self._obj.trait_get(name + "Min")[name + "Min"]
#                 max_val = self._obj.trait_get(name + "Max")[name + "Max"]
#                 subsets.append("({0} >= {1} and {0} <= {2})"
#                                .format(name, min_val, max_val))
#                 
#             self.value = " and ".join(subsets)
#             print self.value                

class SubsetEditor(BasicEditorFactory):
    
    # the editor to be created
    klass = _SubsetEditor
    
    # the name of the trait containing the cytoflow.Experiment to build the UI
    experiment = Str
    
    
if __name__ == '__main__':
    
    import FlowCytometryTools as fc
    
    ex = Experiment()
    ex.add_conditions({"Dox" : "bool"})
    
    tube1 = fc.FCMeasurement(ID='Test 1', 
                       datafile='../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')

    tube2 = fc.FCMeasurement(ID='Test 2', 
                       datafile='../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs')
    
    ex.add_tube(tube1, {"Dox" : True})
    ex.add_tube(tube2, {"Dox" : False})
    
    class C(HasTraits):
        val = Str()
        experiment = Instance(Experiment)

    c = C(experiment = ex)
    
    c.configure_traits(view=View(Item('val',
                                      editor = SubsetEditor(experiment = 'experiment'))))
    
    
    
    