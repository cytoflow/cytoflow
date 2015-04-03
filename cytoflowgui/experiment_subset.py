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
from traitsui.api import View, Group, Item, CheckListEditor, HGroup, \
                         ListEditor, InstanceEditor
from value_bounds_editor import ValuesBoundsEditor
from cytoflow import Experiment
import numpy as np
import pandas as pd
import FlowCytometryTools as fc

class ISubset(Interface):
    subset_str = Property
    
@provides(ISubset)
class BoolSubset(HasTraits):
    name = Str
    experiment = Instance(Experiment)
    selected_t = Bool(False)
    selected_f = Bool(False)
    subset_str = Property
    
    def default_traits_view(self):
        return View(HGroup(Item('selected_t'), Item('selected_f')))
    
    # MAGIC: gets the value of the Property trait "subset_str"
    def _get_subset_str(self):
        if self.selected_t and not self.selected_f:
            return "{0} == True".format(self.name)
        elif not self.selected_t and self.selected_f:
            return "{0} == False".format(self.name)
        else:
            return ""

@provides(ISubset)
class CategorySubset(HasTraits):
    name = Str
    experiment = Instance(Experiment)
    selected = List
    values = Property(depends_on = 'experiment')
    subset_str = Property(depends_on = 'values')
    
    def default_traits_view(self):
        return View(Item('selected',
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

@provides(ISubset)
class RangeSubset(HasTraits):
    name = Str
    experiment = Instance(Experiment)
    values = Property(depends_on = 'experiment')
    high = Float
    low = Float
    
    subset_str = Property
    
    def default_traits_view(self):
        return View(Item('high',
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

class ExperimentSubset(HasTraits):
    
    experiment = Instance(Experiment)
    
    subset_list = List(ISubset)
    
    subset_string = Property(depends_on = 'subset_list', trait = Str)
      
    traits_view = View(Item('subset_list',
                             style = 'custom',
                             editor = ListEditor(editor = InstanceEditor(),
                                                 style = 'custom')))

    # MAGIC: gets the value of the Property trait "subset_string"
    def _get_subset_string(self):
        return " and ".join([s.subset_str for s in self.subset_list])
    
    # MAGIC: gets the default value of the trait "subset_list"
    def _subset_list_default(self):
        cond_map = {"bool" : BoolSubset,
                    "category" : CategorySubset,
                    "float" : RangeSubset,
                    "int" : RangeSubset}
        
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
    
    subset = ExperimentSubset(experiment = ex)
    subset.configure_traits()
    
