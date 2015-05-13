'''
Created on Apr 3, 2015

@author: brian
'''

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasTraits, List, Interface, provides, Float, Property, \
                       Str, Instance, Bool
from traitsui.api import View, Item, CheckListEditor, HGroup, ListEditor, \
                         InstanceEditor
from value_bounds_editor import ValuesBoundsEditor
from cytoflow import Experiment
import numpy as np
import pandas as pd
import FlowCytometryTools as fc

class ISubsetModel(Interface):
    subset_str = Property
    experiment = Instance(Experiment)
    
@provides(ISubsetModel)
class BoolSubsetModel(HasTraits):
    name = Str
    experiment = Instance(Experiment)
    selected_t = Bool(False)
    selected_f = Bool(False)
    subset_str = Property
    
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
    values = Property(depends_on = 'experiment')
    subset_str = Property(depends_on = 'values')
    
    def default_traits_view(self):
        return View(Item('selected',
                         label = self.name,
                         editor = CheckListEditor(
                                     values = self.values,
                                     cols = len(self.values)
                                     )))
    
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
    
    subset_str = Property
    
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
            .format(self.name, self.min, self.max)
    
    # MAGIC: the default value for self.high
    def _high_default(self):
        return self.experiment[self.name].max()
    
    # MAGIC: the default value for self.low
    def _low_default(self):
        return self.experiment[self.name].min()

class SubsetModel(HasTraits):
    
    experiment = Instance(Experiment)
    subset_list = List(ISubsetModel)
    
    subset_str = Property(depends_on = 'subset_list', trait = Str)
      
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
    
    # MAGIC: gets the default value of the trait "subset_list"
    def _subset_list_default(self):
        cond_map = {"bool" : BoolSubsetModel,
                    "category" : CategorySubsetModel,
                    "float" : RangeSubsetModel,
                    "int" : RangeSubsetModel}
        
        ret = []
        for name, dtype in self.experiment.conditions.iteritems():
            ret.append(cond_map[dtype](name = name,
                                       experiment = self.experiment))
        
        return ret 
    
if __name__ == '__main__':
    ex = Experiment()
    ex.add_conditions({"Dox" : "bool"})
    
    tube1 = fc.FCMeasurement(ID='Test 1', 
                       datafile='../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')

    tube2 = fc.FCMeasurement(ID='Test 2', 
                       datafile='../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs')
    
    ex.add_tube(tube1, {"Dox" : True})
    ex.add_tube(tube2, {"Dox" : False})
    
    subset = SubsetModel(experiment = ex)
    subset.configure_traits()
    
