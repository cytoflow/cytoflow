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

import re

# for local debugging
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import Instance, HasTraits, List, CFloat, Str, Dict, Interface, \
                       Property, Bool, provides, on_trait_change, DelegatesTo
from traitsui.api import BasicEditorFactory, View, UI, \
                         CheckListEditor, Item, HGroup, ListEditor, InstanceEditor
from traitsui.qt4.editor import Editor

import pandas as pd
import numpy as np
                       
from cytoflow import Experiment
from cytoflow.utility import sanitize_identifier
from cytoflowgui.value_bounds_editor import ValuesBoundsEditor


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

@provides(ISubsetModel)
class CategorySubsetModel(HasTraits):
    name = Str
    experiment = Instance(Experiment)
    selected = List
    values = Property(trait = List,
                      depends_on = 'experiment')
    subset_str = Property(trait = Str,
                          depends_on = 'name, selected[]')
    
    def default_traits_view(self):
        return View(Item('selected',
                         label = self.name,
                         editor = CheckListEditor(values = self.values,
                                                  cols = 2),
                         style = 'custom'))
    
    # MAGIC: gets the value of the Property trait "values"
    def _get_values(self):
        if self.name:
            return list(self.experiment[self.name].cat.categories)
        else:
            return []

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

@provides(ISubsetModel)
class RangeSubsetModel(HasTraits):
    name = Str
    experiment = Instance(Experiment)
    values = Property(depends_on = 'experiment')
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
                                     high_name = 'high')))
    
    # MAGIC: gets the value of the Property trait "values"
    def _get_values(self):
        return list(np.sort(pd.unique(self.experiment[self.name])))
    
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
        return self.experiment[self.name].max()
    
    # MAGIC: the default value for self.low
    def _low_default(self):
        return self.experiment[self.name].min()

class SubsetModel(HasTraits):
    
    # the experiment we use to set up the editor
    experiment = Instance(Experiment)
    
    # the primary piece of the model; the traits view is a bunch of
    # InstanceEditors for this list.
    subset_list = List(ISubsetModel)
    
    # maps a condition name to an ISubsetModel instance
    subset_map = Dict(Str, Instance(ISubsetModel))
    
    # the actual string representation of this model: something you
    # can feed to pandas.DataFrame.subset()    
    subset_str = Property(trait = Str,
                          depends_on = "subset_list.subset_str")
    
    # if we're unpickling, say, and try to set the subset str before we 
    # have an experiment to set up the rest of the model, save it here.
    initial_subset_str = Str
      
    traits_view = View(Item('subset_list',
                            style = 'custom',
                            show_label = False,
                            editor = ListEditor(editor = InstanceEditor(),
                                                style = 'custom',
                                                mutable = False)))
    
    def __init__(self, *args, **kw_args):
        super(SubsetModel, self).__init__( *args, **kw_args )
        
    # MAGIC: gets the value of the Property trait "subset_string"
    def _get_subset_str(self):
        subset_strings = [s.subset_str for s in self.subset_list]
        subset_strings = filter(lambda x: x, subset_strings)
        return " and ".join(subset_strings)

    # MAGIC: when the Property trait "subset_string" is assigned to,
    # update the view    
    def _set_subset_str(self, value):
        # do we have a valid experiment yet?
        if not self.experiment:
            self.initial_subset_str = value
            return
        
        # reset everything
        for subset in self.subset_list:
            subset.subset_str = ""
            
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
            self.subset_map[name].subset_str = phrase
        
    def _on_experiment_change(self):
        print "experiment changed"
        cond_map = {"bool" : BoolSubsetModel,
                    "category" : CategorySubsetModel,
                    "float" : RangeSubsetModel,
                    "int" : RangeSubsetModel}
        
        subset_list = []
        subset_map = {}
        
        # it's possible that the op we're viewing is no longer valid,
        # in which case the experiment goes away.
        
        if not self.experiment:
            return
        
        for name, dtype in self.experiment.conditions.iteritems():
            subset = cond_map[dtype](name = name,
                                     experiment = self.experiment)
            subset_list.append(subset) 
            subset_map[name] = subset 
            
        self.subset_map = subset_map     
        self.subset_list = subset_list
        
        if self.initial_subset_str:
            self.subset_str = self.initial_subset_str
            self.initial_subset_str = ""

class _SubsetEditor(Editor):
    
    # the model object whose View this Editor displays
    model = Instance(SubsetModel, args = ())
    
    # the cytoflow.Experiment instance to use to construct the UI.  delegates
    # to the editor model.
    experiment = DelegatesTo('model')
    
    # the UI for the Experiment metadata
    _ui = Instance(UI)
    
    def init(self, parent):
        """
        Finishes initializing the editor and make the toolkit control
        """

        self.model = SubsetModel(initial_subset_str = self.value)
        
        # usually, we'd make this a static notifier on 
        # SubsetModel._on_experiment_change.  however, in this case we
        # have to set a dynamic notifier because this is occasionally changed
        # by the processing thread, and we need to re-dispatch to the ui thread
        self.model.on_trait_change(self.model._on_experiment_change, 
                             'experiment', 
                             dispatch = 'ui')
        
        self.sync_value(self.factory.experiment, 'experiment', 'from')        
        self._ui = self.model.edit_traits(kind = 'subpanel',
                                          parent = parent)
        self.control = self._ui.control
        
    def dispose(self):
        
        # disconnect the dynamic notifier.
        self.model.on_trait_change(self.model._on_experiment_change,
                                   'experiment',
                                   dispatch = 'ui',
                                   remove = True)
        
        if self._ui:
            self._ui.dispose()
            self._ui = None
            
    def update_editor(self):
        print "update editor with value: ''{0}''".format(self.value)
        self.model.subset_str = self.value
    
    @on_trait_change('model.subset_str')
    def update_value(self, new):
        if not self.experiment:
            return
        
        print "updating value from editor: ''{0}''".format(new)
        self.value = new            

class SubsetEditor(BasicEditorFactory):
    
    # the editor to be created
    klass = _SubsetEditor
    
    # the name of the trait containing the cytoflow.Experiment to build the UI
    
    # TODO - the required bits are going to have to come back from the remote
    # process.  yikes.
    experiment = Str
    
    
if __name__ == '__main__':
     
    import fcsparser
     
    ex = Experiment()
    ex.add_conditions({"Dox" : "bool"})
     
    tube1 = fcsparser.parse('../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                            reformat_meta = True,
                            channel_naming = "$PnN")
 
    tube2 = fcsparser.parse('../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                            reformat_meta = True,
                            channel_naming = "$PnN")
     
    ex.add_tube(tube1, {"Dox" : True})
    ex.add_tube(tube2, {"Dox" : False})
     
    class C(HasTraits):
        val = Str()
        experiment = Instance(Experiment)
 
    c = C(experiment = ex)
    c.val = "(Dox == True)"
     
    c.configure_traits(view=View(Item('val',
                                      editor = SubsetEditor(experiment = 'experiment'))))
     
     
     
     
