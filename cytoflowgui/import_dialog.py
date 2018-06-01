#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
Created on Feb 26, 2015

@author: brian
"""

# for local debugging
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"
    
from pathlib import Path
        
from traits.api import (HasTraits, HasStrictTraits, provides, Instance, Str, 
                        Int, List, Bool, Enum, Float, DelegatesTo, TraitType,
                        Property, BaseCStr, CStr, on_trait_change, Dict, Event,
                        cached_property, Any)
                       
from traitsui.api import (UI, Group, View, Item, TableEditor, OKCancelButtons,
                          Controller, CheckListEditor, TextEditor, BooleanEditor,
                          InstanceEditor, ListStrEditor, HGroup, ButtonEditor,
                          EnumEditor, TextEditor, BooleanEditor, ListEditor,
                          VGroup, Heading)

from traitsui.menu import OKButton

from traitsui.qt4.table_editor import TableEditor as TableEditorQt

from pyface.i_dialog import IDialog
from pyface.api import Dialog, FileDialog, error, warning, OK, confirm, YES, ImageResource

from pyface.qt import QtCore, QtGui
from pyface.constant import OK as PyfaceOK

from traitsui.table_column import ObjectColumn, TableColumn

from cytoflow import Tube as CytoflowTube
from cytoflow import Experiment, ImportOp
from cytoflow.operations.import_op import check_tube, parse_tube
import cytoflow.utility as util

from cytoflowgui.vertical_list_editor import VerticalListEditor

import fcsparser

def not_true ( value ):
    return (value is not True)

def not_false ( value ):
    return (value is not False)

class Tube(HasStrictTraits):
    """
    The model for a tube in an experiment.
    
    I originally wanted to make the Tube in the ImportDialog and the Tube in
    the ImportOp the same, but that fell apart when I tried to implement
    serialization (dynamic traits don't survive pickling when sending tubes to 
    the remote process)  (well, their values do, but neither the trait type nor 
    the metadata do.)
    
    Oh well.
        
    This model depends on duck-typing ("if it walks like a duck, and quacks
    like a duck...").  Because we want to use all of the TableEditor's nice
    features, each row needs to be an instance, and each column a Trait.
    So, each Tube instance represents a single tube, and each experimental
    condition (as well as the tube name, its file, and optional plate row and 
    col) are traits. These traits are dynamically added to Tube INSTANCES 
    (NOT THE TUBE CLASS.)  Then, we add appropriate columns to the table editor
    to access these traits.
    
    This is slightly complicated by the fact that there are two different
    kinds of traits we want to keep track of: traits that specify experimental
    conditions (inducer concentration, time point, etc.) and other things
    (file name, tube name, etc.).  We differentiate them because we enforce
    the invariant that each tube MUST have a unique combination of experimental
    conditions.  We do this with trait metadata: "condition == True" means 
    "is an experimental condition" (everything but file, source, tube, row, 
    column, parent).
    
    We also use the "transient" flag to specify traits that shouldn't be 
    displayed in the editor.  This matches well with the traits that
    every HasTraits-derived class has by default (all of which are transient.)
    """
    
    # these are the traits that every tube has.  every other trait is
    # dynamically created. 
    
    # the file name.
    file = Str(transient = True)
    
    # need a link to the model; needed for row coloring
    parent = Instance("ExperimentDialogModel", transient = True)
    
    # needed for fast hashing
    conditions = Dict
    
    # metadata from the FCS file
    metadata = Dict
    
    all_conditions_set = Property(Bool, depends_on = "conditions")
            
    def conditions_hash(self):
        ret = int(0)
    
        for key, value in self.conditions.items():
            if not ret:
                ret = hash((key, value))
            else:
                ret = ret ^ hash((key, value))
                
        return ret
    
    def _anytrait_changed(self, name, old, new):
        if self.parent is not None and name in self.parent.tube_traits_dict and self.parent.tube_traits_dict[name].condition:
            old_hash = self.conditions_hash()
            self.conditions[name] = new
            new_hash = self.conditions_hash()
            
            if old_hash in self.parent.counter:
                self.parent.counter[old_hash] -= 1
                
                if self.parent.counter[old_hash] == 0:
                    del self.parent.counter[old_hash]
                
            
                if new_hash not in self.parent.counter:
                    self.parent.counter[new_hash] = 1
                else:
                    self.parent.counter[new_hash] += 1
                
    @cached_property
    def _get_all_conditions_set(self):
        return len([x for x in list(self.conditions.values()) if x is None or x == ""]) == 0
    
    
class ExperimentColumn(ObjectColumn):
    # override ObjectColumn.get_cell_color
    def get_cell_color(self, obj):
        if obj.parent.is_tube_unique(obj) and obj.all_conditions_set:
            return super(ObjectColumn, self).get_cell_color(object)
        else:
            return QtGui.QColor('lightpink')
        

class ValidPythonIdentifier(BaseCStr):

    info_text = 'a valid python identifier'
     
    def validate(self, obj, name, value):
        value = super(ValidPythonIdentifier, self).validate(obj, name, value)
        if util.sanitize_identifier(value) == value:
            return value 
         
        self.error(obj, name, value)
    
class TubeTrait(HasStrictTraits):
    model = Instance('ExperimentDialogModel')

    trait = Property
    name = CStr
    type = Enum(['metadata', 'category', 'float', 'bool'])
    condition = Property(Bool, depends_on = 'type, _condition')
    
    _condition = Bool(False)
        
    remove_trait = Event
    editable = Property
    
    default_view = View(HGroup(Item('type',
                                    editor = EnumEditor(values = {'metadata' : "FCS Metadata",
                                                                  'category' : "Category",
                                                                  'float' : "Number",
                                                                  'bool' : "True/False"})),
                               Item('name',
                                    editor = TextEditor(auto_set = False),
                                    visible_when = 'type != "metadata"'),
                               Item('name',
                                    editor = EnumEditor(name = 'object.model.fcs_metadata'),
                                    visible_when = 'type == "metadata"'),
                               Item('condition',
                                    enabled_when = 'type == "metadata"')))


    # magic - get the value for the "condition" property
    def _get_condition(self):
        if self.type == 'metadata':
            return self._condition
        else:
            return True
    
        
    # magic - set the value for the "condition" property
    def _set_condition(self, value):
        self._condition = value
    
    
    # magic - gets values for the `trait` property
    def _get_trait(self):
        if self.type == 'metadata' or self.type == 'category':
            return Str()
        elif self.type == 'float':
            return Float()
        elif self.type == 'bool':
            return Bool()
    
    
    # magic - get the value of the "editable" property
    def _get_editable(self):
        return self.type != 'metadata'
     
     
    @on_trait_change('remove_trait')
    def _remove_trait(self):
        self.model.tube_traits.remove(self)
    
class ExperimentDialogModel(HasStrictTraits):
    """
    The model for the Experiment setup dialog.
    """
    
    # these bits are needed to defer model init until after
    # the handler has been initialized
    init_op = Any
    init_conditions = Any
    init_metadata = Any
        
    # the list of Tubes (rows in the table)
    tubes = List(Tube)

    # a list of the traits that have been added to Tube instances
    # (columns in the table)
    tube_traits = List(TubeTrait)
    tube_traits_dict = Dict
    
    # keeps track of whether a tube is unique or not
    counter = Dict(Int, Int)
    
    # are all the tubes unique and filled?
    valid = Property(List)
    
    # a dummy Experiment, with the first Tube and no events, so we can check
    # subsequent tubes for voltage etc. and fail early.
    dummy_experiment = Instance(Experiment)
    
    # traits to communicate with the traits_view
    fcs_metadata = Property(List, depends_on = 'tubes')
    
    def init_model(self, op, conditions, metadata):      
        if 'CF_File' not in conditions:
            self.tube_traits.append(TubeTrait(model = self,
                                              name = 'CF_File',
                                              type = 'metadata',
                                              condition = False))
            
        for name, condition in conditions.items():
            if str(condition.dtype).startswith("category") or str(condition.dtype).startswith('object'):
                self.tube_traits.append(TubeTrait(model = self, name = name, type = 'category'))
            elif str(condition.dtype).startswith("int") or str(condition.dtype).startswith("float"):
                self.tube_traits.append(TubeTrait(model = self, name = name, type = 'float'))
            elif str(condition.dtype) == "bool":
                self.tube_traits.append(TubeTrait(model = self, name = name, type = 'bool'))

        self.dummy_experiment = None
        
        shown_error = False
        
        for op_tube in op.tubes:
            tube = Tube(file = op_tube.file,
                        parent = self,
                        metadata = metadata['fcs_metadata'][op_tube.file])
            
            try:
                fcsparser.parse(op_tube.file, meta_data_only = True)
            except Exception:
                if not shown_error:
                    warning(None,
                            "Had trouble loading some of the experiment's FCS "
                            "files.  You will need to re-add them.")
                    shown_error = True
                continue
            
            # if we're the first tube loaded, create a dummy experiment
            # and setup default metadata columns
            if not self.dummy_experiment:
                self.dummy_experiment = ImportOp(tubes = [op_tube],
                                                 conditions = op.conditions,
                                                 events = 1).apply()
                                                 
            self.tubes.append(tube)  # adds the dynamic traits to the tube
            
            tube.trait_set(**op_tube.conditions)
            
            for trait in self.tube_traits:
                if trait.type == 'metadata':
                    tube.trait_set(**{trait.name : tube.metadata[trait.name]})
                    
                if trait.condition:
                    tube.conditions[trait.name] = tube.trait_get()[trait.name]
    
    
    @on_trait_change('tubes_items')
    def _tubes_items(self, event):
        for tube in event.added:
            for trait in self.tube_traits:
                tube.add_trait(trait.name, trait.trait)
                
                if trait.name in tube.metadata:
                    tube.trait_set(**{trait.name : tube.metadata[trait.name]})
                else:
                    tube.trait_set(**{trait.name : trait.trait.default_value})

                if trait.condition:
                    tube.conditions[trait.name] = tube.trait_get()[trait.name]
            
            tube_hash = tube.conditions_hash()
            if tube_hash in self.counter:
                self.counter[tube_hash] += 1
            else:
                self.counter[tube_hash] = 1
                
        for tube in event.removed:
            tube_hash = tube.conditions_hash()
            if self.counter[tube_hash] == 1:
                del self.counter[tube_hash]
            else:
                self.counter[tube_hash] -= 1
                 
    @on_trait_change('tube_traits_items')
    def _tube_traits_changed(self, event):
        for trait in event.added:
            if not trait.name:
                continue
                
            for tube in self.tubes:
                tube.add_trait(trait.name, trait.trait)
                
                if trait.type == 'metadata':
                    tube.trait_set(**{trait.name : tube.metadata[trait.name]})
                else:
                    tube.trait_set(**{trait.name : trait.trait.default_value})

                if trait.condition:
                    tube.conditions[trait.name] = tube.trait_get()[trait.name]
    
            self.tube_traits_dict[trait.name] = trait
             
        for trait in event.removed:
            if not trait.name:
                continue
            
            for tube in self.tubes:
                tube.remove_trait(trait.name)

                if trait.condition:
                    del tube.conditions[trait.name]

            del self.tube_traits_dict[trait.name]
            
        self.counter.clear()
        for tube in self.tubes:
            tube_hash = tube.conditions_hash()
            if tube_hash in self.counter:
                self.counter[tube_hash] += 1
            else:
                self.counter[tube_hash] = 1
            
    @on_trait_change('tube_traits:name')
    def _on_trait_name_change(self, trait, _, old_name, new_name):
        if not new_name:
            trait.name = old_name
            return
        
        for tube in self.tubes:
            trait_value = None
            
            if old_name:
                # store the value
                trait_value = tube.trait_get()[old_name]
                
                if trait.condition:                        
                    del tube.conditions[old_name]
                
                # remove the old trait from the 
                tube.remove_trait(old_name)
                
            if new_name in tube.metadata:
                trait_value = tube.metadata[new_name]
            elif trait_value is None:
                trait_value = trait.trait.default_value
            
            tube.add_trait(new_name, trait.trait)
            tube.trait_set(**{new_name : trait_value})
            
            if trait.condition:
                tube.conditions[new_name] = trait_value
                
        del self.tube_traits_dict[old_name]
        self.tube_traits_dict[new_name] = trait

        self.counter.clear()
        for tube in self.tubes:
            tube_hash = tube.conditions_hash()
            if tube_hash in self.counter:
                self.counter[tube_hash] += 1
            else:
                self.counter[tube_hash] = 1
                
                
    @on_trait_change('tube_traits:condition')
    def _on_condition_change(self, trait, name, new):
        for tube in self.tubes:
            if trait.condition:
                tube.conditions[trait.name] = tube.trait_get()[trait.name]
            else:
                del tube.conditions[trait.name]
                
        self.counter.clear()
        for tube in self.tubes:
            tube_hash = tube.conditions_hash()
            if tube_hash in self.counter:
                self.counter[tube_hash] += 1
            else:
                self.counter[tube_hash] = 1       
        
                            
    
    def update_import_op(self, op):
        conditions = {}
        for trait in self.tube_traits:
            if not trait.condition:
                continue
            
            conditions[trait.name] = trait.type
            if conditions[trait.name] == 'metadata':
                conditions[trait.name] = 'category'
            
        tubes = []
        for tube in self.tubes:
            op_tube = CytoflowTube(file = tube.file,
                                   conditions = tube.trait_get(conditions.keys()))
            tubes.append(op_tube)
            
        op.conditions = conditions
        op.tubes = tubes         
           
#         trait_to_dtype = {"Str" : "category",
#                           "Float" : "float",
#                           "Bool" : "bool",
#                           "Int" : "int"}
#         
#         conditions = {}
#         for trait_name, trait in self.tube_traits:
#             if not trait.condition:
#                 continue
# 
#             trait_type = trait.__class__.__name__
#             conditions[trait_name] = trait_to_dtype[trait_type]
#             
#         tubes = []
#         for tube in self.tubes:
#             op_tube = CytoflowTube(file = tube.file,
#                                    conditions = tube.trait_get(condition = True))
#             tubes.append(op_tube)
#             
#         op.conditions = conditions
#         op.tubes = tubes
            
    def is_tube_unique(self, tube):
        tube_hash = tube.conditions_hash()
        if tube_hash in self.counter:
            return self.counter[tube.conditions_hash()] == 1
        else:
            return False
    
    
    def _get_valid(self):
        return len(set(self.counter)) == len(self.tubes) and all([x.all_conditions_set for x in self.tubes])
    
    
    # magic: gets the list of FCS metadata for the trait list editor
    @cached_property
    def _get_fcs_metadata(self):
        meta = {}
        for tube in self.tubes:
            for name, val in tube.metadata.items():
                if name not in meta:
                    meta[name] = set()
                    
                meta[name].add(val)
                
        return [x for x in meta.keys() if len(meta[x]) > 1]
                    
class ExperimentDialogHandler(Controller):

    add_tubes = Event
    remove_tubes = Event
    add_variable = Event
    import_csv = Event
    
    # traits to communicate with the TabularEditor
    selected_tubes = List
    
    default_view = View(
            HGroup(
                VGroup(
                    Heading("First, define experimental variables"),
                    Item('tube_traits',
                         editor = VerticalListEditor(editor = InstanceEditor(),
                                                     style = 'custom',
                                                     mutable = False,
                                                     deletable = True),
                         show_label = False),
                    HGroup(
                        Item('handler.add_variable',
                             editor = ButtonEditor(label = "Add a variable"),
                             show_label = False))),
                VGroup(
                    Heading("Then, map experimental variables to FCS files"),
                    Item(name = 'tubes', 
                         id = 'table', 
                         editor = TableEditor(editable = True,
                                              sortable = True,
                                              auto_size = True,
                                              configurable = False,
                                              selection_mode = 'rows',
                                              selected = 'handler.selected_tubes'),
                         enabled_when = "object.tubes",
                         show_label = False),
                    HGroup(
                        Item('handler.add_tubes',
                             editor = ButtonEditor(label = "Add tubes..."),
                             show_label = False),
                        Item('handler.remove_tubes',
                             editor = ButtonEditor(label = "Remove tubes"),
                             show_label = False,
                             enabled_when = 'object.tubes'),
                        Item('handler.import_csv',
                             editor = ButtonEditor(label = "Import from CSV..."),
                             show_label = False)))),
            title     = 'Experiment Setup',
            buttons = [OKButton],
            resizable = True
        )

    # keep a ref to the table editor so we can add columns dynamically
    table_editor = Instance(TableEditorQt)

    # keep a refs to enable/disable.
    btn_remove_tubes = Instance(QtGui.QPushButton)
    btn_metadata = Instance(QtGui.QPushButton)
    
    updating = Bool(False)
    
    def init(self, info):
                       
        # save a reference to the table editor
        self.table_editor = info.ui.get_editors('tubes')[0]

        # init the model.  we have to defer this so we don't end up with
        # a bunch of "default" columns
        self.model.init_model(self.model.init_op, 
                              self.model.init_conditions,
                              self.model.init_metadata)
                
        return True
    
    def closed(self, info, is_ok):
        for trait in self.model.tube_traits:
            if not trait.editable:
                continue
            for tube in self.model.tubes:
                tube.on_trait_change(self._try_multiedit, 
                                     trait.name, 
                                     remove = True)
        
            
    @on_trait_change('add_variable')
    def _on_add_variable(self):
        self.model.tube_traits.append(TubeTrait(model = self.model))
        
            
    def _on_import(self):
        """
        Import format: CSV, first column is filename, path relative to CSV.
        others are conditions, type is autodetected.  first row is header
        with names.
        """
        pass

        
    @on_trait_change('add_tubes')
    def _on_add_tubes(self):
        """
        Handle "Add tubes..." button.  Add tubes to the experiment.
        """
        
        file_dialog = FileDialog()
        file_dialog.wildcard = "Flow cytometry files (*.fcs)|*.fcs|"
        file_dialog.action = 'open files'
        file_dialog.open()
        
        if file_dialog.return_code != PyfaceOK:
            return
        
        for path in file_dialog.paths:
            try:
                fcsparser.parse(path, 
                                meta_data_only = True)
            except Exception as e:
                raise RuntimeError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(path, e.value))
                
            # if we're the first tube loaded, create a dummy experiment
            # and setup default metadata columns
            if not self.model.dummy_experiment:
                self.model.dummy_experiment = ImportOp(tubes = [CytoflowTube(file = path)],
                                                       events = 1).apply()
                                                       
            # check the next tube against the dummy experiment
            try:
                check_tube(path, self.model.dummy_experiment)
            except util.CytoflowError as e:
                error(None, e.__str__(), "Error importing tube")
                return
            
            metadata, _ = parse_tube(path, self.model.dummy_experiment, metadata_only = True)
                
            tube = Tube(file = path, parent = self.model, metadata = metadata)
            
            self.model.tubes.append(tube)
            
            
    @on_trait_change('remove_tubes')
    def _on_remove_tubes(self):
        conf = confirm(None,
                       "Are you sure you want to remove the selected tube(s)?",
                       "Remove tubes?")
        if conf == YES:
            for tube in self.selected_tubes:
                self.model.tubes.remove(tube)
                
        if not self.model.tubes:
            self.model.dummy_experiment = None

                
    @on_trait_change('model:tube_traits_items', post_init = True)
    def _tube_traits_changed(self, event):
        for trait in event.added:
            if not trait.name:
                continue
                        
            if self.table_editor:
                self.table_editor.columns.append(ExperimentColumn(name = trait.name,
                                                                  editable = trait.editable))                 
            for tube in self.model.tubes:   
                if trait.editable:
                        tube.on_trait_change(self._try_multiedit, trait.name)

        
        for trait in event.removed:

            table_column = next((x for x in self.table_editor.columns if x.name == trait.name))
            self.table_editor.columns.remove(table_column)
            
            for tube in self.model.tubes:
                if trait.editable:
                    tube.on_trait_change(self._try_multiedit, trait.name, remove = True)
                    
                    
    @on_trait_change('model:tube_traits:name')
    def _tube_trait_name_changed(self, trait, _, old_name, new_name):
        old_table_column = next((x for x in self.table_editor.columns if x.name == old_name))
        column_idx = self.table_editor.columns.index(old_table_column)
        self.table_editor.columns.remove(old_table_column)
        
        for tube in self.model.tubes:
            if trait.editable:
                tube.on_trait_change(self._try_multiedit, old_name, remove = True)
                
        self.table_editor.columns.insert(column_idx,
                                         ExperimentColumn(name = new_name,
                                                          editable = trait.editable))                 
        for tube in self.model.tubes:   
            if trait.editable:
                    tube.on_trait_change(self._try_multiedit, new_name)

            
    def _try_multiedit(self, obj, name, old, new):
        """
        See if there are multiple elements selected when a tube's trait changes
        
        and if so, edit the same trait for all the selected tubes.
        """
        
        if self.updating:
            return
        
        self.updating = True

        for tube, trait_name in self.selected_tubes:
            if tube != obj:
                old_hash = tube.conditions_hash()
                self.model.counter[old_hash] -= 1
                if self.model.counter[old_hash] == 0:
                    del self.model.counter[old_hash]            
    
                # update the underlying traits without notifying the editor
                # we do this all here for performance reasons
                tube.trait_setq(**{trait_name: new})
                tube.conditions[trait_name] = new
                
                new_hash = tube._conditions_hash()
                if new_hash not in self.model.counter:
                    self.model.counter[new_hash] = 1
                else:
                    self.model.counter[new_hash] += 1
                

        # now refresh the editor all at once
        self.table_editor.refresh_editor()
        self.updating = False
        

    