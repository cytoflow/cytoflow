'''
Created on Mar 23, 2015

@author: brian
'''

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traitsui.api import BasicEditorFactory, View, Group, UI, \
                         CheckListEditor, Item
from traitsui.qt4.editor import Editor
from traits.api import Instance, HasTraits, List, Float, Int
from cytoflow import Experiment
from value_bounds_editor import ValuesBoundsEditor
import pandas as pd
import numpy as np

class _SubsetEditor(Editor):
    
    # the cytoflow.Experiment to construct the UI
    experiment = Instance(Experiment)
    
    # the UI for the Experiment metadata
    _ui = Instance(UI)
    
    # the object we create to represent the Experiment conditions
    _obj = Instance(HasTraits)
    
    def init(self, parent):
        """
        Finishes initializing the editor; create the underlying toolkit widget
        """
        
        self.experiment = self.factory.experiment
        #self.sync_value(self.factory.experiment, 'experiment', 'from')
        
        self._obj, group = self._get_view()
        
        self._ui = self._obj.edit_traits(kind='subpanel', 
                                         parent=parent,
                                         view=View(group))

        self._obj.on_trait_change(self._view_changed)
        self.control = self._ui.control
        
    def dispose(self):
        self._obj.on_trait_change(self._view_changed, remove = True)
        super(_SubsetEditor, self).dispose()
        
    def update_editor(self):
        pass  #for the moment
        
    def _get_view(self):
        
        obj = HasTraits()
        group = Group()
        
        for name, dtype in self.experiment.conditions.iteritems():
            if dtype == 'bool':
                values = [name + '-', name + '+']
                obj.add_trait(name, List(editor = CheckListEditor(
                                                    values = values,
                                                    cols = 2)))
                group.content.append(Item(name, 
                                          style = 'custom'))
                
            elif dtype == 'category':
                values = list(self.experiment[name].cat.categories)
                obj.add_trait(name, List(editor = CheckListEditor(
                                                    values = values,
                                                    cols = len(values))))
                group.content.append(Item(name, 
                                          style = 'custom'))
                
            elif dtype == 'float':
                values = list(np.sort(pd.unique(self.experiment[name])))
                obj.add_trait(name + "Min", Float(self.experiment[name].min()))
                obj.add_trait(name + "Max", 
                              Float(default_value = self.experiment[name].max(),
                                    editor = ValuesBoundsEditor( 
                                                values = values,
                                                low_name = name + "Min",
                                                high_name = name + "Max"))
                            )
                group.content.append(Item(name + "Max", 
                                          label = name, 
                                          style = 'custom'))
                
            elif dtype == 'int':
                values = list(np.sort(pd.unique(self.experiment[name])))
                obj.add_trait(name + "Min", Int(self.experiment[name].min()))
                obj.add_trait(name + "Max", 
                              Int(default_value = self.experiment[name].max(),
                                  editor = ValuesBoundsEditor(
                                                values = values,
                                                low_name = name + "Min",
                                                high_name = name + "Max"))
                            )
                group.content.append(Item(name + "Max", 
                                          label = name, 
                                          style = 'custom'))
        
        return obj, group
    
    def _view_changed(self, name, new, old):
        print "view changed"
        # update self.value from self._obj

class SubsetEditor(BasicEditorFactory):
    
    # the editor to be created
    klass = _SubsetEditor
    
    # the cytoflow.Experiment instance to build the UI
    experiment = Instance(Experiment)
    
    